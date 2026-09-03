import bz2
from typing import Any

from models import NormalizedItem


def parse(payload: bytes, source: dict[str, Any]) -> list[NormalizedItem]:
  text: str = bz2.decompress(payload).decode("utf-8", errors="replace")
  items: list[NormalizedItem] = []
  limit: int = int(source.get("limit", 5000))
  min_length: int = int(source.get("minLength", 24))
  max_length: int = int(source.get("maxLength", 220))
  for line in text.splitlines():
    parts: list[str] = line.split("\t", 2)
    if len(parts) != 3:
      continue
    sentence_id, language, sentence = parts
    sentence = sentence.strip()
    if language != source["language"] or not min_length <= len(sentence) <= max_length:
      continue
    items.append({
      "id": f"{source['id']}:{sentence_id}",
      "subject": source["subject"],
      "module": "sentence_corpus",
      "title": sentence[:60],
      "text": sentence,
      "sourceId": source["id"],
      "sourceUrl": source["homepage"],
      "license": source["license"],
      "tags": source.get("tags", []),
      "metadata": {"language": language, "sentenceId": sentence_id}
    })
    if len(items) >= limit:
      break
  return items
