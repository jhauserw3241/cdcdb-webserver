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

    def __db_get_others(self):
        with DatabaseConnection() as db:
            others, _ = db.get_table("not_students")
            q = db.query().add_columns(others)
            db.execute(q)
            rows = [ self.encode_id(dict(r), 'not_students_id') for r in
                db.fetchall() ]
            return rows

    def __db_get_officers(self, current_only=False):
        with DatabaseConnection() as db:
            offs, _ = db.get_table("officers") if current_only else \
                db.get_table("all_officers")
            q = db.query().add_columns(offs)
            db.execute(q)
            rows = [ self.encode_id(dict(r), 'officers_id') for r in
                db.fetchall() ]
            return rows

    def __db_get_students(self, are_voting=False):
        with DatabaseConnection() as db:
            not_offs, _ = db.get_table("not_officers")
            studs, _ = db.get_table("students")
            q = db.query().\
                add_columns(not_offs).\
                add_columns(studs).\
                join(studs, studs.c.id == not_offs.c.id).\
                filter(studs.c.voting_member == are_voting)
            db.execute(q)
            rows = [ self.encode_id(dict(r), 'students_id') for r in
                db.fetchall() ]
            rows = [ globals.decode_year(r, 'students_year') for r in rows ]
            rows = [ globals.decode_major(r, 'students_major') for r in rows ]
            return rows

    def __db_get_person(self, id=None, email=None):
        if not id and not email: return None
        with DatabaseConnection() as db:
            ppl, _ = db.get_table("people_read")
            studs, _ = db.get_table("students")
            offs, _ = db.get_table("officers")
            q = db.query().\
                add_columns(ppl).add_columns(studs).add_columns(offs).\
                outerjoin(studs, studs.c.id == ppl.c.id).\
                outerjoin(offs, offs.c.id == ppl.c.id)
            if id:
                q = q.filter(ppl.c.id == id)
            elif email:
                q = q.filter(ppl.c.email == email)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'people_read_id') for row in
                db.fetchall() ]
            if len(rows) != 1:
                return None
            return rows[0]

    def __db_get_unregistered_people(self, search_email=None):
        with DatabaseConnection() as db:
            ppl, _ = db.get_table("people_read")
            q = db.query().add_columns(ppl.c.id, ppl.c.email).\
                filter(ppl.c.password == None)
            if search_email:
                q = q.filter(ppl.c.email == search_email)
            db.execute(q)
            rows = [ r for r in db.fetchall() ]
            return rows

    def __db_register_person(self, data):
        with DatabaseConnection() as db:
            ppl, _ = db.get_table("people")
            q = ppl.update().\
                returning(ppl.c.id).\
                where(ppl.c.email == data['email']).\
                values(
                    password=data['password'],
                    salt=data['salt'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

    def __db_insert_person(self, data):
        with DatabaseConnection() as db:
            ppl, _ = db.get_table("people")
            q = ppl.insert().\
                returning(ppl.c.id).\
                values(
                    first_name=data['fname'],
                    last_name=data['lname'],
                    preferred_name=data['prefname'],
                    company=data['company'],
                    email=data['email'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

    def __db_insert_student(self, data):
        with DatabaseConnection() as db:
            std, _ = db.get_table("students")
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
            ppl, _ = db.get_table("people")
            q = ppl.update().\
                returning(ppl.c.id).\
                where(ppl.c.id == data['id']).\
                values(
                    first_name=data['fname'],
                    last_name=data['lname'],
                    preferred_name=data['prefname'],
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
            ppl, _ = db.get_table("people")
            q = ppl.delete().\
                where(ppl.c.id == id)
            db.execute(q)

    def __db_delete_student(self, id):
        with DatabaseConnection() as db:
            stud, _ = db.get_table("students")
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
        d['prefname'] = data['prefname'] if data['prefname'] else None
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

    def __validate_registration(self, data):
        # makes sure the given email is an exact match for an
        # existing record, hashes password, generates a salt
        errs = []
        d = {}
        if not data['email']:
            errs.append('Must provide an email')
        if len(data['password']) < 8:
            errs.append('Must provide a password of at least 8 characters')
        if errs: return d, errs
        people = self.__db_get_unregistered_people(search_email=data['email'])
        if len(people) != 1:
            errs.append('Email doesn\'t belong to an unregistered person')
        d['email'] = data['email']
        d['salt'] = globals.gen_salt()
        d['password'] = globals.hash_password(data['password'], d['salt'])
        if not globals.check_password(data['password'], d['password'], d['salt']):
            errs.append('An error occured during securing the given password. Contact an administrator.')
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

    def __can_index(self, session):
        return True

    def __can_index_students(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_index_officers(self, session, current_only=False):
        if current_only: return True
        return 'is_officer' in session and session['is_officer']

    def __can_index_others(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_show(self, session, id=None):
        if id != None and 'person_id' in session and session['person_id'] == id:
            return True
        return 'is_officer' in session and session['is_officer']

    def __can_create(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_edit(self, session, id=None):
        if id != None and 'person_id' in session and session['person_id'] == id:
            return True
        return 'is_officer' in session and session['is_officer']

    def __can_delete(self, session):
        return 'is_officer' in session and session['is_officer']

    def __can_update(self, session, id=None):
        if id != None and 'person_id' in session and session['person_id'] == id:
            return True
        return 'is_officer' in session and session['is_officer']

    def login(self, request, session):
        if request.method == 'GET':
            if 'person_id' not in session:
                return render_template('people/login.html')
            else:
                return redirect(url_for('index_'))
        elif request.method == 'POST':
            e = request.form['email']
            p = request.form['password']
            person = self.__db_get_person(email=e)
            if not person:
                return render_template('people/login.html',
                    errors=['Email or password incorrect'])
            password_good = globals.check_password(p,
                person['people_read_password'],
                person['people_read_salt'])
            if not password_good:
                return render_template('people/login.html',
                    errors=['Email or password incorrect'])
            session['username'] = person['people_read_preferred_name'] if \
                person['people_read_preferred_name'] else \
                person['people_read_first_name']
            session['person_id'] = self.b58.decode(person['people_read_id'])[0]
            session['hashed_person_id'] = self.b58.encode(session['person_id'])
            session['is_officer'] = 'officers_person_id' in person and \
                person['officers_person_id'] != None
            session['is_admin'] = session['is_officer']
            session['is_student'] = 'students_id' in person and \
                person['students_id'] != None
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
            if not self.__can_index(session): abort(403)
            v_studs = self.__db_get_students(are_voting=True) if \
                self.__can_index_students(session) else []
            nv_studs = self.__db_get_students(are_voting=False) if \
                self.__can_index_students(session) else []
            officers = self.__db_get_officers(current_only=True) if \
                self.__can_index_officers(session, current_only=True) else []
            others = self.__db_get_others() if \
                self.__can_index_others(session) else []
            v_studs = sorted(v_studs, key=lambda k: k['not_officers_last_name'])
            nv_studs = sorted(nv_studs, key=lambda k: k['not_officers_last_name'])
            officers = sorted(officers, key=lambda k: k['officers_last_name'])
            others = sorted(others, key=lambda k: k['not_students_last_name'])
            return render_template('people/index.html',
                voting_students=v_studs,
                nonvoting_students=nv_studs,
                officers=officers,
                others=others,
                can_create=self.__can_create(session),
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session, id): abort(403)
            person = self.__db_get_person(id)
            if person == None: abort(404)
            person = globals.decode_year(person, 'students_year')
            person = globals.decode_major(person, 'students_major')
            return render_template('people/show.html', person=person,
                can_edit=self.__can_edit(session, id),
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
            if not self.__can_edit(session, id): abort(403)
            prsn = self.__db_get_person(id)
            data = {}
            data['fname'] = prsn['people_read_first_name']
            data['lname'] = prsn['people_read_last_name']
            data['prefname'] = prsn['people_read_preferred_name'] if prsn['people_read_preferred_name'] else ''
            data['company'] = prsn['people_read_company'] if prsn['people_read_company'] else ''
            data['email'] = prsn['people_read_email']
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
            if not self.__can_update(session, id): abort(403)
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

    def register(self, request, session):
        if request.method == 'GET':
            unreg_ppl = self.__db_get_unregistered_people()
            return render_template('people/register.html',
                unregistered_people=unreg_ppl)
        elif request.method == 'POST':
            data = request.form
            v_data, errs = self.__validate_registration(data)
            if errs:
                unreg_ppl = self.__db_get_unregistered_people()
                return render_template('people/register.html',
                    unregistered_people=unreg_ppl,
                    errors=errs)
            else:
                id = self.__db_register_person(v_data)
                if not id: abort(500)
                id = self.b58.encode(id)
                return redirect(url_for('people_id', id=id))
        abort(405)
