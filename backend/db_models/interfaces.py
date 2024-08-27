import psycopg
# from db_models import models
from general import checkers
from general import exceptions as exc
# from utilities import main as utilities
import json
# from collections import Counter
# from typing import List
# import procedures.preprocessing as proced_pre
# import procedures.recalc as proced_rec
# from itertools import chain
# from general import _logging
# from loguru import logger


class JsonStorage:
    def __init__(self, name: str, pg_con: 'psycopg.Connection') -> None:
        self.name = name
        self.content = None
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        try:
            self._load()
        except exc.ObjectIsNone:
            self._create()

    def _load(self):
        self.cur.execute(
            '''SELECT contentt FROM json_storage WHERE namee=%s''', [self.name])
        a = self.cur.fetchone()

        checkers.not_none(a)
        self.content = a[0]["content"]

    def save(self):
        self.cur.execute('''UPDATE json_storage SET contentt=%s WHERE namee=%s''', [
                         self.__convert_to_save(), self.name])
        self.pg_con.commit()

    def _create(self):
        self.cur.execute('''INSERT INTO json_storage(namee,contentt) VALUES(%s,%s)''', [
                         self.name, self.__convert_to_save()])
        self.pg_con.commit()

    def __convert_to_save(self) -> str:
        return json.dumps({"content": self.content})
