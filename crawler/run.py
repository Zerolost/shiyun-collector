import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "sources" / "registry.json"
OUT = ROOT / ".data"


async def fetch_source(client: httpx.AsyncClient, source: dict[str, Any]) -> dict[str, Any]:
  response: httpx.Response = await client.get(source["url"], follow_redirects=True, timeout=30)
  response.raise_for_status()
  body: bytes = response.content
  return {
    "id": source["id"],
    "subject": source["subject"],
    "kind": source["kind"],
    "sourceUrl": str(response.url),
    "license": source["license"],
    "retrievedAt": datetime.now(UTC).isoformat(),
    "sha256": hashlib.sha256(body).hexdigest(),
    "contentType": response.headers.get("content-type", ""),
    "payload": response.text
  }


async def main() -> None:
  sources: list[dict[str, Any]] = json.loads(REGISTRY.read_text("utf-8"))
  OUT.mkdir(parents=True, exist_ok=True)
  headers: dict[str, str] = {
    "User-Agent": "ShiyunCollector/1.0 (https://github.com/Zerolost/shiyun-collector; contact via GitHub)",
    "Api-User-Agent": "ShiyunCollector/1.0 (https://github.com/Zerolost/shiyun-collector; contact via GitHub)"
  }
  limits = httpx.Limits(max_connections=8, max_keepalive_connections=4)
  async with httpx.AsyncClient(headers=headers, limits=limits) as client:
    results = await asyncio.gather(*(fetch_source(client, source) for source in sources), return_exceptions=True)
  collected: list[dict[str, Any]] = []
  errors: list[dict[str, str]] = []
  for source, result in zip(sources, results):
    if isinstance(result, Exception):
      errors.append({"id": source["id"], "error": str(result)})
    else:
      collected.append(result)
  (OUT / "collected.json").write_text(json.dumps(collected, ensure_ascii=False, indent=2), "utf-8")
  (OUT / "report.json").write_text(json.dumps({"collected": len(collected), "errors": errors}, ensure_ascii=False, indent=2), "utf-8")
  if not collected:
    raise SystemExit(1)


if __name__ == "__main__":
  asyncio.run(main())
