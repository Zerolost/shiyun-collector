import hashlib
import xml.etree.ElementTree as ET
from typing import Any

from models import NormalizedItem


def parse(payload: bytes, source: dict[str, Any]) -> list[NormalizedItem]:
  root = ET.fromstring(payload)
  items: list[NormalizedItem] = []
  for node in root.findall(".//item")[: int(source.get("limit", 100))]:
    title: str = (node.findtext("title") or "").strip()
    link: str = (node.findtext("link") or source["homepage"]).strip()
    description: str = (node.findtext("description") or "").strip()
    if not title:
      continue
    stable: str = hashlib.sha256(link.encode()).hexdigest()[:20]
    items.append({
      "id": f"{source['id']}:{stable}",
      "subject": source["subject"],
      "module": source["module"],
      "title": title,
      "text": description,
      "sourceId": source["id"],
      "sourceUrl": link,
      "license": source["license"],
      "tags": source.get("tags", []),
      "metadata": {}
    })
  return items
