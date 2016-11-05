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
                    inv.c.id, inv.c.description, inv.c.serial_number, inv.c.make,
                    inv.c.model, inv.c.manufacturer, inv.c.location,
                    inv.c.other_notes)
            db.execute(q)
            return [ self.encode_id(dict(row), 'inventory_id') for row in db.fetchall() ]

    def __db_get_item(self, id):
        with DatabaseConnection() as db:
            inv, inv_md = db.get_table("inventory")
            q = db.query().\
                add_columns(
                    inv.c.id, inv.c.description, inv.c.serial_number, inv.c.make,
                    inv.c.model, inv.c.manufacturer, inv.c.location,
                    inv.c.other_notes).\
                filter(inv.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'inventory_id') for row in db.fetchall() ]
            if len(rows) != 1: return None
            return rows[0]

    def __db_update_item(self, id, data):
        with DatabaseConnection() as db:
            inv, inv_md = db.get_table("inventory")
            q = inv.update().\
                where(inv.c.id == id).\
                values(
                    description=data['description'], serial_number=data['serial_number'],
                    make=data['make'], model=data['model'],
                    manufacturer=data['manufacturer'],
                    location=data['location'], other_notes=data['other_notes']
                )
            db.execute(q)

    def __db_insert_item(self, data):
        with DatabaseConnection() as db:
            inv, inv_md = db.get_table("inventory")
            q = inv.insert().\
                returning(inv.c.id).\
                values(
                    description=data['description'],
                    serial_number=data['serial_number'],
                    make=data['make'],
                    model=data['model'],
                    manufacturer=data['manufacturer'],
                    location=data['location'],
                    other_notes=data['other_notes'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

    def __validate_item(self, data):
        d = {}
        errs = []
        d['description'] = data['description']
        d['serial_number'] = data['serial_number']
        d['make'] = data['make']
        d['model'] = data['model']
        d['manufacturer'] = data['manufacturer']
        if not data['location']:
            errs.append('Location is required')
        d['location'] = data['location']
        d['other_notes'] = data['other_notes']
        return d, errs

    def __create_item(self, request, session, data):
        v_data, errs = self.__validate_item(data)
        if errs:
            return render_template('inventory/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_item(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('inventory_id', id=id))

    def __can_index(self, session):
        return 'is_student' in session and session['is_student']

    def __can_show(self, session):
        return 'is_student' in session and session['is_student']

    def __can_edit(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_update(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_create(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_delete(self, session):
        return 'is_officer' in session and session['is_officer']

    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            items = self.__db_get_inventory()
            return render_template('inventory/index.html', items=items,
                can_create=self.__can_create(session),
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            item = self.__db_get_item(id)
            if item == None:
                abort(404)
            return render_template('inventory/show.html', item=item,
            can_edit=self.__can_edit(session),
            can_delete=self.__can_delete(session))
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
            if item == None: abort(404)
            self.__db_update_item(id, request.form)
            return redirect(url_for('inventory_id', id=self.b58.encode(id)))
        abort(405)

    def new(self, request, session):
        if request.method == 'GET':
            if not self.__can_create(session): abort(403)
            return render_template('inventory/new.html',
                data={}, submit_button_text='Create')
        abort(405)

    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session): abort(403)
            data = request.form
            return self.__create_item(request, session, data)
        abort(405)
