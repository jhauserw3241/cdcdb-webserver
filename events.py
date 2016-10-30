from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from datetime import datetime, timedelta
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the inventory routes.

class Events:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.encode_id = globals.encode_id
        self.sqlts_to_rel = globals.sqltimestamp_to_relative
        self.frmt_dt = globals.format_datetime
        self.dt_diff = globals.datetime_difference
        self.td_to_rel = globals.timedelta_to_relative

    def __events_date_magic(self, events):
        for e in events:
            start = e['event_start_timestamp']
            end = e['event_end_timestamp']
            duration = self.dt_diff(start, end)
            if duration == timedelta():
                duration = ""
            else:
                duration = self.td_to_rel(duration)
            e['relative_start'] = self.sqlts_to_rel(str(start))
            e['relative_end'] = self.sqlts_to_rel(str(end))
            e['duration'] = duration
            e['event_start_timestamp'] = self.frmt_dt(start, "%c")
            e['event_end_timestamp'] = self.frmt_dt(end, "%c")
        return events

    def __db_get_events(self, future_only=False):
        with DatabaseConnection() as db:
            evts, evts_md = db.get_table("event")
            q = db.query().\
                add_columns(
                    evts.c.id, evts.c.name, evts.c.description,
                    evts.c.start_timestamp, evts.c.end_timestamp)
            if future_only:
                now = datetime.utcnow()
                q = q.filter(evts.c.start_timestamp > now)
            q = q.order_by(evts.c.start_timestamp)
            db.execute(q)
            events = [ self.encode_id(dict(row), 'event_id') for row in db.fetchall() ]
            events = self.__events_date_magic(events)
            return events[::-1]

    def __db_get_event(self, id):
        with DatabaseConnection() as db:
            evts, evts_md = db.get_table("event")
            q = db.query().\
                add_columns(
                    evts.c.id, evts.c.name, evts.c.description,
                    evts.c.start_timestamp, evts.c.end_timestamp).\
                filter(evts.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'event_id') for row in db.fetchall() ]
            if len(rows) != 1: return None
            return rows[0]

    def __can_index(self, session):
        return True

    def __can_show(self, session):
        return True

    def __can_edit(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_create(self, session):
        return 'is_officer' in session and session['is_officer']

    def __validate_generic(self, data):
        # parse and validate *data* into *d* while also
        # listing any errors in *errs*
        errs = []
        d = {}
        if not data['name']:
            errs.append('Name is required')
        d['name'] = data['name']
        d['description'] = data['description']
        # start date is required
        # store start date and start time in d['start_date']
        try:
            d['start_date'] = datetime.strptime(data['start_date'], '%m/%d/%Y')
        except ValueError:
            errs.append("Invalid start date")
        else:
            # start time is optional. If unset, assume 00:00
            # If set, it must validate.
            if data['start_time']:
                try:
                    start_time = datetime.strptime(data['start_time'],'%H:%M')
                except ValueError:
                    errs.append("Invalid start time")
                else:
                    d['start_date'] = d['start_date'] + timedelta(hours=start_time.hour)
                    d['start_date'] = d['start_date'] + timedelta(minutes=start_time.minute)
        # end date is optional. If unset, set to start date
        # If set, it must validate
        # store end date and end time in d['end_date']
        if data['end_date']:
            try:
                d['end_date'] = datetime.strptime(data['end_date'], '%m/%d/%Y')
            except ValueError:
                errs.append("Invalid end date")
            else:
                # end date is optional. If unset, assume 00:00
                # If set, it must validate
                if data['end_time']:
                    try:
                        end_time= datetime.strptime(data['end_time'],'%H:%M')
                    except ValueError:
                        errs.append("Invalid end time")
                    else:
                        d['end_date'] = d['end_date'] + timedelta(hours=end_time.hour)
                        d['end_date'] = d['end_date'] + timedelta(minutes=end_time.minute)
        else:
            if 'start_date' in d:
                d['end_date'] = d['start_date']
        return d, errs

    def __validate_meeting(self, data):
        d, errs = self.__validate_generic(data)
        d['minutes'] = data['minutes']
        d['required'] = ('required' in data)
        return d, errs

    def __validate_competition(self, data):
        d, errs = self.__validate_generic(data)
        d['documentation'] = data['documentation']
        d['location'] = data['location']
        return d, errs

    def __create_generic(self, request, session, data):
        v_data, errs = self.__validate_generic(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs)
        return "Done (generic) {}".format(v_data)


    def __create_meeting(self, request, session, data):
        v_data, errs = self.__validate_meeting(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs)
        return "Done (meeting) {}".format(v_data)

    def __create_competition(self, request, session, data):
        v_data, errs = self.__validate_competition(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs)
        return "Done (competition) {}".format(v_data)

    def future_events(self, request, session):
        if not self.__can_index(session): abort(403)
        return self.__db_get_events(future_only=True)

    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            events = self.__db_get_events()
            return render_template('events/index.html', events=events,
                can_create=self.__can_create(session))
        abort(405)

    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            evt = self.__db_get_event(id)
            return render_template('events/show.html', event=evt,
                can_edit=self.__can_edit(session))
        abort(405)

    def new(self, request, session):
        if request.method == 'GET':
            if not self.__can_create(session): abort(403)
            return render_template('events/new.html', data={})
        abort(405)

    def create(self, request, session):
        if request.method == 'POST':
            data = request.form
            if not 'type' in data:
                return self.__create_generic(request, session, data)
            elif data['type'] == 'meeting':
                return self.__create_meeting(request, session, data)
            elif data['type'] == 'competition':
                return self.__create_competition(request, session, data)
            else:
                return render_template('events/new.html', data=data,
                errors=['Didn\'t understand event type'])
        abort(405)
