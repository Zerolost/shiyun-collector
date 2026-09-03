from typing import Any, Literal, TypedDict

Subject = Literal["chinese", "english"]


class NormalizedItem(TypedDict, total=False):
  id: str
  subject: Subject
  module: str
  title: str
  text: str
  translation: str
  author: str
  sourceId: str
  sourceUrl: str
  license: str
  tags: list[str]
  metadata: dict[str, Any]


class SourceResult(TypedDict):
  source: dict[str, Any]
  items: list[NormalizedItem]
  rawSha256: str
  retrievedAt: str
