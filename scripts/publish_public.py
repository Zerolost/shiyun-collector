import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/tmp/shiyun-data/normalized")
TARGET = ROOT / "published" / "api" / "v1"
RAW_BASE = "https://raw.githubusercontent.com/Zerolost/shiyun-collector/main/published/api/v1"


def compact(value: Any) -> str:
  return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
  if not SOURCE.exists():
    raise RuntimeError("Private normalized data is unavailable")
  manifest_shards: list[dict[str, Any]] = []
  updated_at = datetime.now(UTC).isoformat()
  data_root = TARGET / "data"
  for source in sorted(SOURCE.glob("*/*.json")):
    subject = source.parent.name
    module = source.stem
    items: list[Any] = json.loads(source.read_text("utf-8"))
    encoded = compact(items)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    target = data_root / subject / f"{module}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    response = {
      "schemaVersion": 3,
      "contentVersion": updated_at,
      "updatedAt": updated_at,
      "subject": subject,
      "module": module,
      "count": len(items),
      "items": items,
      "source": "Shiyun normalized public mirror"
    }
    target.write_text(compact(response), "utf-8")
    manifest_shards.append({
      "subject": subject,
      "module": module,
      "url": f"{RAW_BASE}/data/{subject}/{module}.json",
      "count": len(items),
      "sha256": digest,
      "updatedAt": updated_at
    })
  manifest = {
    "schemaVersion": 3,
    "contentVersion": updated_at,
    "updatedAt": updated_at,
    "shards": manifest_shards
  }
  TARGET.mkdir(parents=True, exist_ok=True)
  (TARGET / "manifest.json").write_text(compact(manifest), "utf-8")


if __name__ == "__main__":
  main()
