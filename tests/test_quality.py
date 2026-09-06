import unittest

from crawler.quality import filter_quality, is_usable_vocabulary_title


class QualityTests(unittest.TestCase):
  def test_rejects_dictionary_fragments(self) -> None:
    self.assertFalse(is_usable_vocabulary_title("-able"))
    self.assertFalse(is_usable_vocabulary_title("'tween"))
    self.assertFalse(is_usable_vocabulary_title("'s Gravenhage"))
    self.assertTrue(is_usable_vocabulary_title("language"))

  def test_removes_unreviewed_wikipedia_essay_items(self) -> None:
    items: list[dict[str, object]] = [{
      "id": "wiki:1",
      "subject": "chinese",
      "module": "essay_material",
      "title": "永州话",
      "text": "这是一段百科介绍文本，长度足够但不应直接作为作文素材使用。" * 8,
      "sourceId": "zh-wikipedia-current",
      "tags": ["作文素材"]
    }]
    self.assertEqual(filter_quality(items), [])

  def test_unknown_stage_is_general(self) -> None:
    items: list[dict[str, object]] = [{
      "id": "quote:1",
      "subject": "chinese",
      "module": "famous_quote",
      "title": "测试名言",
      "text": "文本",
      "metadata": {"learningStage": "高一上"}
    }]
    result: list[dict[str, object]] = filter_quality(items)
    self.assertEqual(result[0]["metadata"], {"learningStage": "high-school-general"})

  def test_simplifies_nested_text(self) -> None:
    item: dict[str, object] = {
      "module": "classical_text",
      "title": "讀襌經",
      "metadata": {"author": "杜甫"},
      "tags": ["繁體"],
    }
    result: list[dict[str, object]] = filter_quality([item])
    self.assertEqual(result[0]["title"], "读禅经")
    self.assertEqual(result[0]["tags"], ["繁体"])


if __name__ == "__main__":
  unittest.main()
