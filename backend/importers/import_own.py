from general import _logging
from db_models import models, db_objects
import re
import psycopg
from loguru import logger
from general.exceptions import UnexpectedExit
from nlp import jp


class UpdateChanges:
    def __init__(self, pg_con: 'psycopg.Connection', card: models.CardModel) -> None:
        self.pg_con = pg_con
        self.cur = pg_con.cursor()
        self.card = card

    def _get_from_db(self):
        self.cur.execute(
            '''SELECT sentence,meaning FROM cards WHERE id=%s''', [self.card.idd])
        fetch_a = self.cur.fetchone()

        return models.CardModel(
            sentence=fetch_a[0], meaning=fetch_a[1], idd=int(self.card.idd))

    def _compare_update_macro(self, db, card, sql: str, args_l: list, sql_l: list):
        if card not in [db, "[~]"]:
            args_l.append(card)
            sql_l.append(sql)

    def compare_and_update(self):
        db_card = self._get_from_db()
        args = []
        sql = []

        # sentence
        self._compare_update_macro(
            db_card.sentence, self.card.sentence, r"sentence = %s", args, sql)

        # meaning
        self._compare_update_macro(
            db_card.meaning, self.card.meaning, r"meaning = %s", args, sql)

        # tags
        self._compare_update_macro(
            db_card.tags, self.card.tags, r"tags = %s", args, sql)

        # audio
        self._compare_update_macro(
            db_card.audio, self.card.audio, r"audio = %s", args, sql)

        # screen
        self._compare_update_macro(
            db_card.screen, self.card.screen, r"screen = %s", args, sql)

        # ai_interpretation
        self._compare_update_macro(
            db_card.ai_interpretation, self.card.ai_interpretation, r"ai_interpretation = %s", args, sql)

        if len(args) != 0:
            sql2 = ", ".join(sql)
            self.cur.execute(
                f'''UPDATE cards SET {sql2} WHERE id={db_card.idd}''', args)

            self.cur.execute(
                '''DELETE FROM preprocessing WHERE related_card=%s''', [db_card.idd])


class StatusResolver:
    '''musi być na końcu do updatowania kart - translacja'''

    def __init__(self, pg_con: 'psycopg.Connection', anki_status: models.AnkiStatusModel, card: models.CardModel, checked: models.RecalcModel) -> None:
        self.pg_con = pg_con
        self.cur = pg_con.cursor()
        self.anki_status = anki_status
        self.card = card
        self.checked = checked

        self.anki_status_db = db_objects.AnkiStatusDb(self.pg_con, False)

    def _status_1(self):
        logger.trace(f"status 1: " + str(self.card.idd))
        self.anki_status_db.delete_by_related_card_id(self.card.idd)

    def _status_2(self):
        logger.trace(f"status 2: " + str(self.card.idd))
        db_objects.WordsOnHold("jp", self.pg_con).add(
            self.checked.unknown_word).save(False)
        self.cur.execute(
            '''DELETE FROM recalc WHERE unknown_word=%s''', [self.checked.unknown_word])

    def _status_4(self):
        logger.trace(f"status 4: " + str(self.card.idd))
        known_word = self.checked.unknown_word
        db_objects.KnownWords("jp", self.pg_con).add(
            known_word).save(False)
        self.anki_status_db.delete_by_related_card_id(self.card.idd)
        self.cur.execute(
            '''DELETE FROM recalc WHERE unknown_word=%s''', [known_word])

    def _status_5(self):
        logger.trace(f"status 5: " + str(self.card.idd))
        unknown_words = self.anki_status.details
        unknown_words2 = unknown_words.split(", ")
        logger.trace(" ".join(["unknown word: ", unknown_words2]))
        db_objects.KnownWords("jp", self.pg_con).remove(
            unknown_words2).save(False)
        self.anki_status_db.delete_by_related_card_id(self.card.idd)

        # find card_id with words
        self.cur.execute(
            '''SELECT related_card FROM public.preprocessing WHERE %s::varchar[] && all_words''', [unknown_words2])
        a = [item[0] for item in self.cur.fetchall()]

        # delete with card_id
        logger.trace("".join(["removing recalc len: ", str(len(a))]))
        self.cur.execute(
            '''DELETE FROM public.recalc WHERE card_id=ANY(%s)''', [a])

    def _status_6(self):
        logger.trace(f"status 6: " + str(self.card.idd))
        self.anki_status_db.delete_by_related_card_id(self.card.idd)
        self.cur.execute(
            '''DELETE FROM recalc WHERE card_id=%s''', [self.card.idd])
        self.cur.execute(
            '''DELETE FROM preprocessing WHERE related_card=%s''', [self.card.idd])

    def _status_7(self):
        logger.trace(f"status 7: " + str(self.card.idd))
        db_objects.WordsIgnore("jp", self.pg_con).add(
            self.checked.unknown_word).save(False)
        self.cur.execute(
            '''DELETE FROM recalc WHERE unknown_word=%s''', [self.checked.unknown_word])

    def _status_8(self):
        logger.trace(f"status 8: " + str(self.card.idd))
        pos_bl = jp.JpPosBlacklister(self.pg_con)
        pos_bl.execute(self.checked.unknown_word, 0)

        self.anki_status_db.delete_by_related_card_id(self.card.idd)

    def _status_10(self):
        logger.trace(f"status 10: " + str(self.card.idd))
        self.anki_status_db.update_handled(self.card.idd, 10)

    def execute(self):
        status_code = self.anki_status.status
        match status_code:
            case 1:
                self._status_1()
            case 2:
                self._status_2()
            case 4:
                self._status_4()
            case 5:
                self._status_5()
            case 6:
                self._status_6()
            case 7:
                self._status_7()
            case 8:
                self._status_8()
            case 10:
                self._status_10()
            case _:
                raise Exception(f"invalid status code: {status_code}")


