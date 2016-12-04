from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from datetime import datetime, timedelta
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the positions routes.

class Positions:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.encode_id = globals.encode_id

    def __can_index(self, session):
        return True

    def __can_show(self, session):
        return True

    def __can_edit(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_update(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_create(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_delete(self, session):
        return 'is_officer' in session and session['is_officer']

    def __db_get_positions(self):
        with DatabaseConnection() as db:
            positions, _ = db.get_table("position")
            q = db.query().\
                add_columns(
                    positions.c.pos_id, positions.c.person_id, positions.c.title,
                    positions.c.start_date, positions.c.end_date)
            db.execute(q)
            positions = [ self.encode_id(dict(row), 'position_id') for row in db.fetchall() ]
            return positions[::-1]

    def __db_get_position(self, data):
        with DatabaseConnection() as db:
            positions, _ = db.get_table("position")
            q = db.query().\
                add_columns(
                    positions.c.pos_id, positions.c.person_id, positions.c.title,
                    positions.c.start_date, positions.c.end_date).\
                filter(positions.c.pos_id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'position_id') for row in db.fetchall() ]
            if len(rows) != 1: return None
            return rows[0]

    def __db_insert_position(self, data):
        with DatabaseConnection() as db:
            positions, _ = db.get_table("position")
            q = positions.insert().\
                returning(positions.c.pos_id).\
                values(
                    person_id=data['person_id'], 
                    title=data['title'],
                    start_date=data['start_date'], 
                    end_date=data['end_date'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

    def __db_update_position(self, data):
        self.__db_delete_position(data['id'])
        self.__db_insert_position(data)

    def __db_delete_position(self, id):
        with DatabaseConnection() as db:
            positions, _ = db.get_table("position")
            q = positions.delete().\
                where(positions.c.pos_id == id)
            db.execute(q)

    def __validate_position(self, data):
        errs = []
        d = {}
        if not data['pos_id']:
            errs.append('pos_id is required')
        d['pos_id'] = data['pos_id']
        if not data['person_id']:
            errs.append('person_id is required')
        d['person_id'] = data['person_id']
        if not data['title']:
            errs.append('title is required')
        d['title'] = data['title']
        if not data['start_date']
            errs.append('start_date is required')
        d['start_date'] = data['start_date']
        s['end_date'] = data['end_date']
        if errs:
            return render_template('presentations/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_presenation(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('presentation_id', id=id))

    def __update_presentation(self, request, session, id, data):
        v_data, errs = self.__validate_vm(data)
        if errs:
            return render_template('presentations/new.html', data=data,
                errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_presentation(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('presentation_id', id=id))


    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            """presentations = self.__db_get_presentations()
            return render_template('presentations/index.html', presentations=presentations,
                can_create=self.__can_create(session),
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))"""
            return "You are in positions.index"
        abort(405)

    def new(self, request, session):
        if request.method == 'GET':
            return "You are in positions.new"
            """"if not self.__can_create(session): abort(403)
            return render_template('presentations/new.html',
                data={}, submit_button_text='Create')"""
        abort(405)

    def create(self, request, session):
        if request.method == 'POST':
            return "You are in positions.create"
            """if not self.__can_create(session): abort(403)
            data = request.form
            return self.__create_presentation(request, session, data)"""
        abort(405)

    def edit(self, request, session, id):
        if request.method == 'GET':
            return "inside positions.edit"
            """if not self.__can_edit(session): abort(403)
            evt = self.__db_get_event(id)
            data = {}
            data['name'] = evt['event_name']
            data['description'] = evt['event_description']
            data['start_date'] = self.frmt_dt(evt['event_start_timestamp'], '%m/%d/%Y')
            data['start_time'] = self.frmt_dt(evt['event_start_timestamp'], '%H:%M')
            data['end_date'] = self.frmt_dt(evt['event_end_timestamp'], '%m/%d/%Y')
            data['end_time'] = self.frmt_dt(evt['event_end_timestamp'], '%H:%M')
            if evt['meeting_id'] and evt['competition_id']:
                raise Exception('This is event is f\'ed up: both a meeting and competition')
            if evt['meeting_id']: data['type'] = 'meeting'
            elif evt['competition_id']: data['type'] = 'competition'
            else: data['type'] = "general"
            data['minutes'] = evt['meeting_minutes'] if evt['meeting_minutes'] else ''
            data['required'] = evt['meeting_required']
            data['documentation'] = evt['competition_documentation'] if\
                evt['competition_documentation'] else ''
            data['location'] = evt['competition_location'] if\
                evt['competition_location'] else ''
            print(evt)
            return render_template('events/new.html', data=data,
                submit_button_text='Update')"""
        abort(405)

    def update(self, request, session, id):
        if request.method == 'POST':
            if not self.__can_update(session): abort(403)
            return "You are in position.update"
            #data = request.form
            #return self.__update_presentation(request, session, id, data)
        abort(405)

    """def delete(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_delete(session): abort(403)
            self.__db_delete_presentation(id)
            return redirect(url_for('events_'))"""
