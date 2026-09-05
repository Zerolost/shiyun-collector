import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / ".data"


def run(command: list[str], cwd: Path) -> None:
  subprocess.run(command, cwd=cwd, check=True)


def encoded_json(value: Any) -> bytes:
  return json.dumps(value, ensure_ascii=False, indent=2).encode()


def merge_vocabulary(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
  grouped: dict[str, list[dict[str, Any]]] = {}
  for item in items:
    if item.get("subject") == "english" and item.get("module") == "vocabulary":
      grouped.setdefault(str(item.get("title", "")).casefold(), []).append(item)
  merged: list[dict[str, Any]] = []
  for key, group in grouped.items():
    preferred: dict[str, Any] = next((item for item in group if item.get("sourceId") == "ecdict-open-english-chinese"), group[0])
    metadata: dict[str, Any] = dict(preferred.get("metadata", {}))
    definitions: list[str] = []
    examples: list[str] = []
    sources: list[str] = []
    licenses: list[str] = []
    tags: list[str] = []
    for item in group:
      item_metadata: dict[str, Any] = item.get("metadata", {})
      definitions.extend(item_metadata.get("englishDefinitions", []))
      examples.extend(item_metadata.get("englishExamples", []))
      sources.append(str(item.get("sourceId", "")))
      licenses.append(str(item.get("license", "")))
      tags.extend(item.get("tags", []))
      if not metadata.get("chineseMeaning") and item_metadata.get("chineseMeaning"):
        metadata["chineseMeaning"] = item_metadata["chineseMeaning"]
    metadata["englishDefinitions"] = list(dict.fromkeys(definitions))
    metadata["englishExamples"] = list(dict.fromkeys(examples))
    metadata["sourceIds"] = list(dict.fromkeys(sources))
    metadata["licenses"] = list(dict.fromkeys(licenses))
    preferred["id"] = f"english-vocabulary:{key}"
    preferred["tags"] = list(dict.fromkeys(tags))
    preferred["metadata"] = metadata
    preferred["text"] = str(metadata.get("englishDefinitions") and "; ".join(metadata["englishDefinitions"]) or metadata.get("chineseMeaning", ""))
    preferred["translation"] = str(metadata.get("chineseMeaning", ""))
    preferred["metadata"] = {**metadata, "learningStage": "high-school-core"}
    merged.append(preferred)
  non_vocabulary: list[dict[str, Any]] = [item for item in items if not (item.get("subject") == "english" and item.get("module") == "vocabulary")]
  return non_vocabulary + merged


def derive_cross_module_content(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
  derived: list[dict[str, Any]] = []
  for item in items:
    if item.get("subject") == "chinese" and item.get("module") == "essay_material":
      source_id: str = str(item.get("id", ""))
      derived.append({
        "id": f"chinese-reading:{hashlib.sha256(source_id.encode()).hexdigest()[:20]}",
        "subject": "chinese",
        "module": "chinese_reading",
        "title": f"{item.get('title', '现代文')}阅读训练",
        "text": item.get("text", ""),
        "sourceId": item.get("sourceId", ""),
        "sourceUrl": item.get("sourceUrl", ""),
        "license": item.get("license", ""),
        "tags": list(dict.fromkeys(item.get("tags", []) + ["阅读理解", "信息提取"])),
        "metadata": {
          "questions": ["概括文本主要内容", "结合文本分析表达效果"],
          "answerGuide": "依据文本事实组织答案，结合关键词分点作答",
          "originContentId": source_id,
          "reviewStatus": "auto-derived"
        }
      })
  return items + derived


def main() -> None:
  target = Path(os.environ["DATA_REPO_DIR"])
  items: list[dict[str, Any]] = json.loads((DATA / "normalized.json").read_text("utf-8"))
  report: dict[str, Any] = json.loads((DATA / "report.json").read_text("utf-8"))
  normalized = target / "normalized"
  existing_essay_path: Path = normalized / "chinese" / "essay_material.json"
  if existing_essay_path.exists():
    existing_essay: list[dict[str, Any]] = json.loads(existing_essay_path.read_text("utf-8"))
    items.extend(existing_essay)
  items = derive_cross_module_content(merge_vocabulary(items))
  normalized.mkdir(parents=True, exist_ok=True)
  groups: dict[str, list[dict[str, Any]]] = {}
  for item in items:
    key: str = f"{item['subject']}/{item['module']}"
    groups.setdefault(key, []).append(item)
  for key, values in groups.items():
    path: Path = normalized / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    previous: list[dict[str, Any]] = []
    replace_vocabulary: bool = key == "english/vocabulary" and report["profile"] == "weekly"
    if path.exists() and not replace_vocabulary:
      try:
        previous = json.loads(path.read_text("utf-8"))
      except (json.JSONDecodeError, OSError):
        previous = []
    if key == "english/vocabulary" and report["profile"] == "weekly":
      sentence_paths: list[Path] = [normalized / "english" / "sentence_corpus.json", normalized / "english" / "bilingual_sentence.json"]
      sentences: list[dict[str, Any]] = []
      for sentence_path in sentence_paths:
        if sentence_path.exists():
          sentences.extend(json.loads(sentence_path.read_text("utf-8")))
      for value in values:
        word: str = str(value.get("title", ""))
        examples: list[dict[str, str]] = []
        for sentence in sentences:
          text: str = str(sentence.get("text", ""))
          tokens: set[str] = {token.casefold().strip(".,!?;:'\"()[]{}") for token in text.split()}
          if word.casefold() not in tokens:
            continue
          example: dict[str, str] = {"english": text}
          if sentence.get("translation"):
            example["chinese"] = str(sentence["translation"])
          examples.append(example)
          if len(examples) >= 3:
            break
        if examples:
          value["metadata"] = {**value.get("metadata", {}), "exampleSentences": examples}
    merged: dict[str, dict[str, Any]] = {value["id"]: value for value in previous}
    merged.update({value["id"]: value for value in values})
    path.write_bytes(encoded_json(sorted(merged.values(), key=lambda value: value["id"])))
  files: list[dict[str, Any]] = []
  for path in sorted(normalized.rglob("*.json")):
    content: bytes = path.read_bytes()
    values: list[dict[str, Any]] = json.loads(content)
    files.append({
      "path": str(path.relative_to(target)),
      "count": len(values),
      "sha256": hashlib.sha256(content).hexdigest()
    })
  reports = target / "reports"
  reports.mkdir(exist_ok=True)
  (reports / f"latest-{report['profile']}.json").write_bytes(encoded_json(report))
  existing_manifest: dict[str, Any] = {}
  manifest_path: Path = target / "manifest.json"
  if manifest_path.exists():
    try:
      existing_manifest = json.loads(manifest_path.read_text("utf-8"))
    except (json.JSONDecodeError, OSError):
      existing_manifest = {}
  total_items: int = sum(file["count"] for file in files)
  previous_total: int = int(existing_manifest.get("totalItems", 0))
  if report["profile"] == "frequent" and previous_total and total_items < previous_total:
    raise RuntimeError(f"Frequent publish would reduce total items: {previous_total} -> {total_items}")
  manifest: dict[str, Any] = {
    "schemaVersion": 3,
    "updatedAt": datetime.now(UTC).isoformat(),
    "totalItems": total_items,
    "files": files,
    "latestProfile": report["profile"],
    "sourceResults": report["sourceResults"],
    "errors": report["errors"]
  }
  (target / "manifest.json").write_bytes(encoded_json(manifest))
  run(["git", "add", "-A"], target)
  changed = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=target)
  if changed.returncode == 0:
    print("no-data-changes")
    return
  run(["git", "commit", "-m", f"Update {report['profile']} language data"], target)
  run(["git", "push", "origin", "main"], target)


if __name__ == "__main__":
  main()
