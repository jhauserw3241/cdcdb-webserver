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

    def __db_get_people(self):
        with DatabaseConnection() as db:
            current_year = globals.current_datetime("%Y")
            ppl, ppl_md = db.get_table("persons")
            studs, studs_md = db.get_table("students")
            pos, pos_md = db.get_table("positions")
            q = db.query().\
                add_columns(ppl.c.id, ppl.c.first_name, ppl.c.last_name).\
                add_columns(ppl.c.company, ppl.c.email).\
                add_columns(studs.c.major, studs.c.year).\
                add_columns(pos.c.title).\
                outerjoin(studs, studs.c.id == ppl.c.id).\
                outerjoin(pos,
                    (pos.c.person_id == ppl.c.id) &
                    (pos.c.year == current_year)
                )
            db.execute(q)
            return [ self.encode_id(dict(row), 'persons_id') for row in
                db.fetchall() ]

    def __db_get_person(self, id):
        with DatabaseConnection() as db:
            current_year = globals.current_datetime("%Y")
            ppl, ppl_md = db.get_table("persons")
            studs, studs_md = db.get_table("students")
            pos, pos_md = db.get_table("positions")
            q = db.query().\
                add_columns(ppl.c.id, ppl.c.first_name, ppl.c.last_name).\
                add_columns(ppl.c.company, ppl.c.email).\
                add_columns(studs.c.major, studs.c.year).\
                add_columns(pos.c.title).\
                outerjoin(studs, studs.c.id == ppl.c.id).\
                outerjoin(pos,
                    (pos.c.person_id == ppl.c.id) &
                    (pos.c.year == current_year)
                ).\
                filter(ppl.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'persons_id') for row in
                db.fetchall() ]
            if len(rows) != 1:
                return None
            return rows[0]

    def __can_index(self, session):
        return 'is_student' in session and session['is_student']

    def __can_show(self, session):
        return 'is_student' in session and session['is_student']

    def login(self, request, session):
        if request.method == 'GET':
            if 'person_id' not in session:
                return render_template('people/login.html')
            else:
                return redirect(url_for('index'))
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
                return redirect(url_for('index'))
            elif u == "admin" and p == "admin":
                session['username'] = u
                session['person_id'] = 2
                session['hashed_person_id'] = self.b58.encode(session['person_id'])
                session['is_admin'] = True if True else False
                session['is_officer'] = False if True else False
                session['is_student'] = True if True else False
                return redirect(url_for('index'))
            elif u == "officer" and p == "officer":
                session['username'] = u
                session['person_id'] = 3
                session['hashed_person_id'] = self.b58.encode(session['person_id'])
                session['is_admin'] = False if True else False
                session['is_officer'] = True if True else False
                session['is_student'] = True if True else False
                return redirect(url_for('index'))
            elif u == "student" and p == "student":
                session['username'] = u
                session['person_id'] = 4
                session['hashed_person_id'] = self.b58.encode(session['person_id'])
                session['is_admin'] = False if True else False
                session['is_officer'] = False if True else False
                session['is_student'] = True if True else False
                return redirect(url_for('index'))
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
            ppl = self.__db_get_people()
            return render_template('people/index.html', people=ppl)
        abort(405)

    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            person = self.__db_get_person(id)
            if not person: abort(404)
            return render_template('people/show.html', person=person)
        abort(405)
