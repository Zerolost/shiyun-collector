import hashlib
import re
from typing import Any

from models import NormalizedItem

THEMES: dict[str, tuple[str, ...]] = {
  "学习成长": ("学", "思", "志", "勤", "行"),
  "责任担当": ("国", "民", "义", "责", "天下"),
  "理想求索": ("路", "梦", "求", "远", "登"),
  "自然审美": ("山", "水", "月", "风", "花"),
  "逆境坚持": ("难", "苦", "孤", "寒", "志")
}

TECHNIQUES: dict[str, tuple[str, ...]] = {
  "比喻": ("如", "似", "若", "犹"),
  "对偶": ("兮",),
  "借景抒情": ("山", "水", "月", "风"),
  "用典": ("尧", "舜", "禹", "周公"),
  "反问": ("何", "岂", "焉", "谁")
}


def match_labels(text: str, rules: dict[str, tuple[str, ...]]) -> list[str]:
  return [name for name, words in rules.items() if any(word in text for word in words)]


def derive_chinese(items: list[NormalizedItem]) -> list[NormalizedItem]:
  derived: list[NormalizedItem] = []
  for item in items:
    if item.get("subject") != "chinese":
      continue
    text: str = str(item.get("text", ""))
    metadata: dict[str, Any] = dict(item.get("metadata", {}))
    themes: list[str] = match_labels(text, THEMES)
    techniques: list[str] = match_labels(text, TECHNIQUES)
    metadata["themes"] = themes
    metadata["techniques"] = techniques
    metadata["reviewStatus"] = "auto-classified"
    item["metadata"] = metadata
    if item.get("module") != "classical_text":
      continue
    sentences: list[str] = [part.strip() for part in re.split(r"[。！？!?\n]", text) if 8 <= len(part.strip()) <= 80]
    for sentence in sentences[:3]:
      stable: str = hashlib.sha256(f"{item['id']}:{sentence}".encode()).hexdigest()[:20]
      derived.append({
        "id": f"derived-chinese-quote:{stable}",
        "subject": "chinese",
        "module": "chinese_quote",
        "title": item.get("title", "古典佳句"),
        "text": sentence,
        "author": item.get("author", ""),
        "sourceId": item.get("sourceId", ""),
        "sourceUrl": item.get("sourceUrl", ""),
        "license": item.get("license", ""),
        "tags": list(dict.fromkeys(item.get("tags", []) + themes + techniques + ["好词好句"])),
        "metadata": {
          "themes": themes,
          "techniques": techniques,
          "argumentAngles": themes,
          "originContentId": item["id"],
          "reviewStatus": "auto-extracted"
        }
      })
  unique: dict[str, NormalizedItem] = {item["id"]: item for item in derived}
  return items + list(unique.values())
