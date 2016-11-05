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

class VMs:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.encode_id = globals.encode_id
        self.sqlts_to_rel = globals.sqltimestamp_to_relative
        self.frmt_dt = globals.format_datetime
        self.dt_diff = globals.datetime_difference
        self.td_to_rel = globals.timedelta_to_relative

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

    def index(self, request, session):
        if request.method == 'GET':
            return "inside vms.index"
            """if not self.__can_index(session): abort(403)
            events = self.__db_get_events()
            events = self.__events_date_magic(events)
            return render_template('events/index.html', events=events,
                can_create=self.__can_create(session),
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))"""
        abort(405)

    def show(self, request, session, id):
        if request.method == 'GET':
            return "inside vms.show"
            """if not self.__can_show(session): abort(403)
            evt = self.__db_get_event(id)
            if not evt: abort(404)
            evt = self.__events_date_magic([evt])[0]
            return render_template('events/show.html', event=evt,
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))"""
        abort(405)

    def new(self, request, session):
        if request.method == 'GET':
            return "inside vms.new"
            """if not self.__can_create(session): abort(403)
            return render_template('events/new.html',
                data={}, submit_button_text='Create')"""
        abort(405)

    def create(self, request, session):
        if request.method == 'POST':
            return "inside vms.create"
            """if not self.__can_create(session): abort(403)
            data = request.form
            if not 'type' in data or data['type'] == 'general':
                return self.__create_generic(request, session, data)
            elif data['type'] == 'meeting':
                return self.__create_meeting(request, session, data)
            elif data['type'] == 'competition':
                return self.__create_competition(request, session, data)
            else:
                return render_template('events/new.html',
                    data=data,
                    submit_button_text='Create',
                    errors=['Didn\'t understand event type'])"""
        abort(405)

    def edit(self, request, session, id):
        if request.method == 'GET':
            return "inside vms.edit"
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
            return "inside vms.update"
            """if not self.__can_update(session): abort(403)
            data = request.form
            if not 'type' in data or data['type'] == 'general':
                return self.__update_generic(request, session, id, data)
            elif data['type'] == 'meeting':
                return self.__update_meeting(request, session, id, data)
            elif data['type'] == 'competition':
                return self.__update_competition(request, session, id, data)
            else:
                return render_template('events/new.html',
                    data=data,
                    submit_button_text='Update',
                    errors=['Didn\'t understand event type'])"""
        abort(405)

    def delete(self, request, session, id):
        if request.method == 'GET':
            return "inside vms.delete"
            """if not self.__can_delete(session): abort(403)
            self.__db_delete_competition(id)
            self.__db_delete_meeting(id)
            self.__db_delete_event(id)
            return redirect(url_for('events_'))"""

