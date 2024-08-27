from os import path
from more_itertools import divide
import tomli
import time
import hashlib
from typing import List


def find_sentence_context_neighbours(line_number: int, depth: int) -> dict:
    if line_number <= 0:
        raise Exception("line number must be greater than 0")

    if depth <= 0:
        raise Exception("depth must be greater than 0")

    start1 = line_number - depth

    if start1 <= 0:
        start1 = 1

    end = line_number + depth + 1

    r_list = [item for item in range(start1, end)]
    r_start = []
    r_end = []

    middle_reached = False
    for item in r_list:
        if item == line_number:
            middle_reached = True
            continue

        if not middle_reached:
            r_start.append(item)
        else:
            r_end.append(item)

    return dict(start=r_start, middle=line_number, end=r_end)


def config_reader() -> dict:
    a = None

    pth = r"C:\\Users\\Mateusz\\PycharmProjects\\zdania_mia_db-v3"
    pth2 = path.join(pth, "config.toml")

    with open(pth2, "rb") as file:
        a = tomli.load(file)

    return a


def is_stable_branch() -> bool:
    '''0:stable, 1:features'''
    a = config_reader()

    if a["mode"] == 0:
        return True
    elif a["mode"] == 1:
        return False
    else:
        raise TypeError


def generate_hash(inp: str, lng: int) -> str:
    return hashlib.shake_256(inp.encode()).hexdigest(lng)


def generate_hash_from_list(strings: list, lng: int):
    inp = "".join([str(item) for item in strings])

    return generate_hash(inp, lng)


def generate_file_name(ln: int = 5) -> str:
    return generate_hash(str(time.time()), ln)


def sql_loader(filep: str) -> str:
    sql = None

    with open(filep, "r", encoding="utf-8") as file:
        sql = file.read()

    return sql


def split_list(threads: int, data):
    return [list(i) for i in divide(threads, data)]


def mass_replace(inpt: str, filters: list):
    '''not regex!'''
    new_string = inpt

    for filter in filters:
        rpl = new_string.replace(filter, "")
        new_string = rpl

    return new_string


if __name__ == "__main__":
    pass
