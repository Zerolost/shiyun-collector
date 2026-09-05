import base64
import hmac
import os
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException

load_dotenv()

app = FastAPI(title="Shiyun Collector Gateway", docs_url=None, redoc_url=None)


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


@app.get("/health")
async def health() -> dict[str, str]:
  return {"status": "ok"}


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
  headers: dict[str, str] = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
  }
  async with httpx.AsyncClient(timeout=20) as client:
    response: httpx.Response = await client.post(url, headers=headers, json={"ref": "main", "inputs": {"profile": profile}})
  if response.status_code != 204:
    raise HTTPException(status_code=502, detail=f"GitHub dispatch failed: {response.status_code}")
  return {"accepted": True, "workflow": workflow, "profile": profile}
