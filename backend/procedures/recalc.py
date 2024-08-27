from db_models import dbs_con, models, db_objects
import psycopg
from nlp import jp as nlp
import multiprocessing as mp
from utilities import main as utilities
from math import ceil
from nlp import sentence_rating_system as srs
from typing import List
from itertools import chain

from general import _logging
from loguru import logger


def recalc(r_list: list, known: list, config: dict, srs_obj, on_hold_words) -> List[models.RecalcModel]:
    logger.info(" ".join(["processing", str(len(r_list)), "records"]))

    return [nlp.JapaneseRecalc(item, known, config, srs_obj, on_hold_words).execute() for item in r_list]


def main(pg_con: 'psycopg.Connection') -> None:
    records_number = 4_800_000
    threads = 36
    config = utilities.config_reader()

    known = db_objects.KnownWords("jp", pg_con).words_list
    on_hold = db_objects.WordsOnHold("jp", pg_con).words_list
    recalc_db = db_objects.RecalcDb(pg_con)

    to_do = recalc_db.not_processed()
    to_do2 = int(ceil(to_do / records_number))

    if to_do != 0 and len(db_objects.PreprocessingDb(pg_con).checked_view__fetch(1)) == 0:
        raise Exception("preprocessing required")

    srs_product = srs.sentence_rating_system_producer(config, pg_con)

    for num in range(to_do2):
        logger.info(f"{num + 1} / {to_do2}")
        a = db_objects.PreprocessingDb(
            pg_con).checked_view__fetch(records_number)
        a_parted = utilities.split_list(threads, a)
        args_list = [(item, known, config, srs_product, on_hold,)
                     for item in a_parted]

        pool = mp.Pool(threads)
        res = pool.starmap(recalc, args_list)
        pool.close()
        b = list(chain.from_iterable(res))
        recalc_db.insert_many(b)


def execute_standalone() -> None:
    with dbs_con.postgres_con() as connection:
        main(connection)
        connection.commit()


if __name__ == "__main__":
    pass
