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

## cron-job.org request

- Method: `POST`
- URL: `https://<project>.pocketbay.app/internal/dispatch`
- Header: `X-Cron-Secret: <CRON_SECRET>`
- Initial frequency: every 30 minutes

Only sources with an explicit reusable/public-domain license should be added to `sources/registry.json`.
