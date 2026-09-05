import hashlib
import json
from typing import Any

from models import NormalizedItem


def parse(payload: bytes, source: dict[str, Any]) -> list[NormalizedItem]:
  rows: list[dict[str, Any]] = json.loads(payload)
  items: list[NormalizedItem] = []
  limit: int = int(source.get("limit", len(rows)))
  for index, row in enumerate(rows[:limit]):
    title: str = str(row.get("title") or row.get("rhythmic") or row.get("chapter") or f"{source.get('collection', '古典文本')}·{index + 1}").strip()
    author: str = str(row.get("author", "")).strip()
    content: list[Any] = row.get("paragraphs") or row.get("content") or []
    paragraphs: list[str] = [str(value).strip() for value in content if str(value).strip()]
    if not paragraphs:
      continue
    stable: str = str(row.get("id") or hashlib.sha256(f"{author}:{title}:{paragraphs[0]}".encode()).hexdigest()[:20])
    tags: list[str] = [str(tag) for tag in row.get("tags", [])]
    for key in ("chapter", "section"):
      if row.get(key):
        tags.append(str(row[key]))
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
      "metadata": {"collection": source.get("collection", ""), "chapter": row.get("chapter", ""), "section": row.get("section", "")}
    })
  return items
