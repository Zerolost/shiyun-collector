import hashlib
import json
from typing import Any

from models import NormalizedItem


def parse(payload: bytes, source: dict[str, Any]) -> list[NormalizedItem]:
  data: dict[str, Any] = json.loads(payload)
  query: dict[str, Any] = data.get("query", {})
  pages: list[dict[str, Any]] = list(query.get("pages", {}).values())
  changes: list[dict[str, Any]] = query.get("recentchanges", [])
  rows: list[dict[str, Any]] = pages or changes
  items: list[NormalizedItem] = []
  for row in rows:
    title: str = str(row.get("title", "")).strip()
    text: str = str(row.get("extract", "")).strip()
    if not title:
      continue
    stable: str = str(row.get("pageid") or row.get("revid") or hashlib.sha256(title.encode()).hexdigest()[:16])
    items.append({
      "id": f"{source['id']}:{stable}",
      "subject": source["subject"],
      "module": source["module"],
      "title": title,
      "text": text,
      "sourceId": source["id"],
      "sourceUrl": source["homepage"],
      "license": source["license"],
      "tags": source.get("tags", []),
      "metadata": {"pageId": row.get("pageid"), "revisionId": row.get("revid")}
    })
  return items
