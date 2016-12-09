from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from datetime import datetime, timedelta
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the Presentations routes.

class Presentations:
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
            presentations, _ = db.get_table("presentation")
            pres_pers,_ = db.get_table("presenters")
            people,_ = db.get_table("people_read")
            q = db.query().\
                add_columns(
                    presentations.c.id, presentations.c.name,
                    presentations.c.slides, pres_pers.c.person_id, people.c.full_name).\
                outerjoin(pres_pers, pres_pers.c.presentation_id == presentations.c.id).\
                outerjoin(people, people.c.id == pres_pers.c.person_id)
            db.execute(q)
            presentations = [ self.encode_id(dict(row), 'presentation_id') for row in db.fetchall() ]
            return presentations[::-1]

    def __db_get_presentation(self, data):
        with DatabaseConnection() as db:
            presentations, _ = db.get_table("presentation")
            q = db.query().\
                add_columns(
                    presentations.c.id, presentations.c.name,
                    presentations.c.slides).\
                filter(presentations.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'presentation_id') for row in db.fetchall() ]
            if len(rows) != 1: return None
            return rows[0]

    def __db_insert_presentation(self, data):
        with DatabaseConnection() as db:
            presentations, _ = db.get_table("presentation")
            q = presentations.insert().\
                returning(presentations.c.id).\
                values(
                    name=data['name'],
                    slides=data['slides'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else:
                pres_pers,_ = db.get_table("presenters")
                q = pres_pers.insert().\
                    returning(pres_pers.c.presentation_id).\
                    values(
                        presentation_id=data[lastrowid[0]],
                        person_id=data['presenter_id']
                    )
                return lastrowid[0]
                
    def __db_update_presentation(self, data):
        self.__db_delete_presentation(data['id'])
        self.__db_insert_presentation(data)

    def __db_delete_presentation(self, id):
        with DatabaseConnection() as db:
            presentations, _ = db.get_table("presentation")
            q = presentations.delete().\
                where(presentations.c.id == id)
            db.execute(q)

    def __validate_presentation(self, data):
        errs = []
        d = {}
        d['name'] = data['name']
        d['slides'] = data['slides']
        d['presenter_id'] = data['presenter_id']
        return d,errs

    def __create_presentation(self, request, session, data):
        v_data, errs = self.__validate_presentation(data)
        if errs:
            return render_template('presentations/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_presentation(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('presentations_id', id=id))

    def __update_presentation(self, request, session, id, data):
        v_data, errs = self.__validate_presentation(data)
        if errs:
            return render_template('presentations/new.html', data=data,
                errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_presentation(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('presentations_id', id=id))


    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            presentations = self.__db_get_presentations()
            return render_template('presentations/index.html', presentations=presentations,
                can_create=self.__can_create(session),
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            presentation = self.__db_get_presentation(id)
            if not presentation: abort(404)
            return render_template('presentations/show.html', presentation=presentation,
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

    def new(self, request, session):
        if request.method == 'GET':
            if not self.__can_create(session): abort(403)
            return render_template('presentations/new.html',
                data={}, submit_button_text='Create')
        abort(405)

    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session): abort(403)
            data = request.form
            return self.__create_presentation(request, session, data)
        abort(405)

    def edit(self, request, session, id):
        if request.method == 'GET':
            return "inside presentations.edit"
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
            data = request.form
            return self.__update_presentation(request, session, id, data)
        abort(405)

    def delete(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_delete(session): abort(403)
            self.__db_delete_presentation(id)
            return redirect(url_for('events_'))

