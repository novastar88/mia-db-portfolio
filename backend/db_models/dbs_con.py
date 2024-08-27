import psycopg
from utilities import config_reader, is_stable_branch


config = config_reader()
pg_settings = config["postgres"]


def postgres_con() -> 'psycopg.Connection':
    stable_branch = is_stable_branch()

    if stable_branch:
        current_db = pg_settings["db_name"]
    else:
        current_db = pg_settings["db_name_features"]

    return psycopg.connect(dbname=current_db, user=pg_settings["user"],
                           password=pg_settings["pass"], host="localhost")


if __name__ == "__main__":
    pass
