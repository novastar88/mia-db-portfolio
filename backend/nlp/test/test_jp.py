import unittest
import nlp.jp as jp
from db_models import dbs_con


class TestStandalone(unittest.TestCase):
    def test_sudachi_tagger(self):
        jp.sudachi_tagger()

    def test_sudachi_mode(self):
        jp.sudachi_mode()


class TestJapaneseNlpE(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = jp.JapaneseNlpE()

    def test_kana_check(self):
        self.assertTrue(self.obj.kana_check("事[こと]"))
        self.assertFalse(self.obj.kana_check("こと"))
        self.assertFalse(self.obj.kana_check("事"))
        self.assertFalse(self.obj.kana_check(
            "岸嶺は三歳の頃から絵本の楽しさに夢中になり、「ご本読んで、ご本読んでー」と両親にせがみ続けた。"))
        self.assertTrue(self.obj.kana_check(
            "岸嶺は三歳の頃から 絵本[えほん]の楽しさに夢中になり、「ご本読んで、ご本読んでー」と両親にせがみ続けた。"))

    def test_ignore_filter_exp(self):
        a = "岸嶺は、子供ながらにそのことに気付いた。"
        self.assertIsInstance(self.obj.ignore_filter_exp(a), str)
        self.assertEqual(a, self.obj.ignore_filter_exp(a))

        b = "岸嶺は、子供ながらにそのことに気付いた。&ensp;"
        self.assertEqual(a, self.obj.ignore_filter_exp(b))

        c = "　岸嶺は、子供ながらにそのことに気付いた。</div>"
        self.assertEqual(a, self.obj.ignore_filter_exp(c))

    def test_kana_remove(self):
        a = "岸嶺は三歳の頃から 絵本[えほん]の楽しさに夢中になり、「ご本読んで、ご本読んでー」と両親にせがみ続けた。"
        b = "岸嶺は三歳の頃から 絵本[えほん]の 楽[たの]しさに夢中になり、「ご本読んで、ご本読んでー」と両親にせがみ続けた。"

        self.assertEqual(
            "岸嶺は三歳の頃から 絵本の楽しさに夢中になり、「ご本読んで、ご本読んでー」と両親にせがみ続けた。", self.obj.kana_remove(a))
        self.assertEqual(
            "岸嶺は三歳の頃から 絵本の 楽しさに夢中になり、「ご本読んで、ご本読んでー」と両親にせがみ続けた。", self.obj.kana_remove(b))

    @unittest.skip("not implemented")
    def test_is_japanese(self):
        ...

    @unittest.skip("not implemented")
    def test_prepare_for_translation(self):
        ...

    @unittest.skip("not implemented")
    def test_produce_pos_hash(self):
        ...

    @unittest.skip("not implemented")
    def test_katakana_hiragana_only(self):
        ...

    def test_filter_empty_lines(self):
        a = "岸嶺は、子供ながらにそのことに気付いた。"
        empty = ["\n", "　", " ", "。", a]

        self.assertSequenceEqual(self.obj.filter_empty_lines(empty), [a])

    @unittest.skip("not implemented")
    def test_replace_thrash_chars(self):
        ...

    @unittest.skip("not implemented")
    def test_extract_sentences(self):
        ...


class TestJapaneseNlp(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = jp.JapaneseNlp(True, True)

    @unittest.skip("not implemented")
    def test_morphs_lenght(self):
        ...

    @unittest.skip("not implemented")
    def test_pos_hash_from_word(self):
        ...

    @unittest.skip("not implemented")
    def test_tokenize_and_normalize(self):
        ...

    @unittest.skip("not implemented")
    def test_count_morphs(self):
        ...


class TestJapaneseRecalc(unittest.TestCase):
    @unittest.skip("not implemented")
    def test_contain_on_hold_word(self):
        ...

    @unittest.skip("not implemented")
    def test_sentence_lenght(self):
        ...

    @unittest.skip("not implemented")
    def test_known_check(self):
        ...

    @unittest.skip("not implemented")
    def test_execute_lenght(self):
        ...

    @unittest.skip("not implemented")
    def test_execute_6(self):
        ...

    @unittest.skip("not implemented")
    def test_execute_4(self):
        ...

    @unittest.skip("not implemented")
    def test_execute_5(self):
        ...

    @unittest.skip("not implemented")
    def test_execute_1(self):
        ...


class TestJpPosBlacklister(unittest.TestCase):
    def setUp(self) -> None:
        self.con = dbs_con.postgres_con()
        self.obj = ...

    def tearDown(self) -> None:
        self.con.cancel()
        self.con.close()

    @unittest.skip("not implemented")
    def test_test_current_blacklist(self):
        ...

    @unittest.skip("not implemented")
    def test_execute_0(self):
        ...

    @unittest.skip("not implemented")
    def test_execute_1(self):
        ...

    @unittest.skip("not implemented")
    def test_execute_2(self):
        ...


class TestNovelTextProcessing(unittest.TestCase):
    @unittest.skip("not implemented")
    def test_source_list(self):
        ...

    @unittest.skip("not implemented")
    def test_source_text_file(self):
        ...

    @unittest.skip("not implemented")
    def test_get_lines(self):
        ...

    @unittest.skip("not implemented")
    def test_main(self):
        ...


if __name__ == "__main__":
    unittest.main()
