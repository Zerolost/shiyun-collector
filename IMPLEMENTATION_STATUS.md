# Implementation Status

## Status

Core collection pipeline is running.

## GitHub

- Public collector repository: `Zerolost/shiyun-collector`
- Private data repository: `Zerolost/shiyun-data`
- Workflow: `.github/workflows/crawl.yml`
- Secrets configured: `DATA_REPO`, `DATA_REPO_TOKEN`

## PocketBay

- URL: `https://shiyun-collector.pocketbay.app`
- Health: `GET /health` returns 200
- Dispatch: `POST /internal/dispatch` returns 202 with a valid `X-Cron-Secret`

## Collection

- Registered sources: 4
- Latest remote collection: 4 successful, 0 errors
- Private manifest contains 4 raw source files

## Verified chain

`PocketBay dispatch → GitHub Actions → source collection → private repository publish` completed successfully.

## Remaining setup

- Sign in to `https://console.cron-job.org/`
- Create a POST job for `https://shiyun-collector.pocketbay.app/internal/dispatch`
- Add request header `X-Cron-Secret`; its value has been copied to the iOS clipboard
- Recommended initial interval: every 10 minutes

## Notes

- PocketBay does not run Cron workers; cron-job.org provides scheduling.
- The workflow runs in the public collector repository, avoiding private-repository Actions minute limits for the collection job.
- Do not expose the cron secret or GitHub tokens in code, logs, or chat.
