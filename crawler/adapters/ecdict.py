import csv
import io
from typing import Any

from models import NormalizedItem


def parse(payload: bytes, source: dict[str, Any]) -> list[NormalizedItem]:
  text: str = payload.decode("utf-8", errors="replace")
  items: list[NormalizedItem] = []
  limit: int = int(source.get("limit", 12000))
  reader = csv.DictReader(io.StringIO(text))
  for row in reader:
    word: str = str(row.get("word", "")).strip()
    translation: str = str(row.get("translation", "")).strip()
    if not word or not translation or len(word) > 40:
      continue
    items.append({
      "id": f"{source['id']}:{word.lower()}",
      "subject": "english",
      "module": "vocabulary",
      "title": word,
      "text": translation,
      "sourceId": source["id"],
      "sourceUrl": source["homepage"],
      "license": source["license"],
      "tags": ["英汉词典"],
      "metadata": {
        "phonetic": str(row.get("phonetic", "")),
        "partOfSpeech": str(row.get("pos", "")),
        "chineseMeaning": translation,
        "collins": str(row.get("collins", "")),
        "oxford": str(row.get("oxford", "")),
        "bnc": str(row.get("bnc", "")),
        "frq": str(row.get("frq", "")),
        "exchange": str(row.get("exchange", ""))
      }
    })
    if len(items) >= limit:
      break
  return items
