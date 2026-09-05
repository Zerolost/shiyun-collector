import re
from typing import Any

from models import NormalizedItem


def enrich_vocabulary_examples(items: list[NormalizedItem], limit: int = 3) -> list[NormalizedItem]:
  sentences: list[NormalizedItem] = [item for item in items if item.get("subject") == "english" and item.get("module") in {"bilingual_sentence", "sentence_corpus"}]
  vocabulary: list[NormalizedItem] = [item for item in items if item.get("subject") == "english" and item.get("module") == "vocabulary"]
  for item in vocabulary:
    word: str = str(item.get("title", "")).casefold()
    if not word or len(word) < 3:
      continue
    pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    matches: list[dict[str, str]] = []
    for sentence in sentences:
      text: str = str(sentence.get("text", ""))
      if not pattern.search(text):
        continue
      match: dict[str, str] = {"english": text}
      if sentence.get("translation"):
        match["chinese"] = str(sentence["translation"])
      matches.append(match)
      if len(matches) >= limit:
        break
    if matches:
      metadata: dict[str, Any] = dict(item.get("metadata", {}))
      metadata["exampleSentences"] = matches
      item["metadata"] = metadata
  return items


def enrich_items(items: list[NormalizedItem]) -> list[NormalizedItem]:
  return enrich_vocabulary_examples(items)
