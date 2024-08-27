from db_models import db_objects as dbo
import psycopg
from general.exceptions import UnexpectedExit
from general.checkers import not_empty


class SentenceRatingSystemProduct:
    def __init__(self) -> None:
        self.mode: int = None
        self.used_list: list = None
        self.used_list_len: int = None


def sentence_rating_system_producer(config: dict, pg_con: 'psycopg.Connection') -> SentenceRatingSystemProduct:
    jp_conf = config["jp_config"]

    match jp_conf["sentence_rating_mode"]:
        case 0:
            a = SentenceRatingSystemProduct()
            a.mode = 0

            return a
        case 1:
            used_list_setting = jp_conf["used_priority_list"]

            a = SentenceRatingSystemProduct()
            a.mode = 1
            a.used_list = dbo.PriorityWordsDb(pg_con).get_list(
                name=used_list_setting).words
            a.used_list_len = len(a.used_list)
            not_empty(a.used_list)

            return a
        case 2:
            used_list_setting = jp_conf["used_frequency_list"]

            a = SentenceRatingSystemProduct()
            a.mode = 2
            a.used_list = dbo.FrequencyWordsLists(pg_con).get_list(
                idd=used_list_setting).words
            a.used_list_len = len(a.used_list)
            not_empty(a.used_list)

            return a
        case _:
            raise UnexpectedExit()


def proxy_function(srs_product: SentenceRatingSystemProduct, unknown_word: str, bonus_rating_sum_a: int) -> int:
    match srs_product.mode:
        case 0:
            return bonus_rating_sum_a
        case 1:
            score = bonus_rating_sum_a

            if unknown_word in srs_product.used_list:
                score += bonus_rating_sum_a

            return score
        case 2:
            score = bonus_rating_sum_a

            if unknown_word in srs_product.used_list:
                indx = srs_product.used_list.index(unknown_word)
                pre_score = srs_product.used_list_len - indx
                score += int(pre_score)

            return score * bonus_rating_sum_a
        case _:
            raise UnexpectedExit()


if __name__ == "__main__":
    pass
