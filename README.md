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

## cron-job.org requests

Create exactly two jobs and do not duplicate them.

Wake job:

- Method: `GET`
- URL: `https://shiyun-collector.pocketbay.app/health`
- Schedule: every 30 minutes

Dispatch job:

- Method: `POST`
- URL: `https://shiyun-collector.pocketbay.app/internal/dispatch?profile=frequent`
- Schedule: two minutes after wake, every 30 minutes
- Header: `X-Cron-Secret: <current CRON_SECRET>`

A `204` from `/health` can mean the PocketBay app is sleeping or waking. A `403` from `/internal/dispatch` means the header secret is missing or stale; edit the existing dispatch job instead of creating another job. Do not expose the secret in logs or chat.

Only sources with an explicit reusable/public-domain license should be added to `sources/registry.json`.
