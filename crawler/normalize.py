from typing import Any

from opencc import OpenCC

_SIMPLIFIER = OpenCC("t2s")


def to_simplified(value: str) -> str:
  return _SIMPLIFIER.convert(value)


def normalize_item(item: dict[str, Any]) -> dict[str, Any]:
  output: dict[str, Any] = dict(item)
  for key in ("title", "text", "translation", "author"):
    if isinstance(output.get(key), str):
      output[key] = to_simplified(output[key])
  if isinstance(output.get("tags"), list):
    output["tags"] = [to_simplified(str(tag)) for tag in output["tags"]]
  metadata: Any = output.get("metadata")
  if isinstance(metadata, dict):
    if output.get("subject") == "english" and output.get("module") in {"vocabulary", "bilingual_sentence", "long_sentence", "grammar"}:
      metadata["learningStage"] = metadata.get("learningStage", "high-school-core")
    if output.get("subject") == "chinese":
      metadata["learningStage"] = metadata.get("learningStage", "high-school-core")
    output["metadata"] = {
      key: to_simplified(value) if isinstance(value, str) else value
      for key, value in metadata.items()
    }
  return output
