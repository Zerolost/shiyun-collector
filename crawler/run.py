import argparse
import asyncio
import hashlib
import importlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import httpx

from derive import derive_chinese
from models import NormalizedItem, SourceResult
from normalize import normalize_item

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sources" / "registry.json"
OUT = ROOT / ".data"
Parser = Callable[[bytes, dict[str, Any]], list[NormalizedItem]]


def load_parser(adapter: str) -> Parser:
  module = importlib.import_module(f"adapters.{adapter}")
  return module.parse


async def fetch_one(client: httpx.AsyncClient, url: str, timeout: int) -> bytes:
  response: httpx.Response | None = None
  last_error: Exception | None = None
  for attempt in range(3):
    try:
      response = await client.get(url, follow_redirects=True, timeout=timeout)
      response.raise_for_status()
      return response.content
    except (httpx.HTTPError, httpx.TimeoutException) as error:
      last_error = error
      if attempt < 2:
        await asyncio.sleep(2 ** attempt)
  raise RuntimeError(repr(last_error))


async def fetch_source(client: httpx.AsyncClient, source: dict[str, Any]) -> SourceResult:
  if source["adapter"] == "local_teaching":
    payload: bytes = (ROOT / source["path"]).read_bytes()
    parser: Parser = load_parser(source["adapter"])
    return {
      "source": source,
      "items": parser(payload, source),
      "rawSha256": hashlib.sha256(payload).hexdigest(),
      "retrievedAt": datetime.now(UTC).isoformat()
    }
  if source["adapter"] == "tatoeba_pairs":
    urls: list[str] = source["urls"]
    payloads: list[bytes] = await asyncio.gather(*(fetch_one(client, url, int(source.get("timeout", 180))) for url in urls))
    parser: Parser = load_parser(source["adapter"])
    return {
      "source": source,
      "items": parser(payloads, source),
      "rawSha256": hashlib.sha256(b"".join(payloads)).hexdigest(),
      "retrievedAt": datetime.now(UTC).isoformat()
    }
  response: httpx.Response | None = None
  last_error: Exception | None = None
  for attempt in range(3):
    try:
      response = await client.get(source["url"], follow_redirects=True, timeout=source.get("timeout", 60))
      response.raise_for_status()
      break
    except (httpx.HTTPError, httpx.TimeoutException) as error:
      last_error = error
      if attempt < 2:
        await asyncio.sleep(2 ** attempt)
  if response is None:
    raise RuntimeError(repr(last_error))
  payload: bytes = response.content
  parser: Parser = load_parser(source["adapter"])
  return {
    "source": source,
    "items": parser(payload, source),
    "rawSha256": hashlib.sha256(payload).hexdigest(),
    "retrievedAt": datetime.now(UTC).isoformat()
  }


def deduplicate(items: list[NormalizedItem]) -> list[NormalizedItem]:
  seen_ids: set[str] = set()
  seen_content: set[str] = set()
  output: list[NormalizedItem] = []
  for item in items:
    item_id: str = str(item.get("id", ""))
    fingerprint: str = hashlib.sha256(f"{item.get('subject')}|{item.get('module')}|{item.get('title')}|{item.get('text')}".encode()).hexdigest()
    if item_id in seen_ids or fingerprint in seen_content:
      continue
    seen_ids.add(item_id)
    seen_content.add(fingerprint)
    output.append(item)
  return output


def enrich_english(items: list[NormalizedItem]) -> list[NormalizedItem]:
  translations: dict[str, dict[str, Any]] = {}
  for item in items:
    if item.get("subject") != "english" or item.get("sourceId") != "ecdict-open-english-chinese":
      continue
    metadata: dict[str, Any] = item.get("metadata", {})
    translations[str(item.get("title", "")).casefold()] = {
      "chineseMeaning": metadata.get("chineseMeaning", item.get("text", "")),
      "phonetic": metadata.get("phonetic", ""),
      "partOfSpeech": metadata.get("partOfSpeech", "")
    }
  output: list[NormalizedItem] = []
  for item in items:
    if item.get("subject") != "english":
      output.append(item)
      continue
    match: dict[str, Any] | None = translations.get(str(item.get("title", "")).casefold())
    if match is None:
      output.append(item)
      continue
    metadata: dict[str, Any] = dict(item.get("metadata", {}))
    metadata["chineseMeaning"] = match["chineseMeaning"]
    metadata["translationSource"] = "ECDICT"
    if not metadata.get("phonetic") and match["phonetic"]:
      metadata["phonetic"] = match["phonetic"]
    if not metadata.get("partOfSpeech") and match["partOfSpeech"]:
      metadata["partOfSpeech"] = match["partOfSpeech"]
    item["metadata"] = metadata
    output.append(item)
  return output


async def main() -> None:
  cli = argparse.ArgumentParser()
  cli.add_argument("--profile", choices=["frequent", "daily", "weekly", "all"], default="frequent")
  args = cli.parse_args()
  registry: list[dict[str, Any]] = json.loads(REGISTRY.read_text("utf-8"))
  sources: list[dict[str, Any]] = [source for source in registry if args.profile == "all" or source["frequency"] == args.profile]
  OUT.mkdir(parents=True, exist_ok=True)
  headers: dict[str, str] = {
    "User-Agent": "ShiyunCollector/2.0 (https://github.com/Zerolost/shiyun-collector; contact via GitHub)",
    "Api-User-Agent": "ShiyunCollector/2.0 (https://github.com/Zerolost/shiyun-collector; contact via GitHub)"
  }
  limits = httpx.Limits(max_connections=6, max_keepalive_connections=4)
  async with httpx.AsyncClient(headers=headers, limits=limits) as client:
    results = await asyncio.gather(*(fetch_source(client, source) for source in sources), return_exceptions=True)
  collected: list[SourceResult] = []
  errors: list[dict[str, str]] = []
  all_items: list[NormalizedItem] = []
  for source, result in zip(sources, results):
    if isinstance(result, Exception):
      errors.append({"id": source["id"], "error": str(result)})
      continue
    collected.append(result)
    all_items.extend(result["items"])
  normalized: list[NormalizedItem] = derive_chinese(enrich_english([normalize_item(item) for item in deduplicate(all_items)]))
  (OUT / "normalized.json").write_text(json.dumps(normalized, ensure_ascii=False, indent=2), "utf-8")
  report: dict[str, Any] = {
    "profile": args.profile,
    "sources": len(sources),
    "collected": len(collected),
    "items": len(normalized),
    "errors": errors,
    "sourceResults": [{"id": result["source"]["id"], "items": len(result["items"]), "sha256": result["rawSha256"], "retrievedAt": result["retrievedAt"]} for result in collected]
  }
  (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
  if sources and not collected:
    raise SystemExit(1)


if __name__ == "__main__":
  asyncio.run(main())
