import re
from utilities import main as utilities
from sudachipy import dictionary, tokenizer
from general.const import *
from db_models import models, db_objects
from nlp import sentence_rating_system as srs
from nlp import models as nlp_models
from general.exceptions import UnexpectedExit
import files_utilities.custom_file_objects as cfo
import psycopg
from typing import List, Set

from general import _logging
from loguru import logger


def sudachi_tagger():
    return dictionary.Dictionary(dict="full").create()


def sudachi_mode():
    return tokenizer.Tokenizer.SplitMode.C


class JapaneseNlpE():
    def kana_check(self, sentence) -> bool:
        a = re.search(KANA_REGEX, sentence)

        if a is None:
            return False
        else:
            return True

    def ignore_filter_exp(self, sentence: str) -> str:
        return utilities.mass_replace(sentence, IGNORE_EXPRESSIONS)

    def kana_remove(self, sentence: str) -> str:
        '''leaving whitespace before word'''
        return utilities.mass_replace(sentence, [item for item in re.findall(KANA_REGEX, sentence)])

    def is_japanese(self, sentence: str) -> bool:
        a = re.search(JP_REGEX, sentence)

        if a is None:
            return False

        return True

    def prepare_for_translation(self, sentence: str) -> str:
        kana_check = self.kana_check(sentence)

        if kana_check == True:
            sentence = self.kana_remove(sentence)

        return utilities.mass_replace(
            self.ignore_filter_exp(sentence), WHITE_SPACES)

    def produce_pos_hash(self, data) -> str:
        filtered = [item for item in data if item != "*"]
        filtered.sort()
        to_hash = "".join(filtered)

        return utilities.generate_hash(to_hash, 10)

    def katakana_hiragana_only(self, sentence) -> bool:
        a = utilities.mass_replace(
            sentence, [item for item in re.findall(KATAKANA_HIRAGANA, sentence)])

        if len(a) == 0:
            return True

        return False

    def filter_empty_lines(self, inpt: List[str]) -> List[str]:
        a = []

        for item in inpt:
            checker1 = len(item) > 1
            checker2 = item not in EMPTY_LINE
            if checker1 and checker2:
                a.append(item)

        return a

    def replace_thrash_chars(self, data: List[str]) -> List[str]:
        return [utilities.mass_replace(item, THRASH_CHARS) for item in data]

    def extract_sentences(self, data: List[str]) -> List[str]:
        sentences = []

        for line in data:
            pattern1 = re.match(JP_SENTENCES_SPLITTER_PATTERN, line)
            if pattern1 != None:
                sentences.append(pattern1[1])

        return sentences


