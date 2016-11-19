from base64 import b64encode
from datetime import datetime
from datetime import timezone
from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the requests routes.

class Requests_:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.encode_id = globals.encode_id

    def decode_id(self, id):
        id = self.b58.decode(id)
        if id == None: return None
        if len(id) != 1: return None
        return id[0]

    def __db_insert_request(self, data):
        with DatabaseConnection() as db:
            co, _ = db.get_table("checked_out")
            q = co.insert().\
                values(
                    item_id=data['item_id'],
                    requested_by=data['person_id'],
                    start_date=data['start_date'],
                    expected_return_date=data['end_date'])
            db.execute(q)

    def __validate_request(self, data):
        d = {}
        errs = []
        d['item_id'] = self.decode_id(data['item_id'])
        if not d['item_id']:
            errs.append('Bad item id. You trying to hack? If not, contact the webmaster')
        d['person_id'] = self.decode_id(data['person_id'])
        if not d['person_id']:
            errs.append('Bad person id. You trying to hack? If not, contact the webmaster')
        if data['start_date']:
            try:
                d['start_date'] = datetime.strptime(data['start_date'], '%m/%d/%Y')
            except ValueError:
                d['start_date'] = None
                errs.append('Invalid start date')
        else:
            d['start_date'] = None
            errs.append('Start date required')
        if data['end_date']:
            try:
                d['end_date'] = datetime.strptime(data['end_date'], '%m/%d/%Y')
            except ValueError:
                d['end_date'] = None
                errs.append('Invalid end date')
        else:
            d['end_date'] = None
        if d['start_date'] and d['end_date'] and d['start_date'] > d['end_date']:
            errs.append('End date must be after start date')
        return d, errs

    def __can_create(self, session):
        return 'is_student' in session and session['is_student']

    def new(self, request, session, inventory):
        if request.method == 'GET':
            if not self.__can_create(session): abort(403)
            hashed_id = request.args.get('id')
            if not hashed_id: abort(501)
            id = self.decode_id(hashed_id)
            data = {
                'item_id': hashed_id,
                'details': inventory.get_item_by_id(request, session, id),
                'person_id': session['hashed_person_id'],
                'person_name': session['username'],
            }
            return render_template('requests/new.html', data=data)
        abort(405)

    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session): abort(403)
            v_data, errs = self.__validate_request(request.form)
            if len(errs) > 0:
                return render_template('error.html', errors=errs)
            else:
                self.__db_insert_request(v_data)
                return "It has probably been done."
        abort(405)
