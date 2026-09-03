import io
import json
import re
import zipfile
from typing import Any

from models import NormalizedItem

WORD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z -]{1,30}$")


def parse(payload: bytes, source: dict[str, Any]) -> list[NormalizedItem]:
  items: list[NormalizedItem] = []
  limit: int = int(source.get("limit", 8000))
  with zipfile.ZipFile(io.BytesIO(payload)) as archive:
    entry_files: list[str] = sorted(name for name in archive.namelist() if name.startswith("entries-") and name.endswith(".json"))
    for name in entry_files:
      data: dict[str, Any] = json.loads(archive.read(name))
      for word, lexical in data.items():
        if not WORD_PATTERN.fullmatch(word):
          continue
        for part_of_speech, details in lexical.items():
          pronunciation: str = ""
          values: list[dict[str, Any]] = details.get("pronunciation", [])
          if values:
            pronunciation = str(values[0].get("value", ""))
          senses: list[dict[str, Any]] = details.get("sense", [])
          if not senses:
            continue
          items.append({
            "id": f"{source['id']}:{word.lower()}:{part_of_speech}",
            "subject": "english",
            "module": "vocabulary",
            "title": word,
            "text": "",
            "sourceId": source["id"],
            "sourceUrl": source["homepage"],
            "license": source["license"],
            "tags": ["wordnet", part_of_speech],
            "metadata": {
              "partOfSpeech": part_of_speech,
              "phonetic": pronunciation,
              "senseIds": [sense.get("id") for sense in senses[:5]],
              "synsetIds": [sense.get("synset") for sense in senses[:5]]
            }
          })
          break
        if len(items) >= limit:
          return items
  return items
