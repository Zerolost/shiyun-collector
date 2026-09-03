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


def main() -> None:
  target = Path(os.environ["DATA_REPO_DIR"])
  items: list[dict[str, Any]] = json.loads((DATA / "normalized.json").read_text("utf-8"))
  report: dict[str, Any] = json.loads((DATA / "report.json").read_text("utf-8"))
  normalized = target / "normalized"
  normalized.mkdir(parents=True, exist_ok=True)
  groups: dict[str, list[dict[str, Any]]] = {}
  for item in items:
    key: str = f"{item['subject']}/{item['module']}"
    groups.setdefault(key, []).append(item)
  for key, values in groups.items():
    path: Path = normalized / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    previous: list[dict[str, Any]] = []
    if path.exists():
      try:
        previous = json.loads(path.read_text("utf-8"))
      except (json.JSONDecodeError, OSError):
        previous = []
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
  manifest: dict[str, Any] = {
    "schemaVersion": 2,
    "updatedAt": datetime.now(UTC).isoformat(),
    "totalItems": sum(file["count"] for file in files),
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
