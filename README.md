# Shiyun Collector

Personal language-content collection pipeline for the Scripting project 诗云.

## Architecture

- cron-job.org sends an authenticated HTTP request.
- PocketBay exposes the minimal `/internal/dispatch` gateway.
- The gateway triggers this repository's `crawl.yml` workflow.
- GitHub Actions fetches registered open sources concurrently.
- Changed results are committed to a separate private data repository.

## Required PocketBay environment variables

- `CRON_SECRET`
- `GITHUB_TOKEN`
- `GITHUB_OWNER`
- `GITHUB_COLLECTOR_REPO`
- `GITHUB_WORKFLOW=crawl.yml`

## Required GitHub Actions secrets

- `DATA_REPO`: `owner/private-data-repository`
- `DATA_REPO_TOKEN`: fine-grained token with Contents write access to the private data repository

## Direct cron-job.org scheduling

PocketBay is not required for scheduled collection. To avoid sleep-layer ambiguity and runtime credits, use one cron-job.org job that calls GitHub Actions directly.

- Method: `POST`
- URL: `https://api.github.com/repos/Zerolost/shiyun-collector/actions/workflows/crawl.yml/dispatches`
- Schedule: every 30 minutes for `frequent`
- Header: `Authorization: Bearer <SHIYUN_GITHUB_TOKEN>`
- Header: `Accept: application/vnd.github+json`
- Header: `X-GitHub-Api-Version: 2022-11-28`
- Body: `{"ref":"main","inputs":{"profile":"frequent"}}`
- Content-Type: `application/json`

A successful GitHub workflow dispatch returns HTTP `204 No Content`. That is expected and means GitHub accepted the trigger. GitHub Actions runs independently after the response.

Token permissions should be restricted to the `Zerolost/shiyun-collector` repository with Actions read/write and the minimum metadata/contents permissions required by the workflow. Do not put the token in source files or logs.

For daily and weekly jobs, create separate schedules with bodies `{"ref":"main","inputs":{"profile":"daily"}}` and `{"ref":"main","inputs":{"profile":"weekly"}}`. Keep one job per profile; do not duplicate jobs.

Only sources with an explicit reusable/public-domain license should be added to `sources/registry.json`.
