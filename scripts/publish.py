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


def main() -> None:
  target = Path(os.environ["DATA_REPO_DIR"])
  collected: list[dict[str, Any]] = json.loads((DATA / "collected.json").read_text("utf-8"))
  report: dict[str, Any] = json.loads((DATA / "report.json").read_text("utf-8"))
  raw_dir = target / "raw"
  raw_dir.mkdir(parents=True, exist_ok=True)
  files: list[dict[str, Any]] = []
  for item in collected:
    body: str = item.pop("payload")
    path = raw_dir / f"{item['id']}.json"
    document: dict[str, Any] = {**item, "payload": body}
    encoded: bytes = json.dumps(document, ensure_ascii=False, indent=2).encode()
    path.write_bytes(encoded)
    files.append({"path": str(path.relative_to(target)), "sha256": hashlib.sha256(encoded).hexdigest()})
  manifest: dict[str, Any] = {
    "schemaVersion": 1,
    "updatedAt": datetime.now(UTC).isoformat(),
    "count": len(files),
    "files": files,
    "report": report
  }
  (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")
  run(["git", "add", "-A"], target)
  changed = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=target)
  if changed.returncode == 0:
    print("no-data-changes")
    return
  run(["git", "commit", "-m", "Update collected language data"], target)
  run(["git", "push", "origin", "main"], target)


if __name__ == "__main__":
  main()
