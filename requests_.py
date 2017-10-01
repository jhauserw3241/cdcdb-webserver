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
        self.frmt_dt = globals.format_datetime

    def decode_id(self, id):
        id = self.b58.decode(id)
        if id == None:
            return None
        if len(id) != 1:
            return None
        return id[0]

    # Do magic with the given list of requests
    # It adds a few attributes for handy human-readable formats
    def __requests_date_magic(self, requests):
        for r in requests:
            start = r['checked_out_start_date']
            e_end = r['checked_out_expected_return_date']
            a_end = r['checked_out_actual_return_date']
            if start:
                r['start_friendly'] = self.frmt_dt(start, '%d %b %Y')
            else:
                r['start_friendly'] = 'Unknown'
            if e_end:
                r['expected_end_friendly'] = self.frmt_dt(e_end, '%d %b %Y')
            else:
                r['expected_end_friendly'] = 'Unknown'
            if a_end:
                r['actual_end_friendly'] = self.frmt_dt(a_end, '%d %b %Y')
            else:
                r['actual_end_friendly'] = 'Unknown'
        return requests

    # add a new request
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

    # get all requests, optionally only the ones that haven't been approved
    def __db_get_requests(self, only_open=False):
        with DatabaseConnection() as db:
            co, _ = db.get_table("checked_out")
            inv, _ = db.get_table("inventory")
            ppl, _ = db.get_table("people_read")
            q = db.query().\
                add_columns(co).\
                add_columns(inv).\
                add_columns(ppl.c.full_name, ppl.c.id).\
                join(inv, inv.c.id == co.c.item_id).\
                join(ppl, ppl.c.id == co.c.requested_by)
            if only_open:
                q = q.filter(co.c.approved_by == None)
            db.execute(q)
            rows = [dict(r) for r in db.fetchall()]
            for r in rows:
                self.encode_id(r, 'checked_out_id')
                self.encode_id(r, 'checked_out_item_id')
                if r['checked_out_approved_by'] != None:
                    self.encode_id(r, 'checked_out_approved_by')
                self.encode_id(r, 'checked_out_requested_by')
            return rows

    # get the request with the given id
    def __db_get_request(self, id):
        with DatabaseConnection() as db:
            co, _ = db.get_table("checked_out")
            inv, _ = db.get_table("inventory")
            ppl, _ = db.get_table("people_read")
            q = db.query().\
                add_columns(co).\
                add_columns(inv).\
                add_columns(ppl.c.full_name, ppl.c.id).\
                join(inv, inv.c.id == co.c.item_id).\
                join(ppl, ppl.c.id == co.c.requested_by).\
                filter(co.c.id == id)
            db.execute(q)
            rows = [dict(r) for r in db.fetchall()]
            for r in rows:
                self.encode_id(r, 'checked_out_id')
                self.encode_id(r, 'checked_out_item_id')
                if r['checked_out_approved_by'] != None:
                    self.encode_id(r, 'checked_out_approved_by')
                self.encode_id(r, 'checked_out_requested_by')
            if len(rows) != 1:
                return None
            return rows[0]

    # approve a request by attached the officer's id
    def __db_approve(self, id, approver):
        with DatabaseConnection() as db:
            co, _ = db.get_table("checked_out")
            q = co.update().\
                where(co.c.id == id).\
                values(approved_by=approver)
            db.execute(q)
            return

    # disapprove or just remove a request by deleting the row
    def __db_delete(self, id):
        with DatabaseConnection() as db:
            co, _ = db.get_table("checked_out")
            q = co.delete().where(co.c.id == id)
            db.execute(q)
            return

    # parse the request and return any errors
    def __validate_request(self, data):
        d = {}
        errs = []
        d['item_id'] = self.decode_id(data['item_id'])
        if not d['item_id']:
            errs.append(
                'Bad item id. You trying to hack? If not, contact the webmaster')
        d['person_id'] = self.decode_id(data['person_id'])
        if not d['person_id']:
            errs.append(
                'Bad person id. You trying to hack? If not, contact the webmaster')
        if data['start_date']:
            try:
                d['start_date'] = datetime.strptime(
                    data['start_date'], '%m/%d/%Y')
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

    #####
    # PERMISSIONS CHECKS
    #####

    def __can_index(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_create(self, session):
        return 'is_student' in session and session['is_student']

    def __can_approve(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_delete(self, session):
        return 'is_officer' in session and session['is_officer']

    def __needs_approval(self, id):
        req = self.__db_get_request(id)
        if not req:
            return False
        if 'checked_out_approved_by' in req and req['checked_out_approved_by']:
            return False
        return True

    # Router calls this to return new request form
    def new(self, request, session, inventory):
        if request.method == 'GET':
            if not self.__can_create(session):
                abort(403)
            hashed_id = request.args.get('id')
            if not hashed_id:
                abort(501)
            id = self.decode_id(hashed_id)
            if not inventory.is_item_available(request, session, id):
                return render_template('error.html',
                                       errors=['This item is not available.'])
            data = {
                'item_id': hashed_id,
                'details': inventory.get_item_by_id(request, session, id),
                'person_id': session['hashed_person_id'],
                'person_name': session['username'],
            }
            return render_template('requests/new.html', data=data)
        abort(405)

    # Router calls this to process new request form
    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session):
                abort(403)
            v_data, errs = self.__validate_request(request.form)
            if len(errs) > 0:
                return render_template('error.html', errors=errs)
            else:
                self.__db_insert_request(v_data)
                return redirect(url_for('requests__'))
        abort(405)

    # Router calls this to show all requests
    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session):
                abort(403)
            open_requests = self.__db_get_requests(only_open=True)
            open_requests = self.__requests_date_magic(open_requests)
            return render_template('requests/index.html', requests=open_requests)
        abort(405)

    # Router calls this to approve an existing request
    def approve(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_approve(session):
                abort(403)
            if not self.__needs_approval(id):
                abort(403)
            approver = session['person_id']
            self.__db_approve(id, approver)
            return redirect(url_for('requests__'))
        abort(405)

    # Router calls this to disapprove or otherwise remove an existing request
    def delete(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_delete(session):
                abort(403)
            self.__db_delete(id)
            return redirect(url_for('requests__'))
        abort(405)
