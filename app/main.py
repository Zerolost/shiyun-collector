import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException

load_dotenv()

app = FastAPI(title="Shiyun Collector Gateway", docs_url=None, redoc_url=None)
CACHE_SECONDS = 600
ALLOWED_MODULES: dict[str, set[str]] = {
  "chinese": {"chinese_quote", "classical_text", "essay_material", "famous_quote", "language_technique", "chinese_reading"},
  "english": {"vocabulary", "sentence_corpus", "bilingual_sentence", "grammar", "long_sentence", "word_story", "reading_material", "question"}
}
cache: dict[str, tuple[float, Any]] = {}


def required_env(name: str) -> str:
  value: str | None = os.getenv(name)
  if not value:
    raise RuntimeError(f"Missing environment variable: {name}")
  return value


def has_valid_basic_auth(authorization: str, expected: str) -> bool:
  if not authorization.startswith("Basic "):
    return False
  try:
    decoded: str = base64.b64decode(authorization[6:]).decode("utf-8")
    _, password = decoded.split(":", 1)
  except (ValueError, UnicodeDecodeError):
    return False
  return hmac.compare_digest(password, expected)


def json_hash(value: Any) -> str:
  encoded: bytes = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
  return hashlib.sha256(encoded).hexdigest()


def valid_module(subject: str, module: str) -> bool:
  return subject in ALLOWED_MODULES and module in ALLOWED_MODULES[subject]


async def github_json(path: str) -> Any:
  key: str = f"github:{path}"
  cached: tuple[float, Any] | None = cache.get(key)
  if cached and time.time() - cached[0] < CACHE_SECONDS:
    return cached[1]
  owner: str = required_env("GITHUB_OWNER")
  repository: str = os.getenv("GITHUB_DATA_REPO", f"{owner}/shiyun-data")
  token: str = required_env("GITHUB_TOKEN")
  url: str = f"https://api.github.com/repos/{repository}/contents/{path}"
  headers: dict[str, str] = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.raw+json",
    "X-GitHub-Api-Version": "2022-11-28"
  }
  async with httpx.AsyncClient(timeout=30) as client:
    response: httpx.Response = await client.get(url, headers=headers)
  if response.status_code == 404:
    raise HTTPException(status_code=404, detail="Data shard not found")
  if response.status_code != 200:
    raise HTTPException(status_code=502, detail=f"Private data fetch failed: {response.status_code}")
  try:
    value: Any = response.json()
  except ValueError as error:
    raise HTTPException(status_code=502, detail="Private data response invalid") from error
  cache[key] = (time.time(), value)
  return value


async def current_manifest() -> dict[str, Any]:
  key = "manifest"
  cached: tuple[float, Any] | None = cache.get(key)
  if cached and time.time() - cached[0] < CACHE_SECONDS:
    return cached[1]
  raw: dict[str, Any] = await github_json("manifest.json")
  shards: list[dict[str, Any]] = []
  for file in raw.get("files", []):
    path: str = str(file.get("path", ""))
    parts: list[str] = path.split("/")
    if len(parts) != 3 or parts[0] != "normalized" or not parts[2].endswith(".json"):
      continue
    subject, filename = parts[1], parts[2]
    module: str = filename.removesuffix(".json")
    if not valid_module(subject, module):
      continue
    items: list[Any] = await github_json(path)
    if not isinstance(items, list):
      continue
    shards.append({
      "subject": subject,
      "module": module,
      "url": f"/api/v1/data/{subject}/{module}",
      "count": len(items),
      "sha256": json_hash(items),
      "updatedAt": str(raw.get("updatedAt", ""))
    })
  manifest: dict[str, Any] = {
    "schemaVersion": 3,
    "contentVersion": str(raw.get("updatedAt", "v1")),
    "updatedAt": str(raw.get("updatedAt", "")),
    "shards": shards
  }
  cache[key] = (time.time(), manifest)
  return manifest


@app.get("/health")
async def health() -> dict[str, str]:
  return {"status": "ok"}


@app.get("/api/v1/manifest")
async def manifest() -> dict[str, Any]:
  return await current_manifest()


@app.get("/api/v1/data/{subject}/{module}")
async def shard(subject: str, module: str) -> dict[str, Any]:
  if not valid_module(subject, module):
    raise HTTPException(status_code=404, detail="Unknown data module")
  manifest_value: dict[str, Any] = await current_manifest()
  entry: dict[str, Any] | None = next((value for value in manifest_value["shards"] if value["subject"] == subject and value["module"] == module), None)
  if entry is None:
    raise HTTPException(status_code=404, detail="Data shard not published")
  items: list[Any] = await github_json(f"normalized/{subject}/{module}.json")
  return {
    "schemaVersion": 3,
    "contentVersion": manifest_value["contentVersion"],
    "updatedAt": manifest_value["updatedAt"],
    "subject": subject,
    "module": module,
    "count": len(items),
    "items": items,
    "source": "Zerolost/shiyun-data"
  }


@app.post("/internal/dispatch", status_code=202)
async def dispatch(
  profile: str = "frequent",
  x_cron_secret: str = Header(default=""),
  authorization: str = Header(default="")
) -> dict[str, Any]:
  if profile not in {"frequent", "daily", "weekly"}:
    raise HTTPException(status_code=400, detail="Invalid collection profile")
  expected: str = required_env("CRON_SECRET")
  if not hmac.compare_digest(x_cron_secret, expected) and not has_valid_basic_auth(authorization, expected):
    raise HTTPException(status_code=401, detail="Unauthorized")
  owner: str = required_env("GITHUB_OWNER")
  repo: str = required_env("GITHUB_COLLECTOR_REPO")
  token: str = required_env("GITHUB_TOKEN")
  workflow: str = os.getenv("GITHUB_WORKFLOW", "crawl.yml")
  url: str = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"
  headers: dict[str, str] = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
  async with httpx.AsyncClient(timeout=20) as client:
    response: httpx.Response = await client.post(url, headers=headers, json={"ref": "main", "inputs": {"profile": profile}})
  if response.status_code != 204:
    raise HTTPException(status_code=502, detail=f"GitHub dispatch failed: {response.status_code}")
  return {"accepted": True, "workflow": workflow, "profile": profile}
