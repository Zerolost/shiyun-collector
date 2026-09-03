import argparse
import asyncio
import hashlib
import importlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import httpx

from models import NormalizedItem, SourceResult

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sources" / "registry.json"
OUT = ROOT / ".data"
Parser = Callable[[bytes, dict[str, Any]], list[NormalizedItem]]


def load_parser(adapter: str) -> Parser:
  module = importlib.import_module(f"adapters.{adapter}")
  return module.parse


async def fetch_source(client: httpx.AsyncClient, source: dict[str, Any]) -> SourceResult:
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
  seen: set[str] = set()
  output: list[NormalizedItem] = []
  for item in items:
    fingerprint: str = hashlib.sha256(f"{item.get('subject')}|{item.get('module')}|{item.get('title')}|{item.get('text')}".encode()).hexdigest()
    if fingerprint in seen:
      continue
    seen.add(fingerprint)
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
  normalized: list[NormalizedItem] = deduplicate(all_items)
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