class JapaneseNlp(JapaneseNlpE):
    def __init__(self, tagger, mode) -> None:
        if tagger == True:
            self.tagger = sudachi_tagger()
        else:
            self.tagger = tagger

        if mode == True:
            self.mode = sudachi_mode()
        else:
            self.mode = mode

    def morphs_lenght(self, sentence_normalised: dict) -> int:
        '''2:Bad lenght: Too short,3:Bad lenght: Too long'''
        jp_config = utilities.config_reader()["jp_config"]
        tokens = sentence_normalised["tokens"]
        minimal_morphs = jp_config["minimal_morphs"]
        max_morphs = jp_config["max_morphs"]
        morphs_count = len(tokens)

        if morphs_count <= minimal_morphs:
            return 2
        elif morphs_count > max_morphs:
            return 3
        else:
            raise AttributeError

    def pos_hash_from_word(self, word: str) -> str:
        extraction = self.tokenize_and_normalize(word, [], [], [])
        tokens_ln = extraction.all_tokens_count

        if tokens_ln != 1:
            msg = " ".join(
                ["number of words not equal 1, equal:", str(tokens_ln)])
            logger.warning(msg)
            logger.trace([str(item.word) for item in extraction.all_tokens])

            return None

        return extraction.all_tokens[0].part_of_speech_hash

    def tokenize_and_normalize(self, sentence: str, pos_blacklist: List[str], ignore_list: List[str], on_hold_list: List[str]) -> nlp_models.TokenizedNormalizedSentence:
        kanaq = self.kana_check(sentence)
        if kanaq is True:
            sentence = self.kana_remove(sentence)

        sentence = self.ignore_filter_exp(sentence)

        if self.is_japanese(sentence) == False:
            return nlp_models.TokenizedNormalizedSentence(sentence=sentence)

        ignored = []
        words_pos_blacklisted = []
        on_hold = []
        not_passed = []
        tokens_passed = []

        all_tokens = []

        for word in self.tagger.tokenize(sentence, self.mode):
            word_model_obj = nlp_models.JpNlpWordModel(
                part_of_speech_hash=self.produce_pos_hash(word.part_of_speech()), normalised_form=word.normalized_form(), word=word.surface(),
                part_of_speech=word.part_of_speech(), dictionary_form=word.dictionary_form(), is_oov=word.is_oov(), reading_form=word.reading_form())

            checker_ignore_list = word_model_obj.normalised_form in ignore_list
            if checker_ignore_list:
                ignored.append(word_model_obj)
                continue

            checker_pos_blacklist = word_model_obj.part_of_speech_hash in pos_blacklist
            if checker_pos_blacklist:
                words_pos_blacklisted.append(word_model_obj)
                continue

            checker_on_hold = word_model_obj.normalised_form in on_hold_list
            if checker_on_hold:
                on_hold.append(word_model_obj)
                continue

            checker_lenght = not len(word_model_obj.normalised_form) <= 10
            checker_japanese = not self.is_japanese(word_model_obj.word)
            checker_final = checker_lenght or checker_japanese
            if checker_final:
                not_passed.append(word_model_obj)
                continue

            tokens_passed.append(word_model_obj)

        all_tokens += tokens_passed
        all_tokens += ignored
        all_tokens += words_pos_blacklisted
        all_tokens += not_passed
        all_tokens += on_hold

        return nlp_models.TokenizedNormalizedSentence(sentence=sentence, tokens_passed=tokens_passed, all_tokens_count=len(all_tokens),
                                                      ignored=ignored, pos_blacklisted=words_pos_blacklisted, not_passed=not_passed,
                                                      on_hold=on_hold, all_tokens=all_tokens)

    def count_morphs(self, sentence: str) -> int:
        return len(list(self.tagger.tokenize(sentence, self.mode)))


class JapaneseRecalc:
    def __init__(self, record: models.PreprocessingModel, knw: List[str], config: dict, srs_product_obj: srs.SentenceRatingSystemProduct, on_hold_words: List[str]) -> None:
        self.record = record
        self.knw = knw
        self.srs_product_obj = srs_product_obj
        self.bonus_rating_sum_a = record.bonus_rating_sum_a
        self.on_hold_words = on_hold_words

        zmienne = config
        self.config = zmienne["jp_config"]

    def _contain_on_hold_word(self, words: List[str]) -> bool:
        '''6:Word on hold'''
        for item in words:
            if item in self.on_hold_words:
                return True

        return False

    def _sentence_lenght(self) -> int:
        '''2:Bad lenght: Too short,3:Bad lenght: Too long'''
        max_morphs = self.config["max_morphs"]
        min_morphs = self.config["minimal_morphs"]
        morphs_count = self.record.words_number

        if morphs_count <= min_morphs:
            return 2
        elif morphs_count > max_morphs:
            return 3
        else:
            return None

    def _known_check(self) -> List[str]:
        '''4:All morphs known'''
        words = self.record.all_words
        unk_wor = [word for word in words if word not in self.knw]

        return unk_wor

    def execute(self) -> models.RecalcModel:
        '''5:Sentence passed,1:Too many unknown'''
        lenght = self._sentence_lenght()

        if lenght is not None:
            return models.RecalcModel(card_id=self.record.related_card, result=lenght, rating=0)

        if self._contain_on_hold_word(self.record.all_words):
            return models.RecalcModel(card_id=self.record.related_card, result=6, rating=0)

        after_known = self._known_check()

        if len(after_known) == 0:
            return models.RecalcModel(card_id=self.record.related_card, result=4, rating=0)
        elif len(after_known) == 1:
            rating = srs.proxy_function(
                self.srs_product_obj, after_known[0], self.bonus_rating_sum_a)

            return models.RecalcModel(card_id=self.record.related_card, result=5, unknown_word=after_known[0], rating=rating)
        else:
            return models.RecalcModel(card_id=self.record.related_card, result=1, rating=0)


