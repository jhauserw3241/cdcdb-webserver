from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from datetime import datetime, timedelta
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the VMs routes.

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

    def __db_get_presentations(self):
        with DatabaseConnection() as db:
            presentations, _ = db.get_table("presentations")
            q = db.query().\
                add_columns(
                    vms.c.id, vms.c.owner_id, vms.c.name,
                    vms.c.network, vms.c.role)
            db.execute(q)
            presentations = [ self.encode_id(dict(row), 'presentation_id') for row in db.fetchall() ]
            return presentations[::-1]

    def __db_get_presentation(self, data):
        with DatabaseConnection() as db:
            presentations, _ = db.get_table("presentations")
            q = db.query().\
                add_columns(
                    vms.c.id, vms.c.owner_id, vms.c.name,
                    vms.c.network, vms.c.role).\
                filter(presentations.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'presentation_id') for row in db.fetchall() ]
            if len(rows) != 1: return None
            return rows[0]

    def __db_insert_presentation(self, data):
        with DatabaseConnection() as db:
            presentations, _ = db.get_table("presentations")
            q = presentations.insert().\
                returning(presentations.c.id).\
                values(
                    owner_id=data['owner_id'],
                    name=data['name'],
                    network=data['network'],
                    role=data['role'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

    def __db_update_presentation(self, data):
        self.__db_delete_presentation(data['id'])
        self.__db_insert_presentation(data)

    def __db_delete_presentation(self, id):
        with DatabaseConnection() as db:
            presentations, _ = db.get_table("presentations")
            q = presentations.delete().\
                where(presentations.c.id == id)
            db.execute(q)

    def __validate_presentation(self, data):
        errs = []
        d = {}
        if not data['owner_id']:
            errs.append('Owner_id is required')
        d['owner_id'] = data['owner_id']
        d['name'] = data['name']
        d['network'] = data['network']
        d['role'] = data['role']

    def __create_presentation(self, request, session, data):
        v_data, errs = self.__validate_vm(data)
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
