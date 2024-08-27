import psycopg
from db_models import models
from general import checkers
from general import exceptions as exc
from utilities import main as utilities
import json
from collections import Counter
from typing import List
import procedures.preprocessing as proced_pre
import procedures.recalc as proced_rec
from itertools import chain
import db_models.interfaces as interfaces
import os
from datetime import datetime
from general import const

from general import _logging
from loguru import logger


def sentences_to_process(pg_con: 'psycopg.Connection') -> int:
    recalc = RecalcDb(pg_con).not_processed()
    preprocessing = PreprocessingDb(pg_con).not_processed()

    return recalc + preprocessing


class PreprocessingDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    # def is_preprocessed(self, card_id: int):
    #     self.cur.execute(
    #         '''SELECT id FROM preprocessing WHERE related_card=%s''', (card_id,))
    #     a = self.cur.fetchone()

    #     if a == None:
    #         return False
    #     else:
    #         return a[0]

    # def card_changed(self, card_id: int):
    #     self.cur.execute(
    #         '''DELETE FROM preprocessing WHERE related_card=%s RETURNING id''', (card_id,))
    #     a = self.cur.fetchone()

    #     if a != None:
    #         self.pg_con.commit()
    #     else:
    #         raise Exception(f"deletion error: {a}")

    # def insert_one(self, record: models.PreprocessingModel):
    #     self.cur.execute('''INSERT INTO preprocessing(all_words,related_card) VALUES(%s,%s)''',
    #                      [record.all_words, record.related_card])
    #     self.pg_con.commit()

    def insert_many(self, records_list: list):
        query_params = []
        records_len = len(records_list)

        if records_len != 0:
            for item in records_list:
                if isinstance(item, models.PreprocessingModel):
                    query_params.append(
                        [item.all_words, item.related_card, item.bonus_rating_sum_a, item.words_number])
                else:
                    print(type(item))
                    raise AttributeError

            statement = '''INSERT INTO preprocessing(all_words,related_card,bonus_rating_sum_a,words_number) VALUES(%s,%s,%s,%s)'''
            self.cur.executemany(statement, query_params)
        else:
            logger.warning("empty insertion!")

    def clear_all(self):
        self.cur.execute('''TRUNCATE TABLE preprocessing''')

    def not_processed(self) -> int:
        self.cur.execute('''SELECT COUNT(id) FROM preprocessing_view''')

        return self.cur.fetchone()[0]

    def checked_view__fetch(self, number: int) -> List[models.PreprocessingModel]:
        self.cur.execute(
            f'''SELECT all_words,related_card,words_number,bonus_rating_sum_a FROM checked_view LIMIT {number}''')

        return [models.PreprocessingModel(
            all_words=item[0], related_card=item[1], words_number=item[2], bonus_rating_sum_a=item[3]) for item in self.cur.fetchall()]


class RecalcDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def insert_many(self, records_list: list):
        query_params = []
        records_len = len(records_list)

        if records_len != 0:
            for item in records_list:
                if isinstance(item, models.RecalcModel):
                    query_params.append(
                        [item.result, item.unknown_word, item.card_id, item.rating])
                else:
                    raise TypeError(type(item))

            statement = '''INSERT INTO recalc(result,unknown_word,card_id,rating) VALUES(%s,%s,%s,%s)'''
            self.cur.executemany(statement, query_params)
        else:
            logger.warning("empty insertion!")

    def clear_all(self):
        self.cur.execute('''TRUNCATE TABLE recalc''')

    def not_processed(self) -> int:
        self.cur.execute(
            '''SELECT COUNT(cards.id) FROM cards LEFT JOIN recalc ON cards.id=recalc.card_id WHERE recalc.card_id IS NULL''')
        return self.cur.fetchone()[0]


class CardsDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def insert_many(self, records_list: list):
        query_params = []

        if len(records_list) != 0:
            for item in records_list:
                if isinstance(item, models.CardModel):
                    item.tags = [item2[:100] for item2 in item.tags]
                    query_params.append([item.deck, item.tags, item.note_type, item.sentence,
                                         item.audio, item.screen, item.meaning, item.line_number, item.ai_interpretation])
                else:
                    print(type(item))
                    raise AttributeError

            statement = '''INSERT INTO cards(deck,tags,note_type,sentence,audio,screen,meaning,line_number,ai_interpretation) 
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            self.cur.executemany(statement, query_params)
        else:
            logger.warning("empty insertion!")

    def random_sentences(self, n: int):
        self.cur.execute(
            f'''SELECT id,deck,creation_time,tags,note_type,sentence,audio,screen,meaning,updated_time,line_number,ai_interpretation
            FROM cards ORDER BY RANDOM() LIMIT {str(n)}''')

        return [models.CardModel(idd=item[0], deck=item[1], creation_time=item[2], tags=item[3], note_type=item[4], sentence=item[5],
                                 audio=item[6], screen=item[7], meaning=item[8], updated_time=item[9], ai_interpretation=item[10]) for item in self.cur.fetchall()]

    def preprocessing_view__fetch(self, number: int) -> list:
        self.cur.execute(
            f'''SELECT sentence,id,bonus_rating_note FROM preprocessing_view LIMIT {number}''')

        return [[models.CardModel(
            idd=item[1], sentence=item[0]), models.NoteTypeModel(bonus_rating_note=item[2])] for item in self.cur.fetchall()]

    def get_last_line_number(self, deck: str) -> int:
        if deck is None:
            return None

        self.cur.execute(
            '''SELECT line_number FROM public.cards WHERE deck=%s ORDER BY line_number DESC LIMIT 1''', [deck])
        card = self.cur.fetchone()

        if card != None:
            line_num = card[0]

            if line_num != None:
                return card[0]

            self.cur.execute(
                '''SELECT COUNT(id) FROM public.cards WHERE deck=%s''', [deck])
            all_count = self.cur.fetchone()[0]

            return all_count

        return 0

    def get_card_neighbours(self, middle_card: models.CardModel, depth: int) -> dict:
        # check if line_numbers_working
        if middle_card.deck is None or middle_card.line_number is None:
            return None

        a = self.get_last_line_number(middle_card.deck)
        if a is None or a == 0:
            return None

        begining = []
        ending = []

        neighbours = utilities.find_sentence_context_neighbours(
            middle_card.line_number, depth)
        n_begining = neighbours["start"]
        n_ending = neighbours["end"]

        for sentence1 in n_begining:
            self.cur.execute(
                '''SELECT id,deck,creation_time,tags,note_type,sentence,audio,screen,meaning,updated_time,line_number,ai_interpretation
                FROM cards WHERE deck=%s AND line_number=%s''', [middle_card.deck, sentence1])
            fetched = self.cur.fetchone()

            if fetched != None:
                begining.append(models.CardModel(idd=fetched[0], deck=fetched[1], creation_time=fetched[2], tags=fetched[3], note_type=fetched[4], sentence=fetched[5],
                                                 audio=fetched[6], screen=fetched[7], meaning=fetched[8], updated_time=fetched[9], ai_interpretation=fetched[10]))

        for sentence2 in n_ending:
            self.cur.execute(
                '''SELECT id,deck,creation_time,tags,note_type,sentence,audio,screen,meaning,updated_time,line_number,ai_interpretation
                FROM cards WHERE deck=%s AND line_number=%s''', [middle_card.deck, sentence2])
            fetched = self.cur.fetchone()

            if fetched != None:
                ending.append(models.CardModel(idd=fetched[0], deck=fetched[1], creation_time=fetched[2], tags=fetched[3], note_type=fetched[4], sentence=fetched[5],
                                               audio=fetched[6], screen=fetched[7], meaning=fetched[8], updated_time=fetched[9], ai_interpretation=fetched[10]))

        return dict(start=begining, middle=middle_card, end=ending)


class AnkiStatusDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def add_as_exported(self, card: models.CardModel | list):
        statement = '''INSERT INTO anki_status(statuss,card_id) VALUES(%s,%s)'''
        if isinstance(card, models.CardModel):
            self.cur.execute(statement, (1, card.idd,))
        elif isinstance(card, list):
            query_params = [[1, item.idd] for item in card]
            self.cur.executemany(statement, query_params)
        else:
            raise AttributeError

    def status1_words(self) -> List[str]:
        master_array = []
        self.cur.execute('''SELECT unknown_word FROM status1_words''')

        for item in self.cur.fetchall():
            arr = item[0]
            if arr != None:
                master_array += arr

        master_array = set(master_array)
        master_array = list(master_array)

        return master_array

    def delete_by_related_card_id(self, card_id: int):
        self.cur.execute(
            '''DELETE FROM anki_status WHERE card_id=%s''', [card_id])

    def update_handled(self, card_id: int, status: int):
        self.cur.execute(
            '''UPDATE anki_status SET handled=%s, statuss=%s WHERE card_id=%s''', [True, status, card_id])


class NoteTypeDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()


class PriorityWordsDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def add_to_db(self, obj: models.PriorityWordsListModel):
        statement = '''INSERT INTO priority_words_lists(namee,lang,words) VALUES(%s,%s,%s)'''
        self.cur.execute(statement, [obj.name, obj.lang, obj.words])

    def get_all_for_lang(self, lang: str) -> list:
        statement = '''SELECT words FROM priority_words_lists WHERE lang=%s'''
        self.cur.execute(statement, [lang])
        a = self.cur.fetchall()

        return [models.PriorityWordsListModel(words=item[0]) for item in a]

    def get_list(self, name: str) -> models.PriorityWordsListModel:
        statement = '''SELECT id,namee,lang,words,updated_time,creation_time FROM priority_words_lists WHERE namee=%s'''
        self.cur.execute(statement, [name])
        a = self.cur.fetchone()

        return models.PriorityWordsListModel(id=a[0], name=a[1], lang=a[2], words=a[3], updated_time=a[4], creation_time=a[5])


class DecksDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def add_if_not_exists(self, name: str):
        statement = '''INSERT INTO decks(deck_name) VALUES(%s) ON CONFLICT DO NOTHING'''
        self.cur.execute(statement, [name])


class PriorityWordsSingle:
    def __init__(self, name: str, lang: str, pg_con: 'psycopg.Connection') -> None:
        self.name = name
        self.lang = lang
        self.content = []

        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        try:
            self._load()
        except exc.ObjectIsNone:
            self._create()

    def _load(self):
        self.cur.execute(
            '''SELECT words FROM priority_words_lists WHERE namee=%s''', [self.name])
        a = self.cur.fetchone()
        checkers.not_none(a)
        self.content = a[0]

    def save(self):
        self.cur.execute('''UPDATE priority_words_lists SET words=%s WHERE namee=%s''', [
                         self.content, self.name])

    def _create(self):
        self.cur.execute('''INSERT INTO priority_words_lists(namee,words,lang) VALUES(%s,%s,%s)''', [
                         self.name, self.content, self.lang])

    def update_many_unique(self, data: list | set):
        if isinstance(data, list):
            pass
        elif isinstance(data, set):
            data = list(data)
        else:
            raise TypeError

        self.content = list(set(self.content + data))

        self.save()


class JsonStorageCollection(interfaces.JsonStorage):
    def __init__(self, name: str, pg_con: 'psycopg.Connection') -> None:
        super().__init__(name, pg_con)
        if self.content == None:
            self.content = []

    def update_many_unique(self, data: list | set):
        if isinstance(data, list):
            pass
        elif isinstance(data, set):
            data = list(data)
        else:
            raise TypeError

        self.content = list(set(self.content + data))

        self.save()

    def save(self):
        if isinstance(self.content, list):
            super().save()
        else:
            raise Exception("wrong self.content type")

    def remove(self, data):
        if len(data) != 0:
            self.content = [item for item in self.content if item not in data]

        self.save()


class JpPosBlacklist:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        self.objects_list = []
        self.str_list = []

        self._load()

    def _load(self):
        self.pos_to_add = []
        self.pos_to_remove = []
        self.cur.execute(
            '''SELECT id,time_added,pos_hash FROM jp_pos_blacklist''')
        a = self.cur.fetchall()
        self.objects_list = [models.JpPosBlacklistModel(
            idd=item[0], time_added=item[1], pos_hash=item[2]) for item in a]
        self.str_list = [item[2] for item in a]

    def add(self, data):
        if isinstance(data, str):
            if data not in self.str_list:
                self.pos_to_add.append(data)
        elif isinstance(data, list):
            self.pos_to_add += [item for item in data if item not in self.str_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item not in self.str_list:
                    self.pos_to_add.append(item)
        else:
            raise AttributeError

        return self

    def remove(self, data):
        if isinstance(data, str):
            if data in self.str_list:
                self.pos_to_remove.append(data)
        elif isinstance(data, list):
            self.pos_to_remove += [item for item in data if item in self.str_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item in self.str_list:
                    self.pos_to_remove.append(item)
        else:
            raise AttributeError

        return self

    def save(self, reload: bool = True):
        statement = '''INSERT INTO jp_pos_blacklist(pos_hash) VALUES(%s) ON CONFLICT DO NOTHING'''
        query_params = [[item] for item in self.pos_to_add]
        if len(query_params) != 0:
            self.cur.executemany(statement, query_params)

        statement2 = '''DELETE FROM jp_pos_blacklist WHERE pos_hash=%s'''
        query_params2 = [[item] for item in self.pos_to_remove]
        if len(query_params2) != 0:
            self.cur.executemany(statement2, query_params2)

        self.pg_con.commit()

        if reload == True:
            self._load()

            return self


class KnownWords:
    def __init__(self, lang: str, pg_con: 'psycopg.Connection') -> None:
        self.lang = lang
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        self.objects_list = []
        self.words_list = []

        self._load()

    def _load(self):
        self.words_to_add = []
        self.words_to_remove = []
        self.cur.execute(
            '''SELECT id,word,time_known,lang FROM words_known WHERE lang=%s''', [self.lang])
        a = self.cur.fetchall()
        self.objects_list = [models.WordsKnown(
            idd=item[0], word=item[1], time_known=item[2], lang=item[3]) for item in a]
        self.words_list = [item[1] for item in a]

    def add(self, data):
        if isinstance(data, str):
            if data not in self.words_list:
                self.words_to_add.append(data)
        elif isinstance(data, list):
            self.words_to_add += [item for item in data if item not in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item not in self.words_list:
                    self.words_to_add.append(item)
        else:
            raise TypeError(type(data))

        return self

    def remove(self, data):
        if isinstance(data, str):
            if data in self.words_list:
                self.words_to_remove.append(data)
        elif isinstance(data, list):
            self.words_to_remove += [item for item in data if item in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item in self.words_list:
                    self.words_to_remove.append(item)
        else:
            raise TypeError

        return self

    def save(self, reload: bool = True):
        statement = '''INSERT INTO words_known(word, lang) VALUES(%s,%s) ON CONFLICT DO NOTHING'''
        query_params = [[item, self.lang] for item in self.words_to_add]
        if len(query_params) != 0:
            self.cur.executemany(statement, query_params)

        statement2 = '''DELETE FROM words_known WHERE word=%s AND lang=%s'''
        query_params2 = [[item, self.lang] for item in self.words_to_remove]
        if len(query_params2) != 0:
            self.cur.executemany(statement2, query_params2)

        if reload == True:
            self._load()

            return self


class WordsIgnore:
    def __init__(self, lang: str, pg_con: 'psycopg.Connection') -> None:
        self.lang = lang
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        self.objects_list = []
        self.words_list = []

        self._load()

    def _load(self):
        self.words_to_add = []
        self.words_to_remove = []
        self.cur.execute(
            '''SELECT id,lang,time_added,word FROM words_ignore WHERE lang=%s''', [self.lang])
        a = self.cur.fetchall()
        self.objects_list = [models.WordsIgnoreModel(
            idd=item[0], word=item[3], time_added=item[2], lang=item[1]) for item in a]
        self.words_list = [item.word for item in self.objects_list]

    def add(self, data):
        if isinstance(data, str):
            if data not in self.words_list:
                self.words_to_add.append(data)
        elif isinstance(data, list):
            self.words_to_add += [item for item in data if item not in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item not in self.words_list:
                    self.words_to_add.append(item)
        else:
            raise TypeError(type(data))

        return self

    def remove(self, data):
        if isinstance(data, str):
            if data in self.words_list:
                self.words_to_remove.append(data)
        elif isinstance(data, list):
            self.words_to_remove += [item for item in data if item in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item in self.words_list:
                    self.words_to_remove.append(item)
        else:
            raise TypeError

        return self

    def save(self, reload: bool = True):
        statement = '''INSERT INTO words_known(word, lang) VALUES(%s,%s) ON CONFLICT DO NOTHING'''
        query_params = [[item, self.lang] for item in self.words_to_add]
        if len(query_params) != 0:
            self.cur.executemany(statement, query_params)

        statement2 = '''DELETE FROM words_on_hold WHERE word=%s AND lang=%s'''
        query_params2 = [[item, self.lang] for item in self.words_to_remove]
        if len(query_params2) != 0:
            self.cur.executemany(statement2, query_params2)

        if reload == True:
            self._load()

            return self


class WordsIgnore:
    def __init__(self, lang: str, pg_con: 'psycopg.Connection') -> None:
        self.lang = lang
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        self.objects_list = []
        self.words_list = []

        self._load()

    def _load(self):
        self.words_to_add = []
        self.words_to_remove = []
        self.cur.execute(
            '''SELECT id,lang,time_added,word FROM words_ignore WHERE lang=%s''', [self.lang])
        a = self.cur.fetchall()
        self.objects_list = [models.WordsIgnoreModel(
            idd=item[0], word=item[3], time_added=item[2], lang=item[1]) for item in a]
        self.words_list = [item.word for item in self.objects_list]

    def add(self, data):
        if isinstance(data, str):
            if data not in self.words_list:
                self.words_to_add.append(data)
        elif isinstance(data, list):
            self.words_to_add += [item for item in data if item not in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item not in self.words_list:
                    self.words_to_add.append(item)
        else:
            raise AttributeError

        return self

    def remove(self, data):
        if isinstance(data, str):
            if data in self.words_list:
                self.words_to_remove.append(data)
        elif isinstance(data, list):
            self.words_to_remove += [item for item in data if item in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item in self.words_list:
                    self.words_to_remove.append(item)
        else:
            raise AttributeError

        return self

    def save(self, reload: bool = True):
        statement = '''INSERT INTO words_ignore(word, lang) VALUES(%s,%s) ON CONFLICT DO NOTHING'''
        query_params = [[item, self.lang] for item in self.words_to_add]
        if len(query_params) != 0:
            self.cur.executemany(statement, query_params)

        statement2 = '''DELETE FROM words_ignore WHERE word=%s AND lang=%s'''
        query_params2 = [[item, self.lang] for item in self.words_to_remove]
        if len(query_params2) != 0:
            self.cur.executemany(statement2, query_params2)

        if reload == True:
            self._load()

            return self


class WordsOnHold:
    def __init__(self, lang: str, pg_con: 'psycopg.Connection') -> None:
        self.lang = lang
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        self.objects_list = []
        self.words_list = []

        self._load()

    def _load(self):
        self.words_to_add = []
        self.words_to_remove = []
        self.cur.execute(
            '''SELECT id,lang,time_added,word FROM words_on_hold WHERE lang=%s''', [self.lang])
        a = self.cur.fetchall()
        self.objects_list = [models.WordsOnHoldModel(
            idd=item[0], word=item[3], time_added=item[2], lang=item[1]) for item in a]
        self.words_list = [item[3] for item in a]

    def add(self, data):
        if isinstance(data, str):
            if data not in self.words_list:
                self.words_to_add.append(data)
        elif isinstance(data, list):
            self.words_to_add += [item for item in data if item not in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item not in self.words_list:
                    self.words_to_add.append(item)
        else:
            raise AttributeError

        return self

    def remove(self, data):
        if isinstance(data, str):
            if data in self.words_list:
                self.words_to_remove.append(data)
        elif isinstance(data, list):
            self.words_to_remove += [item for item in data if item in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item in self.words_list:
                    self.words_to_remove.append(item)
        else:
            raise AttributeError

        return self

    def save(self, reload: bool = True):
        statement = '''INSERT INTO words_on_hold(word, lang) VALUES(%s,%s) ON CONFLICT DO NOTHING'''
        query_params = [[item, self.lang] for item in self.words_to_add]
        if len(query_params) != 0:
            self.cur.executemany(statement, query_params)

        statement2 = '''DELETE FROM words_on_hold WHERE word=%s AND lang=%s'''
        query_params2 = [[item, self.lang] for item in self.words_to_remove]
        if len(query_params2) != 0:
            self.cur.executemany(statement2, query_params2)

        if reload == True:
            self._load()

            return self


class FrequencyWordsLists:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def get_list(self, idd: int) -> models.FrequencyWordsListModel:
        self.cur.execute(
            '''SELECT id,namee,lang,updated_time,creation_time,words
            FROM frequency_words_lists WHERE id=%s''', [idd])
        a = self.cur.fetchone()

        return models.FrequencyWordsListModel(id=a[0], namee=a[1], lang=a[2], updated_time=a[3], words=a[5], creation_time=a[4])

    def ready_check(self):
        rec = proced_rec.not_recalced(self.pg_con)
        pre = proced_pre.not_processed(self.pg_con)
        summ = rec + pre

        if summ != 0:
            raise Exception("not all cards processed")

    def generate(self, name: str, lang: str, tags: List[str] = [], decks: List[str] = [], note_types: List[str] = []) -> None:
        self.ready_check()

        tags_ln = len(tags)
        decks_ln = len(decks)
        note_types_ln = len(note_types)
        args_ln = tags_ln + decks_ln + note_types_ln

        ids = []
        if args_ln != 0:
            cards_query = ["SELECT id FROM cards", " WHERE "]
            cards_params = []

            if tags_ln != 0:
                cards_query.append("tags && %s::VARCHAR[]")
                cards_params.append(tags)

            if decks_ln != 0:
                if tags_ln != 0:
                    cards_query.append(" AND ")

                cards_query.append("deck = ANY(%s::Varchar[])")
                cards_params.append(decks)

            if note_types_ln != 0:
                if tags_ln != 0 or decks_ln != 0:
                    cards_query.append(" AND ")

                cards_query.append("note_type = ANY(%s::Varchar[])")
                cards_params.append(note_types)

            self.cur.execute("".join(cards_query), cards_params)
            ids = [item[0] for item in self.cur.fetchall()]

        words_lists = []
        if len(ids) != 0:
            self.cur.execute(
                '''SELECT all_words FROM preprocessing WHERE related_card = ANY(%s::INTEGER[])''', [ids])
        else:
            self.cur.execute('''SELECT all_words FROM preprocessing''')
        words_lists = [item[0] for item in self.cur.fetchall()]

        words_lists_unpacked = list(chain.from_iterable(words_lists))
        words_counter = Counter(words_lists_unpacked).most_common(20_000)
        words_counter2 = [item[0] for item in words_counter]

        self.cur.execute(
            '''INSERT INTO frequency_words_lists(namee,lang,words) VALUES(%s,%s,%s)''', [name, lang, words_counter2])


class FullTextsStorageDb:
    def __init__(self, pg_con: 'psycopg.Connection', lang: str) -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()
        self.lang = lang

    def add_list(self, sentences: List[str], full_path: str, fake_file: bool = False):
        if fake_file:
            full_path2 = os.path.normpath(
                "".join(["C:\\", "fake_", datetime.now().strftime(const.FILE_DATE_FORMAT_PREC), ".txt"]))
        else:
            full_path2 = os.path.normpath(full_path)

        sentences_hash = utilities.generate_hash_from_list(sentences, 128)
        file_name = os.path.split(full_path2)[1]

        self.cur.execute('''INSERT INTO full_texts_storage(lang,file_path,file_name,sentences,sentences_hash) 
                         VALUES(%s,%s,%s,%s,%s)''', [self.lang, str(full_path2), str(file_name), sentences, sentences_hash])


if __name__ == "__main__":
    pass
