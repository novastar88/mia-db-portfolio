import nlp.deepl_translator as deepltranslator
import unittest

# from general import _logging
# from loguru import logger


class TestDeepL(unittest.TestCase):
    def setUp(self) -> None:
        self.client = deepltranslator.Translator("JA", "PL")

    def test_translate_sentence(self):
        to_translate = r"すなわち、廃はい墟きよ──と。"
        translated = self.client.translate_sentence(to_translate)
        self.assertIsInstance(translated, str)
        self.assertGreater(len(translated), 3)


if __name__ == "__main__":
    unittest.main()