class JpPosBlacklister:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        self.tagger = JapaneseNlp(True, True)
        self.words_ignore_obj = db_objects.WordsIgnore("jp", pg_con)
        self.blacklist_obj = db_objects.JpPosBlacklist(self.pg_con)

    def _get_random_sentences(self) -> List[str]:
        a = db_objects.CardsDb(self.pg_con).random_sentences(25000)

        return [item.sentence for item in a]

    def __truncate_both(self):
        db_objects.RecalcDb(self.pg_con).clear_all()
        db_objects.PreprocessingDb(self.pg_con).clear_all()

    def _simulation(self, pos_hash: str) -> Set[str]:
        banned = set()
        random_sentences = self._get_random_sentences()

        for item in random_sentences:
            if len(banned) == 51:
                break

            a = self.tagger.tokenize_and_normalize(
                item, [pos_hash], [], [])
            if len(a.pos_blacklisted) != 0:
                for item2 in a.pos_blacklisted:
                    banned.add(item2.normalised_form)

        return banned

    def execute(self, data, typee: int) -> bool:
        '''typee: 0: word, 1: pos, 2: pos_hash'''
        match typee:
            case 0:
                pos_hash = self.tagger.pos_hash_from_word(data)

                if pos_hash == None:
                    print("unable to get pos, you can only add word to words ignore")
                    only_add = input(f"{data} - add to words ignore? y/n?: ")

                    match only_add:
                        case "y":
                            action1 = "2"
                        case "n":
                            action1 = "3"
                        case _:
                            raise UnexpectedExit()
                else:
                    logger.info("effects simulation start")
                    simulation_result = self._simulation(pos_hash)

                    print(f"word: {data}")
                    print("if this pos is blacklisted, these words will be ignored:")
                    print(simulation_result)

                    action1 = input(
                        "\naction? 1:ban pos, 2:add to skip words - ")

                match action1:
                    case "1":
                        self.blacklist_obj.add(pos_hash).save()
                        self.__truncate_both()

                        return True
                    case "2":
                        self.words_ignore_obj.add(data).save()
                        self.__truncate_both()

                        return True
                    case _:
                        raise UnexpectedExit()
            case 1:
                raise NotImplementedError()
            case 2:
                raise NotImplementedError()
            case _:
                raise UnexpectedExit()

    def test_current_blacklist(self) -> None:
        raise NotImplementedError
        # blacklist_obj = db_objects.JpPosBlacklist(self.pg_con)

        # new_list = blacklist_obj.content
        # current_ln = len(blacklist_obj.content)

        # for num, item in enumerate(blacklist_obj.content):
        #     print("-----------------------------------")
        #     print("".join([str(num + 1), "/", str(current_ln)]))
        #     print(f"POS: {item}")
        #     print("simulation:")
        #     print(self._simulation(item))
        #     action = input(
        #         "\naction? 1:remove from blacklist, 2:break, any:nothing - ")

        #     match action:
        #         case "1":
        #             new_list.remove(item)
        #         case "2":
        #             break
        #         case _:
        #             pass

        # blacklist_content_len = len(blacklist_obj.content)
        # new_list_len = len(new_list)

        # if blacklist_content_len != new_list_len:
        #     remove_len = blacklist_content_len - new_list_len
        #     difference = [
        #         item for item in blacklist_obj.content if item not in new_list]

        #     logger.info(f"removing {remove_len}")
        #     logger.trace(difference)

        #     blacklist_obj.content = new_list
        #     blacklist_obj.save()


