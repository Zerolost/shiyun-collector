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
    if source["module"] == "famous_quote":
      module: str = "famous_quote"
      tags: list[str] = list(dict.fromkeys(source.get("tags", []) + ["主题待审核"]))
    elif source["module"] == "essay_material":
      module = "essay_material"
      tags = list(dict.fromkeys(source.get("tags", []) + ["议论文素材", "主题待审核"]))
    else:
      module = source["module"]
      tags = list(source.get("tags", []))
    stable: str = str(row.get("pageid") or row.get("revid") or hashlib.sha256(title.encode()).hexdigest()[:16])
    items.append({
      "id": f"{source['id']}:{stable}",
      "subject": source["subject"],
      "module": module,
      "title": title,
      "text": text,
      "sourceId": source["id"],
      "sourceUrl": source["homepage"],
      "license": source["license"],
      "tags": tags,
      "metadata": {"pageId": row.get("pageid"), "revisionId": row.get("revid")}
    })
  return items