class OwnImporter:
    def __init__(self, pathh: str) -> None:
        self.pathh = pathh
        self.records = []

        self._load_file()

    def _anki_status_reader(self, status_part: str):
        try:
            status_code = int(status_part)

            return models.AnkiStatusModel(status=status_code)
        except ValueError:
            try:
                pattern = r"(\d*?)\[(.*?)\]"
                find = re.search(pattern, status_part)
                status_code = int(find.group(1))
                details = find.group(2)

                return models.AnkiStatusModel(status=status_code, details=details)
            except AttributeError:
                return models.AnkiStatusModel(status=1)

    def _load_file(self):
        a = open(self.pathh, "r", encoding="utf-8").read()
        b = a.splitlines()

        for item in b:
            c = item.split("\t")
            d = []

            for item in c:
                if item == "":
                    d.append(None)
                else:
                    d.append(item)

            d_len = len(d)
            if d_len != 8:
                raise Exception(f"expected 8 fields got {d_len}")

            try:
                tags_separated = d[9].split(" ")
            except AttributeError:
                tags_separated = None

            try:
                unknown_word = d[4]
            except AttributeError:
                raise Exception("unknown words is empty")

            card = models.CardModel(sentence=d[0], meaning=d[1], idd=int(
                d[5]), audio=d[2], screen=d[3], tags=tags_separated, ai_interpretation=d[8])
            recalc = models.RecalcModel(unknown_word=unknown_word)
            anki_status = self._anki_status_reader(c[6])
            anki_status.card_id = card.idd
            self.records.append([anki_status, card, recalc])

    def retrive(self):
        return self.records


def main(pg_con: 'psycopg.Connection', file_name: str, dry_run: bool = False):
    file = OwnImporter(file_name).retrive()

    if dry_run == True:
        print(file)
    elif dry_run == False:
        ln = len(file)
        for num, item in enumerate(file):
            logger.trace("".join([str(num + 1), " / ", str(ln)]))
            UpdateChanges(pg_con, item[1]).compare_and_update()
            StatusResolver(
                pg_con, item[0], item[1], item[2]).execute()
    else:
        raise UnexpectedExit()


if __name__ == "__main__":
    pass
