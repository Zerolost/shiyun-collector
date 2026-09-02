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

- Sign in again to `https://console.cron-job.org/` because the browser session expired before saving jobs
- Create wake job: `GET https://shiyun-collector.pocketbay.app/health`, cron `0,30 * * * *`
- Create dispatch job: `POST https://shiyun-collector.pocketbay.app/internal/dispatch`, cron `2,32 * * * *`
- Add request header `X-Cron-Secret`; the rotated value has been copied to the iOS clipboard
- This gives PocketBay roughly 28 minutes of idle time between collection windows so it may sleep

## Notes

- PocketBay does not run Cron workers; cron-job.org provides scheduling.
- The workflow runs in the public collector repository, avoiding private-repository Actions minute limits for the collection job.
- Do not expose the cron secret or GitHub tokens in code, logs, or chat.
