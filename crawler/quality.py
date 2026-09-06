import re
from typing import Any

try:
  from .normalize import to_simplified
except ImportError:
  from normalize import to_simplified

NormalizedItem = dict[str, Any]

ENGLISH_WORD = re.compile(r"^[A-Za-z]+(?:['-][A-Za-z]+)*$")
UNREVIEWED_ESSAY_SOURCE = "zh-wikipedia-current"
TRADITIONAL_VARIANTS: dict[str, str] = {
  "襌": "禅",
  "詣": "诣",
  "讀": "读",
  "經": "经",
  "劔": "剑",
  "閟": "闺",
  "宫": "宫",
}


def is_usable_vocabulary_title(value: str) -> bool:
  word: str = value.strip()
  if not 2 <= len(word) <= 28:
    return False
  if not ENGLISH_WORD.fullmatch(word):
    return False
  if word.startswith(("-", "'")) or word.endswith(("-", "'")):
    return False
  return True


def is_usable_essay_item(item: NormalizedItem) -> bool:
  if item.get("sourceId") == UNREVIEWED_ESSAY_SOURCE:
    return False
  title: str = str(item.get("title", "")).strip()
  text: str = str(item.get("text", "")).strip()
  tags: set[str] = {str(tag) for tag in item.get("tags", [])}
  return len(title) >= 4 and len(text) >= 80 and bool(tags & {"议论文素材", "作文素材", "人物素材", "时事素材"})


def normalize_learning_stage(metadata: dict[str, Any]) -> dict[str, Any]:
  output: dict[str, Any] = dict(metadata)
  stage: str = str(output.get("learningStage", "")).strip()
  if stage in {"", "high-school-core", "g10s1", "高一上"}:
    output["learningStage"] = "high-school-general"
  return output


def has_traditional_chinese(item: NormalizedItem) -> bool:
  for value in walk_text(item):
    if to_simplified(value) != value:
      return True
  return False


def walk_text(value: Any) -> list[str]:
  if isinstance(value, str):
    return [value]
  if isinstance(value, list):
    return [text for item in value for text in walk_text(item)]
  if isinstance(value, dict):
    return [text for item in value.values() for text in walk_text(item)]
  return []


def simplify_text(value: Any) -> Any:
  if isinstance(value, str):
    simplified: str = to_simplified(value)
    for traditional, simplified_variant in TRADITIONAL_VARIANTS.items():
      simplified = simplified.replace(traditional, simplified_variant)
    return simplified
  if isinstance(value, list):
    return [simplify_text(item) for item in value]
  if isinstance(value, dict):
    return {key: simplify_text(item) for key, item in value.items()}
  return value


def filter_quality(items: list[NormalizedItem]) -> list[NormalizedItem]:
  output: list[NormalizedItem] = []
  for original in items:
    item: NormalizedItem = simplify_text(dict(original))
    module: str = str(item.get("module", ""))
    if module == "vocabulary" and not is_usable_vocabulary_title(str(item.get("title", ""))):
      continue
    if module == "essay_material" and not is_usable_essay_item(item):
      continue
    metadata: dict[str, Any] = normalize_learning_stage(dict(item.get("metadata", {})))
    item["metadata"] = metadata
    output.append(item)
  return output
