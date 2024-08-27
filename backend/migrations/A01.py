import migrations.interfaces as interfaces
import psycopg
from db_models.db_objects import JpPosBlacklist
import db_models.dbs_con as dc


class JpPosBlacklistMigrate(interfaces.Migration):
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        super().__init__(pg_con)

    def main(self):
        self.cur.execute('''SELECT contentt FROM json_storage WHERE namee=%s''', [
                         "jp_pos_blacklist"])
        to_insert = self.cur.fetchone()[0]["content"]
        JpPosBlacklist(self.pg_con).add(to_insert).save(False)

        self.cur.execute('''DELETE FROM json_storage''')


class A01M(interfaces.Migration):
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        super().__init__(pg_con)

    def main(self):
        uuid_to_id = '''
            ALTER TABLE preprocessing
            DROP COLUMN id;
            ALTER TABLE preprocessing
            ADD COLUMN id int GENERATED ALWAYS AS IDENTITY;
            
            ALTER TABLE recalc DROP COLUMN id;
            ALTER TABLE recalc;
            ADD COLUMN id int GENERATED ALWAYS AS IDENTITY;
            '''
        self.cur.execute(uuid_to_id)
        JpPosBlacklistMigrate(self.pg_con).main()

        full_texts_storage = '''
            CREATE TABLE full_texts_storage (
                id int GENERATED ALWAYS AS IDENTITY,
                lang VARCHAR(3) CHECK(lang = 'jp' or lang = 'eng'),
                file_path TEXT NOT NULL,
                file_name VARCHAR(50) UNIQUE NOT NULL,
                sentences TEXT[] NOT NULL,
                sentences_hash VARCHAR(256) UNIQUE NOT NULL,
                time_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
                '''
        self.cur.execute(full_texts_storage)

        self.cur.execute('''ALTER TABLE cards ADD ai_interpretation TEXT''')


def run():
    a = dc.postgres_con()

    A01M(a).main()

    a.commit()
    a.close()
