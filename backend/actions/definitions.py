import os
from typing import List

from db_models import db_objects, dbs_con
from files_utilities import main as fu
from general import exportt, maintenance
from general.maintenance import Postgres
from importers import import_own, importt
from nlp import jp
from procedures import preprocessing, recalc

from .interface import Action

from general import _logging
from loguru import logger


class PostgresBackup(Action):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "postgres backup"

    def _do(self):
        Postgres().backup()


class PostgresRestore(Action):
    def __init__(self, backup_name: str | bool = False) -> None:
        self.backup_name = backup_name

    def __str__(self) -> str:
        return "postgres restore"

    def _do(self):
        if self.backup_name == False:
            a = fu.FileOps().file_list_by_date_oldest(r"backup\postgres_backups")
            a2 = a[-1]
            a3 = os.path.split(a2)
            a4 = a3[1].replace(".dump", "")
            logger.debug(a4)
            self.backup_name = a4

        elif isinstance(self.backup_name, str):
            pass
        else:
            raise AttributeError

        logger.debug(f"restoring {self.backup_name}")
        Postgres().restore(self.backup_name)


class ImportVn(Action):
    def __init__(self, vn_name: str, file_path: str, clean_file: bool) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.file_path = file_path
        self.vn_name = vn_name
        self.clean_file = clean_file

    def __str__(self) -> str:
        return "import visual novel"

    def _do(self):
        importt.ImportVisualNovel().importt(self.file_path, self.clean_file, self.vn_name)

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()
        PostgresBackup().execute()


# class ImportMediaRandom(Action):
#     def __init__(self, file_path: str) -> None:
#         self.pg_con = dbs_con.postgres_con()
#         self.file_path = file_path

#     def __str__(self) -> str:
#         return "import media random"

#     def _do(self):
#         importt.ImportJpMediaRandom().importt(self.file_path)

#     def _effects(self):
#         self.pg_con.close()


# class ImportTwitterRandom(Action):
#     def __init__(self, file_path: str) -> None:
#         self.pg_con = dbs_con.postgres_con()
#         self.file_path = file_path

#     def __str__(self) -> str:
#         return "import twitter random"

#     def _do(self):
#         importt.ImportTwitter().importt(self.file_path)

#     def _effects(self):
#         self.pg_con.close()


class AddToKnownJp(Action):
    def __init__(self, to_add: list, lang: str) -> None:
        self.to_add = to_add
        self.lang = lang

        self.pg_con = dbs_con.postgres_con()

    def __str__(self) -> str:
        return "add to known jp"

    def _do(self):
        db_objects.KnownWords(self.lang, self.pg_con).add(
            self.to_add).save(False)

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()


class ImportOwn(Action):
    def __init__(self, file_name: str, dry_run: bool, backup_start: bool, backup_end: bool) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.file_name = file_name
        self.dry_run = dry_run
        self.backup_start = backup_start
        self.backup_end = backup_end

    def __str__(self) -> str:
        return "import anki mia own"

    def _preparation(self):
        if self.backup_start == True:
            PostgresBackup().execute()

    def _do(self):
        import_own.main(self.pg_con, self.file_name, self.dry_run)

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()

        if self.backup_end == True:
            PostgresBackup().execute()


class Exportt(Action):
    def __init__(self, num: int) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.num = num

    def __str__(self) -> str:
        return "mia db export"

    def _do(self):
        exportt.Export(self.pg_con, self.num).export()

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()


class ImportLightNovelsMass(Action):
    def __init__(self, folder: str) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.folder = folder

    def __str__(self) -> str:
        return "mass import light novels"

    def _preparation(self):
        pass

    def _do(self):
        a = importt.ImportLn(self.pg_con)
        a.import_to_db_mass(self.folder)

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()
        # maintenance.Postgres().backup()


class ImportLightNovelsSingle(Action):
    def __init__(self, file: str) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.file = file

    def __str__(self) -> str:
        return "mass import light novels"

    def _preparation(self):
        pass

    def _do(self):
        a = importt.ImportLn(self.pg_con)
        a.import_to_db_single(self.file)

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()
        # maintenance.Postgres().backup()

# class ImportBooksRandomMass(Action):
#     def __init__(self, folder: str) -> None:
#         self.pg_con = dbs_con.postgres_con()
#         self.folder = folder

#     def __str__(self) -> str:
#         return "mass import random books"

#     def _preparation(self):
#         maintenance.Postgres().backup()

#     def _do(self):
#         a = importt.ImportLn(self.pg_con)
#         a.import_to_db_mass(self.folder)

#     def _effects(self):
#         self.pg_con.close()


class Preprocessing(Action):
    def __init__(self, drop: bool) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.drop = drop

    def __str__(self) -> str:
        return "preprocessing"

    def _preparation(self):
        if self.drop == True:
            db_objects.PreprocessingDb(self.pg_con).clear_all()

    def _do(self):
        preprocessing.main(self.pg_con)

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()


class Recalc(Action):
    def __init__(self, drop: bool) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.drop = drop

    def __str__(self) -> str:
        return "recalc"

    def _preparation(self):
        if self.drop == True:
            db_objects.RecalcDb(self.pg_con).clear_all()

    def _do(self):
        recalc.main(self.pg_con)

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()


class PreprocessingRecalc(Action):
    '''WARNING: auto-truncating tables'''

    def __init__(self) -> None:
        self.pg_con = dbs_con.postgres_con()

    def __str__(self) -> str:
        return "preprocessing and recalc"

    def _do(self):
        Preprocessing(drop=True, backup_start=False,
                      backup_end=False).execute()
        Recalc(drop=True, backup_start=False, backup_end=True).execute()

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()


class GenerateFrequency(Action):
    def __init__(self, name: str, lang: str, tags: List[str] = [], decks: List[str] = [], note_types: List[str] = []) -> None:
        self.generate_args = {"name": name, "lang": lang,
                              "tags": tags, "decks": decks, "note_types": note_types}
        self.pg_con = dbs_con.postgres_con()

    def __str__(self) -> str:
        return "generating frequency"

    def _do(self):
        db_objects.FrequencyWordsLists(
            self.pg_con).generate(**self.generate_args)

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()


class PosMaintenanceJp(Action):
    def __init__(self, backup_start: bool) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.backup_start = backup_start

    def _preparation(self):
        if self.backup_start == True:
            PostgresBackup().execute()

    def _do(self):
        jp.JpPosBlacklister(self.pg_con).test_current_blacklist()

    def __str__(self) -> str:
        return "JpPosMaintenance"

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()


class AddToPosBlacklistJp(Action):
    def __init__(self, word: str) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.word = word

    def _do(self):
        jp.JpPosBlacklister(self.pg_con).execute(self.word, 0)

    def __str__(self) -> str:
        return "AddToPosBlacklistJp"

    def _effects(self):
        self.pg_con.commit()
        self.pg_con.close()


if __name__ == "__main__":
    pass
