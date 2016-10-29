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

    def __db_get_inventory(self):
        with DatabaseConnection() as db:
            inv, inv_md = db.get_table("inventory")
            q = db.query().\
                add_columns(
                    inv.c.id, inv.c.name, inv.c.serial_number, inv.c.make,
                    inv.c.model, inv.c.manufacturer, inv.c.location,
                    inv.c.other_notes)
            db.execute(q)
            return [ self.encode_id(dict(row), 'inventory_id') for row in db.fetchall() ]

    def __db_get_item(self, id):
        with DatabaseConnection() as db:
            inv, inv_md = db.get_table("inventory")
            q = db.query().\
                add_columns(
                    inv.c.id, inv.c.name, inv.c.serial_number, inv.c.make,
                    inv.c.model, inv.c.manufacturer, inv.c.location,
                    inv.c.other_notes).\
                filter(inv.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'inventory_id') for row in db.fetchall() ]
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

    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            item = self.__db_get_item(id)
            if not item:
                abort(404)
            return render_template('inventory/show.html', item=item,
            can_edit=self.__can_edit(session))
        abort(405)

    def edit(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_edit(session): abort(403)
            item = self.__db_get_item(id)
            if not item: abort(404)
            return render_template('inventory/edit.html', item=item)
        abort(405)

    def update(self, request, session, id):
        if request.method == 'POST':
            if not self.__can_update(session): abort(403)
            item = self.__db_get_item(id)
            if not item: abort(404)
            print(dict(request.form))
            print(dict(request.args))
            return str(dict(request.form))
        abort(405)
