import json
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parents[1] / ".data" / "normalized.json"


def main() -> None:
  items: list[dict[str, Any]] = json.loads(DATA.read_text("utf-8"))
  errors: list[str] = []
  ids: set[str] = set()
  for item in items:
    item_id: str = str(item.get("id", ""))
    if not item_id or item_id in ids:
      errors.append(f"invalid-or-duplicate-id:{item_id}")
    ids.add(item_id)
    for field in ("subject", "module", "title", "sourceId", "sourceUrl", "license"):
      if not item.get(field):
        errors.append(f"{item_id}:missing-{field}")
    if item.get("module") in {"bilingual_sentence", "long_sentence", "grammar"} and not item.get("translation"):
      errors.append(f"{item_id}:missing-translation")
    if item.get("subject") == "english" and item.get("module") == "vocabulary" and not item.get("translation") and not item.get("metadata", {}).get("chineseMeaning") and not item.get("metadata", {}).get("englishDefinitions"):
      errors.append(f"{item_id}:missing-definition" )
    if item.get("module") == "vocabulary":
      metadata: dict[str, Any] = item.get("metadata", {})
      if not metadata.get("chineseMeaning") and not metadata.get("englishDefinitions") and not item.get("text"):
        errors.append(f"{item_id}:missing-definition")
    if item.get("module") == "grammar":
      metadata = item.get("metadata", {})
      if not item.get("translation") or not metadata.get("stage") or not metadata.get("keyPoints"):
        errors.append(f"{item_id}:incomplete-grammar")
    if item.get("module") == "long_sentence" and (not item.get("translation") or not item.get("metadata", {}).get("structures")):
      errors.append(f"{item_id}:incomplete-long-sentence")
    if item.get("module") == "question":
      metadata = item.get("metadata", {})
      if not metadata.get("options") or not metadata.get("answer") or not metadata.get("explanation"):
        errors.append(f"{item_id}:incomplete-question")
  modules: dict[str, int] = {}
  for item in items:
    module: str = str(item.get("module", ""))
    modules[module] = modules.get(module, 0) + 1
  report_path = DATA.parent / "report.json"
  profile: str = "all"
  if report_path.exists():
    profile = json.loads(report_path.read_text("utf-8")).get("profile", "all")
  profile_modules: dict[str, set[str]] = {
    "frequent": {"classical_text", "famous_quote", "essay_material", "sentence_corpus"},
    "daily": {"chinese_quote", "classical_text", "language_technique", "grammar", "sentence_corpus"},
    "weekly": {"bilingual_sentence", "vocabulary", "long_sentence", "word_story", "question"},
    "all": {"chinese_quote", "essay_material", "classical_text", "language_technique", "chinese_reading", "bilingual_sentence", "vocabulary", "grammar", "long_sentence", "word_story", "question"}
  }
  for module in sorted(profile_modules.get(profile, profile_modules["all"])):
    if modules.get(module, 0) == 0:
      errors.append(f"missing-module:{module}")
  print(json.dumps({"items": len(items), "modules": modules, "errors": len(errors), "sampleErrors": errors[:20]}, ensure_ascii=False))
  if errors:
    raise SystemExit(1)


if __name__ == "__main__":
  main()
