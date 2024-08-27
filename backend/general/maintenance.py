from os import system
from datetime import datetime
from utilities import config_reader, is_stable_branch
from general import const

config_postgres = config_reader()["postgres"]


class Postgres:
    def __init__(self) -> None:
        self.stable_branch = is_stable_branch()

        if self.stable_branch:
            self.dbname = config_postgres["db_name"]
        else:
            self.dbname = config_postgres["db_name_features"]

    def backup(self):
        dt_now = datetime.now().strftime(const.FILE_DATE_FORMAT)

        if self.stable_branch:
            filename = "_".join(["stable", dt_now])
        else:
            filename = "_".join(["features", dt_now])

        command = "".join(['"C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe" ',
                          '-U postgres --exclude-table-data=preprocessing --exclude-table-data=recalc -Fc ', self.dbname, ' > ',
                           'backup\\postgres_backups\\', filename, '.dump'])
        system(command)

    def backup_only_schema(self):
        dt_now = datetime.now().strftime(const.FILE_DATE_FORMAT)

        if self.stable_branch:
            filename = "_".join(["stable", dt_now, "schema"])
        else:
            filename = "_".join(["features", dt_now, "schema"])

        command = "".join(['"C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe" ',
                          '-U postgres --schema-only -Fp ', self.dbname, ' > ',
                           'backup\\postgres_backups\\', filename, '.dump'])
        system(command)

    def restore(self, backup_name: str):
        command = "".join(['"C:\\Program Files\\PostgreSQL\\16\\bin\\pg_restore.exe" ',
                          '-U postgres --clean -d ', self.dbname, ' <', 'backup\\postgres_backups\\', backup_name, '.dump'])
        system(command)


if __name__ == "__main__":
    pass
