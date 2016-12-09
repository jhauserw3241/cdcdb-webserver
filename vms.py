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

    def __db_get_vms(self):
        with DatabaseConnection() as db:
            vms, _ = db.get_table("vms")
            people,_= db.get_table("people_read")
            q = db.query().\
                add_columns(
                    vms.c.id, vms.c.owner_id, vms.c.name,
                    vms.c.network, vms.c.role, people.c.id,people.full_name).\
                 outerjoin(people, people.c.id == vms.c.owner_id)
            db.execute(q)
            vms = [ self.encode_id(dict(row), 'vms_id') for row in db.fetchall() ]
            return vms[::-1]

    def __db_get_vm(self, id):
        with DatabaseConnection() as db:
            vms, _ = db.get_table("vms")
            q = db.query().\
                add_columns(
                    vms.c.id, vms.c.owner_id, vms.c.name,
                    vms.c.network, vms.c.role).\
                filter(vms.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'vms_id') for row in db.fetchall() ]
            if len(rows) != 1: return None
            return rows[0]

    def __db_insert_vm(self, data):
        with DatabaseConnection() as db:
            vms, _ = db.get_table("vms")
            q = vms.insert().\
                returning(vms.c.id).\
                values(
                    owner_id=data['owner_id'],
                    name=data['name'],
                    network=data['network'],
                    role=data['role'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

    def __db_update_vm(self, data):
        self.__db_delete_vm(data['id'])
        self.__db_insert_vm(data)

    def __db_delete_vm(self, id):
        with DatabaseConnection() as db:
            vms, _ = db.get_table("vms")
            q = vms.delete().\
                where(vms.c.id == id)
            db.execute(q)

    def __validate_vm(self, data):
        errs = []
        d = {}
        if not data['owner_id']:
            errs.append('Owner_id is required')
        d['owner_id'] = data['owner_id']
        if not data['name']:
            err.append('VM name is required')
        d['name'] = data['name']
        d['network'] = data['network']
        d['role'] = data['role']
        return d, errs

    def __create_vm(self, request, session, data):
        v_data, errs = self.__validate_vm(data)
        if errs:
            return render_template('vms/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_vm(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('vms_id', id=id))

    def __update_vm(self, request, session, id, data):
        v_data, errs = self.__validate_vm(data)
        if errs:
            return render_template('vms/new.html', data=data,
                errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_vm(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('vms_id', id=id))

    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            vms = self.__db_get_vms()
            return render_template('vms/index.html', vms=vms,
                can_create=self.__can_create(session),
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            vm = self.__db_get_vm(id)
            if not vm: abort(404)
            return render_template('vms/show.html', vm=vm,
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

    def new(self, request, session):
        if request.method == 'GET':
            if not self.__can_create(session): abort(403)
            return render_template('vms/new.html',
                data={}, submit_button_text='Create')
        abort(405)

    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session): abort(403)
            data = request.form
            return self.__create_vm(request, session, data)
        abort(405)

    def edit(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_edit(session): abort(403)
            vm = self.__db_get_vm(id)
            data = {}
            data['name'] = vm['vms_name']
            data['owner_id'] = vm['vms_owner_id']
            data['network'] = vm['vms_network']
            data['role'] = vm['vms_role']
            print(vm)
            return render_template('vms/new.html', data=data,
                submit_button_text='Update')
        abort(405)

    def update(self, request, session, id):
        if request.method == 'POST':
            if not self.__can_update(session): abort(403)
            data = request.form
            return self.__update_vm(request, session, id, data)
        abort(405)

    def delete(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_delete(session): abort(403)
            self.__db_delete_vm(id)
            return redirect(url_for('vms_'))

