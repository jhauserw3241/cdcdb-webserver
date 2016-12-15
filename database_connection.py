from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, Table
from globals import globals

# manages a connection to a database
# should be used in a with block
# with DatabaseConnection() as db:
#       pass

class DatabaseConnection:
    # Called as the python 'with' block is entered
    def __enter__(self):
        self.engine = globals.db_engine
        self.Session = sessionmaker(bind=self.engine)
        self.sess = self.Session()
        self.last_result = None
        return self

    # Called when exiting the python 'with' block
    def __exit__(self, type, value, traceback):
        if self.last_result:
            self.last_result.close()
            self.last_result = None
        self.sess.commit()
        self.sess.close()
        self.sess = None

    # Perform the given statement
    def execute(self, statement):
        if self.last_result:
            self.last_result.close()
            self.last_result = None
        self.last_result = self.sess.execute(statement)

    # Dumb little wrapper to return the new query with any entities/kwargs
    def query(self, *entities, **kwargs):
        return self.sess.query(*entities, **kwargs)

    # Dumb little wrapper
    def commit(self):
        self.sess.commit()

    # Dumb little wrapper
    def fetchone(self):
        if not self.last_result:
            raise Exception("Can't fetch without selecting first")
        return self.last_result.fetchone()

    # Dumb little wrapper
    def fetchall(self):
        if not self.last_result:
            raise Exception("Can't fetch without selecting first")
        for row in self.last_result.fetchall():
            yield row

    # Dumb little wrapper
    def lastrowid(self):
        if not self.last_result:
            raise Exception(
                "Can't get lastrowid without inserting/updating first")
        return self.last_result.fetchone()

    # Useful little wrapper to get everything about the given table
    def get_table(self, table_name):
        meta = MetaData(self.engine)
        table = Table(table_name, meta, autoload=True, autoload_with=self.engine)
        return table, meta
