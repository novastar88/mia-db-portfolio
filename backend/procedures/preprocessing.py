from nlp import jp as nlp
from db_models import dbs_con, db_objects, models
import multiprocessing as mp
from utilities import main as utilities
from math import ceil
import psycopg
from typing import List
from itertools import chain

from general import _logging
from loguru import logger


def process(records_l: list, blacklist: List[str], words_ignore_list: List[str]) -> List[models.PreprocessingModel]:
    logger.info(" ".join(["processing", str(len(records_l)), "records"]))
    nlp_o = nlp.JapaneseNlp(True, True)
    prep_records_list = []

    for item in records_l:
        nlp_out = nlp_o.tokenize_and_normalize(
            item[0].sentence, blacklist, words_ignore_list, [])

        prep_records_list.append(models.PreprocessingModel(related_card=item[0].idd, all_words=[item.normalised_form for item in nlp_out.tokens_passed],
                                                           bonus_rating_sum_a=item[1].bonus_rating_note, words_number=nlp_out.all_tokens_count))

    return prep_records_list


def main(pg_con: 'psycopg.Connection') -> None:
    records_number = 4_200_000
    threads = 12

    to_do = db_objects.PreprocessingDb(pg_con).not_processed()
    to_do2 = int(ceil(to_do / records_number))
    blacklist = db_objects.JpPosBlacklist(pg_con).str_list
    words_ignore = db_objects.WordsIgnore("jp", pg_con).words_list

    for num in range(to_do2):
        logger.info(f"{num + 1} / {to_do2}")
        a = db_objects.CardsDb(
            pg_con).preprocessing_view__fetch(records_number)

        a_parted = utilities.split_list(threads, a)
        args_list = [(item, blacklist, words_ignore,) for item in a_parted]
        pool = mp.Pool(threads)
        res = pool.starmap(process, args_list)
        pool.close()
        b = list(chain.from_iterable(res))

        db_objects.PreprocessingDb(pg_con).insert_many(b)


def execute_standalone() -> None:
    with dbs_con.postgres_con() as connection:
        main(connection)
        connection.commit()


if __name__ == "__main__":
    pass
