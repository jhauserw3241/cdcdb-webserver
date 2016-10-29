from sqlalchemy import select, join
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table
from globals import globals
# manages a connection to a database
# should be used in a with block
# with DatabaseConnection() as db:
#       pass

class DatabaseConnection:
    def __enter__(self):
        self.engine = globals.db_engine
        self.Session = sessionmaker(bind=self.engine)
        self.sess = self.Session()
        self.last_result = None
        return self
    def __exit__(self, type, value, traceback):
        if self.last_result:
            self.last_result.close()
            self.last_result = None
        self.sess.close()
        self.sess = None

    def execute(self, statement):
        if self.last_result:
            self.last_result.close()
            self.last_result = None
        self.last_result = self.sess.execute(statement)

    def query(self, *entities, **kwargs):
        return self.sess.query(*entities, **kwargs)

    def fetchone(self):
        if not self.last_result:
            raise Exception("Can't fetch without selecting first")
        return self.last_result.fetchone()

    def fetchall(self):
        if not self.last_result:
            raise Exception("Can't fetch without selecting first")
        for row in self.last_result.fetchall():
            yield row

    def get_table(self, table_name):
        meta = MetaData(self.engine)
        table = Table(table_name, meta, autoload=True, autoload_with=self.engine)
        return table, meta
