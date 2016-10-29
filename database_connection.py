from sqlalchemy import select, join
from sqlalchemy import MetaData, Table
from globals import globals
# manages a connection to a database
# should be used in a with block
# with DatabaseConnection() as db:
#       pass

class DatabaseConnection:
    def __enter__(self):
        self.engine = globals.db_engine
        self.conn = self.engine.connect()
        self.last_result = None
        return self
    def __exit__(self, type, value, traceback):
        if self.last_result:
            self.last_result.close()
            self.last_result = None
        self.conn.close()
        self.conn = None

    def execute(self, statement):
        if self.last_result:
            self.last_result.close()
            self.last_result = None
        self.last_result = self.conn.execute(statement)

    def select(self, columns=None, whereclause=None, from_obj=None,
        distinct=False, having=None, correlate=True, prefixes=None,
        suffixes=None, **kwargs):
        return select(columns, whereclause, **kwargs)

    def join(self, stmt, left, right, onclause=None, isouter=None):
        j = left.join(right, onclause, isouter)
        return stmt.select_from(j)

    #def join(self, stmt, right, onclause=None, isouter=None):
    #    return stmt.join(right, onclause, isouter)

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
        meta = MetaData()
        table = Table(table_name, meta, autoload=True, autoload_with=self.engine)
        return table, meta
