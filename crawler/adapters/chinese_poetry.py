import hashlib
import json
from typing import Any

from models import NormalizedItem


def parse(payload: bytes, source: dict[str, Any]) -> list[NormalizedItem]:
  rows: list[dict[str, Any]] = json.loads(payload)
  items: list[NormalizedItem] = []
  limit: int = int(source.get("limit", len(rows)))
  for row in rows[:limit]:
    title: str = str(row.get("title", "")).strip()
    author: str = str(row.get("author", "")).strip()
    paragraphs: list[str] = [str(value).strip() for value in row.get("paragraphs", []) if str(value).strip()]
    if not title or not paragraphs:
      continue
    stable: str = str(row.get("id") or hashlib.sha256(f"{author}:{title}:{paragraphs[0]}".encode()).hexdigest()[:20])
    tags: list[str] = [str(tag) for tag in row.get("tags", [])]
    items.append({
      "id": f"{source['id']}:{stable}",
      "subject": "chinese",
      "module": "classical_text",
      "title": title,
      "text": "\n".join(paragraphs),
      "author": author,
      "sourceId": source["id"],
      "sourceUrl": source["homepage"],
      "license": source["license"],
      "tags": list(dict.fromkeys(source.get("tags", []) + tags)),
      "metadata": {"collection": source.get("collection", "")}
    })
  return items
