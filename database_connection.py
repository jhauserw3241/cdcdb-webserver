import sqlite3
# manages a connection to a database
# should be used in a with block
# with DatabaseConnection() as db:
#       pass
class DatabaseConnection:
    def __enter__(self):
        self.filename = "database.sqlite"
        self.is_open = False
        self.connection = None
        self.cursor = None
        return self
    def __exit__(self, type, value, traceback):
        self.disconnect()
    def connect(self):
        if not self.is_open:
            self.connection = sqlite3.connect(self.filename)
            self.cursor = self.connection.cursor()
            self.cursor.row_factory = sqlite3.Row
            self.is_open = True
        return self.is_open
    def disconnect(self):
        if self.is_open:
            self.commit()
            self.cursor.close()
            self.is_open = False
        return not self.is_open
    def execute(self, query, tup=None):
        if not self.is_open:
            self.connect()
        if not tup:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, tup)
    def commit(self):
        if self.is_open:
            self.connection.commit()
    def lastrowid(self):
        if self.is_open:
            return self.cursor.lastrowid
        else:
            return None
    def fetchone(self):
        return self.cursor.fetchone()
    def fetchall(self):
        return self.cursor.fetchall()
    def rowcount(self):
        if self.is_open:
            return self.cursor.rowcount
        else:
            return None
