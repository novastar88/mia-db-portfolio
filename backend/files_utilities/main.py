import os
import re
from glob import glob
from pathlib import Path
# import random
import csv
from typing import List
from general import _logging
from loguru import logger


# class TestingSuite:
#     def txt_files_loader(self, file: str):
#         a = open(file, "r", encoding="utf-8")
#         b = a.read().splitlines()
#         a.close()

#         return b

#     def manual_result(self, source, changed, question: str):
#         print("--------------------")
#         print(source)
#         print("vs")
#         print(changed)
#         b = input(f"{question} (t,n): ")

#         if b == "t":
#             pass
#         else:
#             raise Exception

#     def manual_result_tokenize_normalise(self, data: dict):
#         print("--------------------")
#         print("sentence")
#         print(data["sentence"])
#         print("--------------------")
#         print("tokens passed")
#         for item in data["tokens"]:
#             print(item)
#         print("--------------------")
#         print("banned_expressions")
#         for item2 in data["banned_expressions"]:
#             print(item2)

#         b = input("Is correctly tokenized? (t,n): ")

#         if b == "t":
#             pass
#         else:
#             raise Exception

#     def manual_check_random(self, data: list, n: int, question: str):
#         pick_random = random.choices(data, k=n)

#         for item in pick_random:
#             print("--------------------")
#             print(item)
#             a = input(f"{question} (t,n): ")
#             if a == "t":
#                 pass
#             else:
#                 raise Exception


class FileOps:
    # def file_list_with_names(self, location: str) -> dict:
    #     list_of_files = []
    #     list_of_filenames = []
    #     for (dirpath, _, filenames) in os.walk(location):
    #         list_of_files += [os.path.join(dirpath, file)
    #                           for file in filenames]
    #         list_of_filenames = list(filenames)

    #     return {"list_of_files": list_of_files, "list_of_filenames": list_of_filenames}

    # def unpack_apkg(self, file: str) -> dict:
    #     a = os.path.split(file)
    #     b = os.path.splitext(a[1])
    #     nazwa = b[0]
    #     master_dir = os.path.join(os.path.dirname(
    #         os.path.realpath(__file__)), "apkg_temp")
    #     placee = os.path.join(master_dir, nazwa)

    #     if os.path.exists(placee) is True:
    #         pass
    #     else:
    #         shutil.unpack_archive(file, placee, format="zip")

    #     med = os.path.join(placee, "media")

    #     if os.path.exists(os.path.join(placee, "collection.anki21")):
    #         dbb = os.path.join(placee, "collection.anki21")
    #     else:
    #         dbb = os.path.join(placee, "collection.anki2")

    #     return {"media": med, "db": dbb, "path": placee, "name": nazwa}

    # def rename_media(self, file: str, directory: str, nazwa: str):
    #     zmienne = utilities.config_reader()
    #     media_storage = zmienne["media_storage_folder"]
    #     a = open(file, "r", encoding="utf-8")
    #     b = json.load(a)

    #     media_placement = None

    #     for k, v in b.items():
    #         point = os.path.join(directory, k)

    #         if media_storage == "":
    #             change = os.path.join(directory, v)
    #         else:
    #             change = os.path.join(media_storage, nazwa, v)
    #             media_placement = os.path.join(media_storage, nazwa)

    #         try:
    #             shutil.move(point, change)
    #         except FileNotFoundError:
    #             os.mkdir(media_placement)
    #             shutil.move(point, change)

    #     return media_placement

    # def clean_files_apkg(self) -> None:
    #     a = os.path.join(os.path.dirname(
    #         os.path.realpath(__file__)), "apkg_temp")
    #     shutil.rmtree(a)
    #     os.makedirs(a)

    def all_files_with_extension(self, folder: str, extension: str):
        a = os.path.join(folder, "*." + extension)
        b = glob(a)
        return b

    def apkg_img_extract(self, data):
        patterns = [r"<img src=\"(.*?.)\" \/>", r"<img src=\"(.*?.)\">",
                    r"<img src=(.*?.)>", r"<img src=\"(.*?.)\""]

        for pattern in patterns:
            a = re.findall(pattern, data)
            if len(a) == 0:
                continue
            else:
                return [str(item) for item in a]

        logger.warning(f"img not found: {data}")
        return None

    def apkg_sound_extract(self, data):
        a = re.findall(r"\[sound:(.*?.)\]", data)
        if len(a) == 0:
            logger.warning(f"sound not found: {data}")
            return None
        else:
            return [str(item) for item in a]

    def file_list_by_date_oldest(self, dir: str) -> list:
        return list(sorted(Path(dir).iterdir(),
                           key=os.path.getmtime))

    # def returrn_media(self, directory: str) -> dict:
    #     names = []
    #     paths = []

    #     for root, _, file in os.walk(directory):
    #         for name in file:
    #             names.append(name)
    #             paths.append(os.path.join(root, name))

    #     return {"names": names, "paths": paths}

    # def get_apkg_extract_media(self, data, dirr: str):
    #     a = Deck(True, {"name": data["deck"]}).get_record()
    #     b = data["files"]

    #     main_pth = a["path"]
    #     if b[0] != "":
    #         b1 = self.apkg_sound_extract(b[0])
    #         b1a = os.path.join(main_pth, a["name"], b1)
    #         b1c = os.path.join(dirr, b1)
    #         try:
    #             shutil.move(b1a, b1c)
    #         except Exception:
    #             pass

    #     if b[1] != "":
    #         b2 = self.apkg_img_extract(b[1])
    #         b2a = os.path.join(main_pth, a["name"], b2)
    #         b2c = os.path.join(dirr, b2)
    #         try:
    #             shutil.move(b2a, b2c)
    #         except Exception:
    #             pass


class WordsFromTxt:
    def __init__(self, f_path: str) -> None:
        self.f_path = f_path

    def as_csv(self, target_column: int, delimiter: str = "	") -> List[str]:
        with open(self.f_path, "r", encoding="utf-8") as file:
            a = csv.reader(file.read().splitlines(), delimiter=delimiter)
            return [item[target_column] for item in a]

    def word_per_line(self) -> List[str]:
        with open(self.f_path, "r", encoding="utf-8") as file:
            return file.read().splitlines()


if __name__ == "__main__":
    pass
