# Shiyun Collector Status

## Current status

The cloud data layer is not yet complete for Shiyun integration.

## Latest verified private data

- Repository: `Zerolost/shiyun-data`
- Schema: 3
- Total normalized items: 40,913
- Latest profile: weekly
- Collection errors: 0

## Current normalized modules

- Chinese quotes: 2,891
- Chinese classical text: 1,270
- Chinese essay material: 218
- Chinese famous quotes: 11
- Chinese language techniques: 1,000
- English bilingual sentences: 648, all with translations
- English grammar: 5
- English long sentences: 288, all with translations
- English generated questions: 1,000
- English reading material: 41
- English sentence corpus: 8,000
- English vocabulary: 25,541

## Completed in the latest cycle

- ECDICT and Open English WordNet vocabulary merge
- Chinese traditional-to-simplified conversion
- Tatoeba English-Chinese sentence pairs
- Rule-based Chinese themes, argument angles and language-technique evidence
- Rule-based English long-sentence derivation
- Rule-based English vocabulary questions
- Normalized-data quality gate
- Frequent, daily and weekly collection profiles
- GitHub Actions remote runs for daily and weekly profiles

## Known gaps before Shiyun integration

- English vocabulary needs reliable Chinese translation coverage in the final schema, not only metadata.
- English grammar has only a small foundation set and needs broader high-school coverage.
- English word stories are not yet populated.
- Chinese modern good phrases need richer explanation, usage context, imitation examples and review.
- Chinese essay material needs verified facts, themes, argument angles and usage cautions.
- Chinese reading comprehension and Chinese grammar/technique curriculum need dedicated modules.
- Generated questions are rule-based and require stronger review before educational use.
- Stage classification is currently source/rule based and needs high-school level curation.
- Oxford and Cambridge data are not included without an official API or license.

## Decision

Do not start Shiyun cloud-data integration yet. Continue data completion and quality review until all required Chinese and English modules are non-empty with required fields and a published data contract.

## Scheduler

Use direct cron-job.org to GitHub Actions dispatch. PocketBay is not required for scheduled collection. GitHub workflow dispatch success is HTTP 204.
