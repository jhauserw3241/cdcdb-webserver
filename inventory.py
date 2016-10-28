from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the inventory routes.

class Inventory:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.encode_id = globals.encode_id

    def __db_get_table(self, db):
        i, _ = db.get_table("inventory")
        return i

    def __db_get_inventory(self):
        with DatabaseConnection() as db:
            inv = self.__db_get_table(db)
            db.select([inv])
            return [ self.encode_id(dict(row)) for row in db.fetchall() ]

    def __db_get_item(self, id):
        with DatabaseConnection() as db:
            inv = self.__db_get_table(db)
            db.select([inv], inv.c.id == id)
            rows = [ self.encode_id(dict(row)) for row in db.fetchall() ]
            if len(rows) != 1:
                return None
            return rows[0]

    def __can_index(self, session):
        return 'is_student' in session and session['is_student']

    def __can_show(self, session):
        return 'is_student' in session and session['is_student']

    def __can_edit(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_update(self, session):
        return 'is_officer' in session and session['is_officer']

    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            items = self.__db_get_inventory()
            return render_template('inventory/index.html', items=items)
        abort(405)
        abort(405)
