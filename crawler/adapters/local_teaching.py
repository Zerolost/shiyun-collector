import json
from typing import Any

from models import NormalizedItem


def parse(payload: bytes, source: dict[str, Any]) -> list[NormalizedItem]:
  rows: list[dict[str, Any]] = json.loads(payload)
  items: list[NormalizedItem] = []
  for row in rows:
    item: NormalizedItem = {
      "id": row["id"],
      "subject": row["subject"],
      "module": row["module"],
      "title": row["title"],
      "text": row["text"],
      "translation": row.get("translation", ""),
      "sourceId": source["id"],
      "sourceUrl": source["homepage"],
      "license": source["license"],
      "tags": row.get("tags", []),
      "metadata": row.get("metadata", {})
    }
    items.append(item)
  return items