class NovelTextProcessing:
    def __init__(self, source: cfo.TextFile | List[str]) -> None:
        self.source = source
        self.nlp = JapaneseNlp(True, True)
        jp_config = utilities.config_reader()["jp_config"]

        self.sentence_max_lenght = jp_config["max_morphs"]
        self.sentence_min_lenght = jp_config["minimal_morphs"]

    def __too_long(self, n: int) -> bool:
        return n >= self.sentence_max_lenght

    def __too_short(self, n: int) -> bool:
        return n <= self.sentence_min_lenght

    def __find_neighbours(self, n: int) -> List[int]:
        return [item for item in range(n+1, n+7)]

    def __rebuild_sentences_storage(self, now_processed: List[nlp_models.NovelTextProcessingSentence]):
        new_sentences_processed = []
        for num, item in enumerate(now_processed):
            a: nlp_models.NovelTextProcessingSentence = item
            a.line_number = num + 1

            new_sentences_processed.append(a)

        self.sentences = new_sentences_processed
        self.sentences_indexed = {
            item.line_number: item for item in new_sentences_processed}

    def __split_long(self):
        sentences_processed = []

        current_line = 1
        while current_line < len(self.sentences) + 1:
            sentence = self.sentences_indexed[current_line]

            if self.__too_long(sentence.lenght):
                replaced = sentence.sentence.replace(r"。", r"。‽")
                broken = [item for item in replaced.split(
                    r"‽") if len(item) != 0]

                if len(broken) == 1:
                    sentences_processed.append(sentence)
                    current_line += 1
                    continue
                else:
                    for item in broken:
                        new_obj = nlp_models.NovelTextProcessingSentence(
                            sentence=item, line_number=0, lenght=self.nlp.count_morphs(item))
                        sentences_processed.append(new_obj)

                    current_line += 1
                    continue

            sentences_processed.append(sentence)
            current_line += 1
            continue

        self.__rebuild_sentences_storage(sentences_processed)

    def __join_short(self):
        sentences_processed = []
        all_sentences_len = len(self.sentences)

        current_line = 1
        while current_line < all_sentences_len + 1:
            sentence = self.sentences_indexed[current_line]

            if self.__too_short(sentence.lenght):
                next_sentences = [self.sentences_indexed[item]
                                  for item in self.__find_neighbours(sentence.line_number) if item <= all_sentences_len]
                line_number = sentence.line_number
                new_lenght = sentence.lenght
                new_sentence = sentence.sentence
                skip_to = None

                for item in next_sentences:
                    temp_lenght = new_lenght + item.lenght

                    if self.__too_long(temp_lenght):
                        break

                    new_lenght += item.lenght
                    new_sentence = " ".join([new_sentence, item.sentence])
                    skip_to = item.line_number + 1

                if skip_to == None:
                    sentences_processed.append(sentence)
                    current_line += 1
                    continue
                else:
                    new_obj = nlp_models.NovelTextProcessingSentence(
                        sentence=new_sentence, line_number=line_number, lenght=new_lenght)
                    sentences_processed.append(new_obj)
                    current_line = skip_to
                    continue

            sentences_processed.append(sentence)
            current_line += 1
            continue

        self.__rebuild_sentences_storage(sentences_processed)

    def __prepare_sentences(self):
        to_do = [self.nlp.extract_sentences,
                 self.nlp.replace_thrash_chars, self.nlp.filter_empty_lines]
        current = self.get_lines()

        for func in to_do:
            a = func(current)
            current = a

        self.sentences = [nlp_models.NovelTextProcessingSentence(
            sentence=item, line_number=num + 1, lenght=self.nlp.count_morphs(item)) for num, item in enumerate(current)]
        self.sentences_indexed = {
            item.line_number: item for item in self.sentences}

    def get_lines(self) -> List[str]:
        if isinstance(self.source, cfo.TextFile):
            a = self.source.give_lines()
        elif isinstance(self.source, list):
            a = self.source
        else:
            raise TypeError(type(self.source))

        return a

    def main(self) -> List[nlp_models.NovelTextProcessingSentence]:
        self.__prepare_sentences()
        self.__split_long()
        self.__join_short()

        return self.sentences


if __name__ == "__main__":
    pass
