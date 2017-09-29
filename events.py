from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from datetime import datetime, timedelta
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the events routes.


class Events:
    # Initializes the Events object to include functions from globals
	def __init__(self):
        self.b58 = globals.base58_hashids
        self.encode_id = globals.encode_id
        self.sqlts_to_rel = globals.sqltimestamp_to_relative
        self.frmt_dt = globals.format_datetime
        self.dt_diff = globals.datetime_difference
        self.td_to_rel = globals.timedelta_to_relative

	# Formats the dates and times returned from the database
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
            e['event_start_friendly'] = self.frmt_dt(start, "%d %b %Y")
            if start.hour != 0 or start.minute != 0:
                e['event_start_friendly'] += self.frmt_dt(start, " %H:%M")
            e['event_end_friendly'] = self.frmt_dt(end, "%d %b %Y")
            if end.hour != 0 or end.minute != 0:
                e['event_end_friendly'] += self.frmt_dt(end, " %H:%M")
        return events

	# Returns either all of the events in the events table, or only those
	# in the future based on the provided boolean.
    def __db_get_events(self, future_only=False):
        with DatabaseConnection() as db:
            evts, _ = db.get_table("event")
            q = db.query().\
                add_columns(
                    evts.c.id, evts.c.name, evts.c.description,
                    evts.c.start_timestamp, evts.c.end_timestamp)
            if future_only:
                now = globals.current_datetime(utc=False)
                q = q.filter(evts.c.start_timestamp > now)
            q = q.order_by(evts.c.start_timestamp)
            db.execute(q)
            events = [ self.encode_id(dict(row), 'event_id') for row in db.fetchall() ]
            return events[::-1]
	
	# Returns the details of the event with the provided ID, including any
	# meeting or competition information if applicable.
    def __db_get_event(self, id):
        with DatabaseConnection() as db:
            evts, _ = db.get_table("event")
            mts, _ = db.get_table("meeting")
            comps, _ = db.get_table("competition")
            q = db.query().\
                add_columns(
                    evts.c.id, evts.c.name, evts.c.description,
                    evts.c.start_timestamp, evts.c.end_timestamp,
                    mts.c.id, mts.c.minutes, mts.c.required,
                    comps.c.id, comps.c.documentation, comps.c.location).\
                filter(evts.c.id == id).\
                outerjoin(mts, mts.c.id == evts.c.id).\
                outerjoin(comps, comps.c.id == evts.c.id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'event_id') for row in db.fetchall() ]
            if len(rows) != 1: return None
            return rows[0]

	# Inserts an event with the provided data into the database. Returns the
	# id of the newly created event
    def __db_insert_event(self, data):
        with DatabaseConnection() as db:
            evts, _ = db.get_table("event")
            q = evts.insert().\
                returning(evts.c.id).\
                values(
                    name=data['name'],
                    description=data['description'],
                    start_timestamp=data['start_date'],
                    end_timestamp=data['end_date'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

	# Inserts a meeting with the provided data into the database.
    def __db_insert_meeting(self, data):
        with DatabaseConnection() as db:
            mts, _ = db.get_table("meeting")
            q = mts.insert().\
                values(
                    id=data['id'],
                    minutes=data['minutes'],
                    required=data['required'])
            db.execute(q)

	# Inserts a new competition with the given information.
    def __db_insert_competition(self, data):
        with DatabaseConnection() as db:
            comps, _ = db.get_table("competition")
            q = comps.insert().\
                values(
                    id=data['id'],
                    documentation=data['documentation'],
                    location=data['location'])
            db.execute(q)

	# Updates the an event with the provided data. The event
	# to update is determined by the ID of the provided information.
    def __db_update_event(self, data):
        with DatabaseConnection() as db:
            evts, _ = db.get_table("event")
            q = evts.update().\
                returning(evts.c.id).\
                where(evts.c.id == data['id']).\
                values(
                    name=data['name'],
                    description=data['description'],
                    start_timestamp=data['start_date'],
                    end_timestamp=data['end_date'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

	# Updates a meeting by deleting the meeting with the same ID
	# and replacing it with a new meeting
    def __db_update_meeting(self, data):
        self.__db_delete_meeting(data['id'])
        self.__db_insert_meeting(data)

	# Updates a competition by deleting the competition with the 
	# matching ID in the provided information and creating a new
	# competition. 
    def __db_update_competition(self, data):
        self.__db_delete_competition(data['id'])
        self.__db_insert_competition(data)

	# Deletes the event with the provided ID
    def __db_delete_event(self, id):
        with DatabaseConnection() as db:
            evts, _ = db.get_table("event")
            q = evts.delete().\
                where(evts.c.id == id)
            db.execute(q)
	# Deletes the meeting with the provided ID
    def __db_delete_meeting(self, id):
        with DatabaseConnection() as db:
            mts, _ = db.get_table("meeting")
            q = mts.delete().\
                where(mts.c.id == id)
            db.execute(q)

	# Deletes the competition with the provided ID
    def __db_delete_competition(self, id):
        with DatabaseConnection() as db:
            comps, _ = db.get_table("competition")
            q = comps.delete().\
                where(comps.c.id == id)
            db.execute(q)

	# Determines if the user can view the list of events.
    def __can_index(self, session):
        return True

	# Determines if the user can view details on any of the events
    def __can_show(self, session):
        return True

	# Determines if the user can view the edit page
    def __can_edit(self, session):
        return 'is_officer' in session and session['is_officer']

	# Determines if the user can update events
    def __can_update(self, session):
        return 'is_officer' in session and session['is_officer']
	
	# Determines if the user can create new events
    def __can_create(self, session):
        return 'is_officer' in session and session['is_officer']
	
	# Determines if the user can delete events
    def __can_delete(self, session):
        return 'is_officer' in session and session['is_officer']

	# Ensures that sufficient data is provided for a generic event.
	# This ensures that all NOTNULL contraints in the database are
	# observed before attempting to add information to the database
	# itself
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
        if 'end_date' in d and 'start_date' in d and d['end_date'] < d['start_date']:
            errs.append("End date must be after start date")
        return d, errs

	# Ensures that all required information for a meeting
	# is provided before inserting/updating the database
    def __validate_meeting(self, data):
        d, errs = self.__validate_generic(data)
        d['minutes'] = data['minutes']
        d['required'] = ('required' in data)
        return d, errs

	# Ensures that all required competition information is 
	# provided before passing the information to the database
    def __validate_competition(self, data):
        d, errs = self.__validate_generic(data)
        d['documentation'] = data['documentation']
        d['location'] = data['location']
        return d, errs

	# Validates information and inserts a generic event
    def __create_generic(self, request, session, data):
        v_data, errs = self.__validate_generic(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_event(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('events_id', id=id))
	
	# Validates and inserts a meeting 
    def __create_meeting(self, request, session, data):
        v_data, errs = self.__validate_meeting(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_event(v_data)
        if not id: abort(500)
        v_data['id'] = id
        self.__db_insert_meeting(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('events_id', id=id))

	# Validates and inserts a competition
    def __create_competition(self, request, session, data):
        v_data, errs = self.__validate_competition(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_event(v_data)
        if not id: abort(500)
        v_data['id'] = id
        self.__db_insert_competition(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('events_id', id=id))

	# Validates and updates a generic event
    def __update_generic(self, request, session, id, data):
        v_data, errs = self.__validate_generic(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_event(v_data)
        self.__db_delete_meeting(id)
        self.__db_delete_competition(id)
        id = self.b58.encode(id)
        return redirect(url_for('events_id', id=id))

	# Validates and updates a meeting
    def __update_meeting(self, request, session, id, data):
        v_data, errs = self.__validate_meeting(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_event(v_data)
        if not id: abort(500)
        self.__db_update_meeting(v_data)
        self.__db_delete_competition(id)
        id = self.b58.encode(id)
        return redirect(url_for('events_id', id=id))

	# Validates and updates a competition.
    def __update_competition(self, request, session, id, data):
        v_data, errs = self.__validate_competition(data)
        if errs:
            return render_template('events/new.html', data=data,
                errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_event(v_data)
        if not id: abort(500)
        self.__db_update_competition(v_data)
        self.__db_delete_meeting(id)
        id = self.b58.encode(id)
        return redirect(url_for('events_id', id=id))

	# Checks user permissions and then returns all future events 
    def future_events(self, request, session):
        if not self.__can_index(session): abort(403)
        events = self.__db_get_events(future_only=True)
        events = self.__events_date_magic(events)
        return events

	# Checks user permissions and then returns a rendered index
	# page with all of the events listed
    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            events = self.__db_get_events()
            events = self.__events_date_magic(events)
            return render_template('events/index.html', events=events,
                can_create=self.__can_create(session),
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session),
                now=globals.current_datetime(utc=False))
        abort(405)
	
	# Checks user permissions and then returns a rendered page 
	# with the details of the specified event
    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            evt = self.__db_get_event(id)
            if not evt: abort(404)
            evt = self.__events_date_magic([evt])[0]
            return render_template('events/show.html', event=evt,
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

	# Renders the events test page
    def test(self, request, session):
        if request.method == 'GET':
            return render_template('events/test.html')
        abort(405)
	
	# Checks permissions then returns the page to insert
	# event information
    def new(self, request, session):
        if request.method == 'GET':
            if not self.__can_create(session): abort(403)
            return render_template('events/new.html',
                data={}, submit_button_text='Create')
        abort(405)
	# Checks permissions then creates a new event from the
	# provided information
    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session): abort(403)
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
                    errors=['Didn\'t understand event type'])
        abort(405)

	# Checks permissions then returns a page to insert event information
	# with the information of the provided event already filled out.
    def edit(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_edit(session): abort(403)
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
                submit_button_text='Update')
        abort(405)

	# Checks for proper permissions then updates the specified event
	# with the provided information
    def update(self, request, session, id):
        if request.method == 'POST':
            if not self.__can_update(session): abort(403)
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
                    errors=['Didn\'t understand event type'])
        abort(405)

	# Checks the users permissions then deletes the specified event
    def delete(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_delete(session): abort(403)
            self.__db_delete_competition(id)
            self.__db_delete_meeting(id)
            self.__db_delete_event(id)
            return redirect(url_for('events_'))
