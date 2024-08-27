from general.const import *
import sqlite3
from utilities import main as utilities
from zipfile import ZipFile
import shutil
import os
import uuid
from db_models import models
import csv
import pickle
from typing import List


class TextFile():
    def __init__(self, f_path: str, encoding: str = "utf-8") -> None:
        self.f_path = f_path
        self.encoding = encoding

        self.content = None
        self.current_encoding = self.encoding

        self.__load()

    def __load(self):
        a = self.__open("r")
        self.content: str = a.read()
        a.close()

    def __open(self, mode: str):
        a = None
        try:
            a = open(file=self.f_path, mode=mode, encoding=self.encoding)
        except (UnicodeDecodeError, UnicodeError):
            for item in ENCODINGS:
                try:
                    a = open(self.f_path, mode, item)
                    self.encoding = item
                    break
                except (UnicodeDecodeError, UnicodeError):
                    pass

        return a

    def give_lines(self) -> List[str]:
        a = self.__open("r")
        lines = a.read().splitlines()
        a.close()

        return lines

    def clean_file(self):
        a = self.__open("w")
        a.write("")
        a.close()


class Apkg:
    def __init__(self) -> None:
        self.identifier = utilities.generate_hash(str(uuid.uuid4), 6)
        # self.identifier = "test"
        self.file_path = None
        self.apkg_path = None
        self.media_file = None
        self.db_file = None
        self.con = None
        self.cur = None

    def load(self, f_path: str) -> None:
        self.apkg_path = f_path
        self.file_path = os.path.join("backend", "temp", self.identifier)

        archive = ZipFile(f_path, "r")
        archive.extractall(self.file_path)

        self.media_file = os.path.join(self.file_path, "media")
        self.db_file = os.path.join(self.file_path, "collection.anki2")

        self.con = sqlite3.connect(self.db_file)
        self.cur = self.con.cursor()

    def _remove_temp(self):
        shutil.rmtree(self.file_path)

    def _remove_apkg(self):
        os.remove(self.apkg_path)


class ExportFileCsv:
    def __init__(self) -> None:
        self.identifier = utilities.generate_file_name()
        self.f_path = os.path.join(utilities.config_reader(
        )["paths"]["main_dir"], "export", self.identifier)

    def _make_dir(self):
        try:
            os.makedirs(self.f_path)
        except FileExistsError:
            pass

    def _make_media_dir(self):
        self.m_path = os.path.join(self.f_path, "media")
        try:
            os.mkdir(self.m_path)
        except FileExistsError:
            pass

    def _csv_init(self):
        self.t_path = os.path.join(self.f_path, "cards.csv")
        self.t_file = open(file=self.t_path, mode="w", encoding="utf-8")

    def _line_maker(self, card: models.CardModel, recalc: models.RecalcModel, context: str):
        if recalc.unknown_word != None:
            unk_w = recalc.unknown_word
        else:
            unk_w = ""

        if card.tags != None:
            tags = " ".join(card.tags)
        else:
            tags = ""

        if card.meaning != None:
            meaning = card.meaning
        else:
            meaning = ""

        if card.audio != None:
            audio = card.audio
        else:
            audio = ""

        if card.screen != None:
            screen = card.screen
        else:
            screen = ""

        if context != None:
            card_context = context
        else:
            card_context = ""

        if card.ai_interpretation != None:
            card_ai = card.ai_interpretation
        else:
            card_ai = ""

        return [card.sentence, meaning, audio, screen, unk_w, str(card.idd),
                tags, card_context, card_ai]

    def save_text(self, cards: list):
        '''1:card,2:recalc,3:context'''
        self._make_dir()
        self._csv_init()

        a = [self._line_maker(item[0], item[1], item[2])
             for item in cards]

        writer = csv.writer(self.t_file, delimiter="‽")
        writer.writerows(a)

        self.t_file.close()


class PickleTempContainer:
    def __init__(self, name: str = None) -> None:
        pathh = os.path.join(utilities.config_reader()[
                             "paths"]["main_dir"], "temp")

        if name == None:
            name2 = ".".join([utilities.generate_file_name(), "pickle"])
        else:
            name2 = ".".join([name, "pickle"])

        self.full_path = os.path.join(pathh, name2)
        self.content = None

        try:
            self.__load()
        except FileNotFoundError:
            pass

    def __load(self):
        with open(self.full_path, "rb") as file:
            self.content = pickle.load(file)

    def save(self):
        with open(self.full_path, "wb") as file:
            pickle.dump(self.content, file)


if __name__ == "__main__":
    pass
