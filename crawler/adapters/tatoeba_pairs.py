import bz2
import io
import tarfile
from typing import Any

from models import NormalizedItem


def parse(payload: Any, source: dict[str, Any]) -> list[NormalizedItem]:
  english_raw, chinese_raw, links_raw = payload
  english: dict[str, str] = {}
  chinese: dict[str, str] = {}
  for raw, language, target in ((english_raw, "eng", english), (chinese_raw, "cmn", chinese)):
    for line in bz2.open(io.BytesIO(raw), "rt", encoding="utf-8", errors="replace"):
      parts: list[str] = line.rstrip("\n").split("\t", 2)
      if len(parts) != 3 or parts[1] != language:
        continue
      sentence: str = parts[2].strip()
      if 35 <= len(sentence) <= 220:
        target[parts[0]] = sentence
  items: list[NormalizedItem] = []
  limit: int = int(source.get("limit", 5000))
  with tarfile.open(fileobj=io.BytesIO(links_raw), mode="r:bz2") as archive:
    member = archive.getmember("links.csv")
    handle = archive.extractfile(member)
    if handle is None:
      return items
    lines = io.TextIOWrapper(handle, encoding="utf-8", errors="replace")
    for line in lines:
      pair: list[str] = line.rstrip("\n").split("\t")
      if len(pair) != 2:
        continue
      english_id, chinese_id = pair
      if english_id not in english or chinese_id not in chinese:
        continue
      items.append({
        "id": f"{source['id']}:{english_id}:{chinese_id}",
        "subject": "english",
        "module": "bilingual_sentence",
        "title": english[english_id][:80],
        "text": english[english_id],
        "translation": chinese[chinese_id],
        "sourceId": source["id"],
        "sourceUrl": source["homepage"],
        "license": source["license"],
        "tags": ["中英句对", "例句", "待高中分级"],
        "metadata": {"englishSentenceId": english_id, "chineseSentenceId": chinese_id}
      })
      if len(items) >= limit:
        break
  return items
