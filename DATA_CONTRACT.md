# Shiyun Cloud Data Contract

## Published repository

`Zerolost/shiyun-data` is the published normalized data repository.

## Manifest

`manifest.json` is the synchronization entry point.

Required fields:

```text
schemaVersion
updatedAt
totalItems
files[].path
files[].count
files[].sha256
latestProfile
errors
```

Clients must download a changed file only when its path or SHA-256 differs from the cached manifest.

## Normalized item

Every item contains:

```text
id
subject
module
title
text
sourceId
sourceUrl
license
tags
metadata
```

Optional shared fields:

```text
translation
author
```

## Chinese modules

```text
chinese_quote
classical_text
essay_material
famous_quote
language_technique
chinese_reading
```

Chinese teaching metadata may contain:

```text
themes
techniques
argumentAngles
usageContext
imitationPrompt
misuseWarning
learningStage
reviewStatus
questions
answerGuide
```

## English modules

```text
vocabulary
sentence_corpus
bilingual_sentence
grammar
long_sentence
word_story
reading_material
question
```

English metadata may contain:

```text
chineseMeaning
englishDefinitions
englishExamples
exampleSentences
phonetic
partOfSpeech
learningStage
structures
keyPoints
commonErrors
options
answer
explanation
```

## Required module-specific fields

| Module | Required fields |
|---|---|
| `bilingual_sentence` | `text`, `translation` |
| `grammar` | `text`, `translation`, `metadata.stage`, `metadata.keyPoints` |
| `long_sentence` | `text`, `translation`, `metadata.structures` |
| `vocabulary` | `translation` or `metadata.chineseMeaning` or `metadata.englishDefinitions` |
| `question` | `metadata.options`, `metadata.answer`, `metadata.explanation` |
| `chinese_reading` | `metadata.questions`, `metadata.answerGuide` |

## Data quality

- All source and license fields are required.
- Automatic derivations have `reviewStatus` or an equivalent status field.
- Existing reliable translation is preserved.
- Machine translation may be cached with provider and original hash, but must not overwrite a reliable source translation.
- The client must show unavailable translation honestly.

## Sync policy

1. Display local cache immediately.
2. Fetch manifest in background.
3. Download changed module shards only.
4. Validate JSON before replacing local cache.
5. Retain last valid cache on network or parsing failure.
6. Never store GitHub access tokens in the client.
