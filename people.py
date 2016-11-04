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

# Handles the people routes. Also has the job of logging in/out and registering

class People:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.check_password = globals.check_password
        self.convert_datetime = globals.sqltimestamp_to_relative
        self.hash_password = globals.hash_password
        self.encode_id = globals.encode_id

    def __db_get_people(self, limit):
        with DatabaseConnection() as db:
            current_year = globals.current_datetime("%Y")
            ppl, ppl_md = db.get_table("people")
            studs, studs_md = db.get_table("students")
            pos, pos_md = db.get_table("position")
            q = db.query().\
                add_columns(ppl.c.id, ppl.c.first_name, ppl.c.last_name).\
                add_columns(ppl.c.company, ppl.c.email).\
                add_columns(studs.c.major, studs.c.year).\
                add_columns(pos.c.title)
            if limit == 'officers':
                q = q.outerjoin(studs, studs.c.id == ppl.c.id).\
                    join(pos,
                        (pos.c.id == ppl.c.id) &
                        (pos.c.year == current_year)
                    )
            else:
                q = q.outerjoin(studs, studs.c.id == ppl.c.id).\
                    outerjoin(pos,
                        (pos.c.id == ppl.c.id) &
                        (pos.c.year == current_year)
                    )
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'people_id') for row in
                db.fetchall() ]
            return rows

    def __db_get_person(self, id):
        with DatabaseConnection() as db:
            current_year = globals.current_datetime("%Y")
            ppl, ppl_md = db.get_table("people")
            studs, studs_md = db.get_table("students")
            pos, pos_md = db.get_table("position")
            q = db.query().\
                add_columns(ppl.c.id, ppl.c.first_name, ppl.c.last_name).\
                add_columns(ppl.c.company, ppl.c.email).\
                add_columns(studs.c.id, studs.c.eid).\
                add_columns(studs.c.major, studs.c.year).\
                add_columns(studs.c.voting_member).\
                add_columns(pos.c.title).\
                outerjoin(studs, studs.c.id == ppl.c.id).\
                outerjoin(pos,
                    (pos.c.id == ppl.c.id) &
                    (pos.c.year == current_year)
                ).\
                filter(ppl.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'people_id') for row in
                db.fetchall() ]
            if len(rows) != 1:
                return None
            return rows[0]

    def __db_insert_person(self, data):
        with DatabaseConnection() as db:
            ppl, ppl_md = db.get_table("people")
            q = ppl.insert().\
                returning(ppl.c.id).\
                values(
                    first_name=data['fname'],
                    last_name=data['lname'],
                    company=data['company'],
                    email=data['email'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

    def __db_insert_student(self, data):
        with DatabaseConnection() as db:
            std, std_md = db.get_table("students")
            q = std.insert().\
                values(
                    id=data['id'],
                    eid=data['eid'],
                    year=data['year'],
                    major=data['major'],
                    voting_member=data['voting_member'])
            db.execute(q)

    def __db_update_person(self, data):
        with DatabaseConnection() as db:
            ppl, ppl_md = db.get_table("people")
            q = ppl.update().\
                returning(ppl.c.id).\
                where(ppl.c.id == data['id']).\
                values(
                    first_name=data['fname'],
                    last_name=data['lname'],
                    company=data['company'],
                    email=data['email'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

    def __db_update_student(self, data):
        self.__db_delete_student(data['id'])
        self.__db_insert_student(data)

    def __db_delete_person(self, id):
        with DatabaseConnection() as db:
            ppl, ppl_md = db.get_table("people")
            q = ppl.delete().\
                where(ppl.c.id == id)
            db.execute(q)

    def __db_delete_student(self, id):
        with DatabaseConnection() as db:
            stud, stud_md = db.get_table("students")
            q = stud.delete().\
                where(stud.c.id == id)
            db.execute(q)

    def __validate_generic(self, data):
        # parse and validate *data* into *d* while also
        # listing any errors in *errs*
        errs = []
        d = {}
        if not data['fname']:
            errs.append('First name is required')
        d['fname'] = data['fname']
        d['lname'] = data['lname']
        d['company'] = data['company']
        if not data['email']:
            errs.append('Email is required')
        d['email'] = data['email']
        return d, errs

    def __validate_student(self, data):
        d, errs = self.__validate_generic(data)
        if not data['eid']:
            errs.append('EID is required')
        d['eid'] = data['eid']
        d['year'] = data['year'] if data['year'] else 'Unknown'
        if not data['major']:
            errs.append('major is required')
        d['major'] = data['major']
        d['voting_member'] = 'voting_member' in data
        return d, errs

    def __create_generic(self, request, session, data):
        v_data, errs = self.__validate_generic(data)
        if errs:
            return render_template('people/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_person(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('people_id', id=id))

    def __create_student(self, request, session, data):
        v_data, errs = self.__validate_student(data)
        if errs:
            return render_template('people/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_person(v_data)
        if not id: abort(500)
        v_data['id'] = id
        self.__db_insert_student(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('people_id', id=id))

    def __update_generic(self, request, session, id, data):
        v_data, errs = self.__validate_generic(data)
        if errs:
            return render_template('people/new.html', data=data,
                errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_person(v_data)
        self.__db_delete_student(id)
        id = self.b58.encode(id)
        return redirect(url_for('people_id', id=id))

    def __update_student(self, request, session, id, data):
        v_data, errs = self.__validate_student(data)
        if errs:
            return render_template('people/new.html', data=data,
                errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_person(v_data)
        if not id: abort(500)
        self.__db_update_student(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('people_id', id=id))

    def __can_index(self, session, limit):
        if limit == 'officers':
            return True
        else:
            return 'is_officer' in session and session['is_officer']

    def __can_show(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_create(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_edit(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_delete(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_update(self, session):
        return 'is_officer' in session and session['is_officer']

    def login(self, request, session):
        if request.method == 'GET':
            if 'person_id' not in session:
                return render_template('people/login.html')
            else:
                return redirect(url_for('index_'))
        elif request.method == 'POST':
            u = request.form['username']
            p = request.form['password']
            if u == "root" and p == "root":
                session['username'] = u
                session['person_id'] = 1
                session['hashed_person_id'] = self.b58.encode(session['person_id'])
                session['is_admin'] = True if True else False
                session['is_officer'] = True if True else False
                session['is_student'] = True if True else False
                return redirect(url_for('index_'))
            elif u == "admin" and p == "admin":
                session['username'] = u
                session['person_id'] = 2
                session['hashed_person_id'] = self.b58.encode(session['person_id'])
                session['is_admin'] = True if True else False
                session['is_officer'] = False if True else False
                session['is_student'] = True if True else False
                return redirect(url_for('index_'))
            elif u == "officer" and p == "officer":
                session['username'] = u
                session['person_id'] = 3
                session['hashed_person_id'] = self.b58.encode(session['person_id'])
                session['is_admin'] = False if True else False
                session['is_officer'] = True if True else False
                session['is_student'] = True if True else False
                return redirect(url_for('index_'))
            elif u == "student" and p == "student":
                session['username'] = u
                session['person_id'] = 4
                session['hashed_person_id'] = self.b58.encode(session['person_id'])
                session['is_admin'] = False if True else False
                session['is_officer'] = False if True else False
                session['is_student'] = True if True else False
                return redirect(url_for('index_'))
        abort(405)

    def logout(self, request, session):
        if request.method == 'GET':
            if session:
                session.pop('username', None)
                session.pop('person_id', None)
                session.pop('hashed_person_id', None)
                session.pop('is_admin', None)
                session.pop('is_officer', None)
                session.pop('is_student', None)
            return redirect(url_for('people_login'))
        abort(405)

    def index(self, request, session):
        if request.method == 'GET':
            if request.args and request.args['limit']:
                limit = request.args['limit']
            else:
                limit = None
            if not self.__can_index(session, limit): abort(403)
            ppl = self.__db_get_people(limit)
            ppl = [ globals.decode_year(r, 'students_year') for r in ppl ]
            ppl = [ globals.decode_major(r, 'students_major') for r in ppl ]
            return render_template('people/index.html', people=ppl,
            can_create=self.__can_create(session),
            can_edit=self.__can_edit(session),
            can_delete=self.__can_delete(session))
        abort(405)

    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            person = self.__db_get_person(id)
            if person == None: abort(404)
            person = globals.decode_year(person, 'students_year')
            person = globals.decode_major(person, 'students_major')
            return render_template('people/show.html', person=person,
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

    def new(self, request, session):
        if request.method == 'GET':
            if not self.__can_create(session): abort(403)
            return render_template('people/new.html',
                data={}, submit_button_text='Create')
        abort(405)

    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session): abort(403)
            data = request.form
            if not 'type' in data or data['type'] == 'general':
                return self.__create_generic(request, session, data)
            elif data['type'] == 'student':
                return self.__create_student(request, session, data)
            else:
                return render_template('people/new.html',
                    data=data,
                    submit_button_text='Create',
                    errors=['Didn\'t understand person type'])
        abort(405)

    def edit(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_edit(session): abort(403)
            prsn = self.__db_get_person(id)
            data = {}
            data['fname'] = prsn['people_first_name']
            data['lname'] = prsn['people_last_name']
            data['company'] = prsn['people_company'] if prsn['people_company'] else ''
            data['email'] = prsn['people_email']
            if prsn['students_id']: data['type'] = 'student'
            else: data['type'] = 'general'
            data['eid'] = prsn['students_eid'] if prsn['students_eid'] else ''
            data['year'] = prsn['students_year']
            data['major'] = prsn['students_major'] if prsn['students_major'] else ''
            data['voting_member'] = prsn['students_voting_member']
            return render_template('people/new.html', data=data,
                submit_button_text='Update')
            pass
        abort(405)

    def update(self, request, session, id):
        if request.method == 'POST':
            if not self.__can_update(session): abort(403)
            data = request.form
            if not 'type' in data or data['type'] == 'general':
                return self.__update_generic(request, session, id, data)
            elif data['type'] == 'student':
                return self.__update_student(request, session, id, data)
            else:
                return render_template('people/new.html',
                    data=data,
                    submit_button_text='Update',
                    errors=['Didn\'t understand event type'])

    def delete(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_delete(session): abort(403)
            self.__db_delete_student(id)
            self.__db_delete_person(id)
            return redirect(url_for('people_'))
