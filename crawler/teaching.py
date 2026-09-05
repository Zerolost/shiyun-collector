import hashlib
import re
from typing import Any

from models import NormalizedItem

CLAUSE_MARKERS: dict[str, str] = {
  "although": "让步状语从句",
  "because": "原因状语从句",
  "which": "定语从句",
  "that": "从句连接词",
  "when": "时间状语从句",
  "while": "时间或让步关系",
  "if": "条件状语从句",
  "unless": "条件状语从句"
}


def stable_id(prefix: str, value: str) -> str:
  return f"{prefix}:{hashlib.sha256(value.encode()).hexdigest()[:20]}"


def derive_long_sentences(items: list[NormalizedItem], limit: int = 500) -> list[NormalizedItem]:
  output: list[NormalizedItem] = []
  for item in items:
    if item.get("module") != "bilingual_sentence":
      continue
    text: str = str(item.get("text", ""))
    words: list[str] = re.findall(r"[A-Za-z']+", text)
    lower: str = text.casefold()
    structures: list[str] = [label for marker, label in CLAUSE_MARKERS.items() if re.search(rf"\b{marker}\b", lower)]
    if len(words) < 16 or not structures:
      continue
    output.append({
      "id": stable_id("derived-long-sentence", str(item["id"])),
      "subject": "english",
      "module": "long_sentence",
      "title": text[:80],
      "text": text,
      "translation": str(item.get("translation", "")),
      "sourceId": str(item.get("sourceId", "")),
      "sourceUrl": str(item.get("sourceUrl", "")),
      "license": str(item.get("license", "")),
      "tags": list(dict.fromkeys(item.get("tags", []) + structures + ["长难句"])),
      "metadata": {
        "wordCount": len(words),
        "structures": structures,
        "analysisStatus": "rule-based",
        "originContentId": item["id"]
      }
    })
    if len(output) >= limit:
      break
  return output


def derive_vocabulary_questions(items: list[NormalizedItem], limit: int = 1000) -> list[NormalizedItem]:
  vocabulary: list[NormalizedItem] = [item for item in items if item.get("module") == "vocabulary" and item.get("metadata", {}).get("chineseMeaning")]
  output: list[NormalizedItem] = []
  for index, item in enumerate(vocabulary[:limit]):
    options: list[str] = [str(item["metadata"]["chineseMeaning"])]
    for offset in (1, 7, 17):
      if vocabulary:
        candidate: str = str(vocabulary[(index + offset) % len(vocabulary)]["metadata"]["chineseMeaning"])
        if candidate not in options:
          options.append(candidate)
    if len(options) < 3:
      continue
    output.append({
      "id": stable_id("derived-vocabulary-question", str(item["id"])),
      "subject": "english",
      "module": "question",
      "title": f"{item['title']} 词义辨析",
      "text": f"选择 {item['title']} 最合适的中文释义。",
      "sourceId": str(item.get("sourceId", "")),
      "sourceUrl": str(item.get("sourceUrl", "")),
      "license": str(item.get("license", "")),
      "tags": ["词汇练习", "自动生成"],
      "metadata": {
        "questionType": "singleChoice",
        "options": options,
        "answer": options[0],
        "explanation": str(item["metadata"]["chineseMeaning"]),
        "originContentId": item["id"]
      }
    })
  return output


def derive_chinese_techniques(items: list[NormalizedItem], limit: int = 1000) -> list[NormalizedItem]:
  output: list[NormalizedItem] = []
  for item in items:
    if item.get("subject") != "chinese":
      continue
    techniques: list[str] = item.get("metadata", {}).get("techniques", [])
    for technique in techniques:
      output.append({
        "id": stable_id("derived-chinese-technique", f"{item['id']}:{technique}"),
        "subject": "chinese",
        "module": "language_technique",
        "title": technique,
        "text": str(item.get("text", ""))[:300],
        "author": str(item.get("author", "")),
        "sourceId": str(item.get("sourceId", "")),
        "sourceUrl": str(item.get("sourceUrl", "")),
        "license": str(item.get("license", "")),
        "tags": list(dict.fromkeys(item.get("tags", []) + [technique, "表现手法"])),
        "metadata": {"technique": technique, "originContentId": item["id"], "reviewStatus": "rule-based-evidence"}
      })
      if len(output) >= limit:
        return output
  return output


def derive_teaching_items(items: list[NormalizedItem]) -> list[NormalizedItem]:
  return items + derive_long_sentences(items) + derive_vocabulary_questions(items) + derive_chinese_techniques(items)
