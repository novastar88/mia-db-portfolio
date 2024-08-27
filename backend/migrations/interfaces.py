import psycopg


class Migration:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def main(self):
        raise NotImplementedError
