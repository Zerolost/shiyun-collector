import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import httpx

CACHE_PATH = Path(os.getenv("TRANSLATION_CACHE", ".data/translation_cache.json"))


def load_cache() -> dict[str, str]:
  if not CACHE_PATH.exists():
    return {}
  try:
    value: Any = json.loads(CACHE_PATH.read_text("utf-8"))
    return value if isinstance(value, dict) else {}
  except (OSError, json.JSONDecodeError):
    return {}


def cache_key(text: str, source: str, target: str) -> str:
  return hashlib.sha256(f"{source}|{target}|{text}".encode()).hexdigest()


async def mymemory(client: httpx.AsyncClient, text: str, source: str, target: str) -> str:
  response: httpx.Response = await client.get("https://api.mymemory.translated.net/get", params={"q": text, "langpair": f"{source}|{target}"}, timeout=20)
  response.raise_for_status()
  data: dict[str, Any] = response.json()
  translated: str = str(data.get("responseData", {}).get("translatedText", "")).strip()
  if not translated or translated.casefold() == text.casefold():
    raise RuntimeError("MyMemory returned no useful translation")
  return translated


async def libretranslate(client: httpx.AsyncClient, text: str, source: str, target: str) -> str:
  response: httpx.Response = await client.post("https://libretranslate.com/translate", json={"q": text, "source": source, "target": target, "format": "text"}, timeout=30)
  response.raise_for_status()
  translated: str = str(response.json().get("translatedText", "")).strip()
  if not translated:
    raise RuntimeError("LibreTranslate returned no translation")
  return translated


async def translate_text(text: str, source: str = "en", target: str = "zh-CN") -> tuple[str, str]:
  cache: dict[str, str] = load_cache()
  key: str = cache_key(text, source, target)
  if key in cache:
    return cache[key], "cache"
  providers = (mymemory, libretranslate)
  async with httpx.AsyncClient(headers={"User-Agent": "ShiyunCollector/3.0"}) as client:
    for provider in providers:
      try:
        translated: str = await provider(client, text, source, target)
        cache[key] = translated
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), "utf-8")
        return translated, provider.__name__
      except (httpx.HTTPError, RuntimeError):
        await asyncio.sleep(1)
  return "", "unavailable"
