import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
import nlp.sentence_rating_system as srs

mock_priority_words = MagicMock(spec=["get_list", "words"])
mock_priority_words.words = ["test", "test2"]


class SentenceRatingSystemProducer(unittest.TestCase):
    @unittest.skip("not implemented")
    def test_case_0(self):
        fake_config = {"jp_config": {"sentence_rating_mode": 0}}

    @patch("db_models.db_objects.PriorityWordsDb", mock_priority_words)
    def test_case_1(self):
        fake_config = {"jp_config": {
            "used_priority_list": 1, "sentence_rating_mode": 1}}

        a = srs.sentence_rating_system_producer(fake_config, None)
        self.assertSequenceEqual(a.used_list, ["test", "test2"])
        self.assertEqual(a.used_list_len, 2)

    @unittest.skip("not implemented")
    def test_case_2(self):
        fake_config = {"jp_config": {
            "used_frequency_list": 1, "sentence_rating_mode": 2}}


class TestStandalone(unittest.TestCase):
    @unittest.skip("not implemented")
    def test_proxy_function(self):
        ...


if __name__ == "__main__":
    unittest.main()
