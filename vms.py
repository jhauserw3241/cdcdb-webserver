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

        # Determines if the user can view the list of VMs
    def __can_index(self, session):
        return True

        # Determines if the user can view VM details
    def __can_show(self, session):
        return True

        # Determines if the user can view the VM edit page
    def __can_edit(self, session):
        return 'is_officer' in session and session['is_officer']

        # Determines if the user can update VM information in the database
    def __can_update(self, session):
        return 'is_officer' in session and session['is_officer']

        # Determines if the user can create new VMs
    def __can_create(self, session):
        return 'is_officer' in session and session['is_officer']

        # Determines if the user can delete VMs from the database
    def __can_delete(self, session):
        return 'is_officer' in session and session['is_officer']

        # Used internally to return a list of all the VMs in the database
    def __db_get_vms(self):
        with DatabaseConnection() as db:
            vms, _ = db.get_table("vms")
            people, _ = db.get_table("people_read")
            q = db.query().\
                add_columns(
                    vms.c.id, vms.c.owner_id, vms.c.name,
                    vms.c.network, vms.c.role, people.c.id, people.c.full_name).\
                outerjoin(people, people.c.id == vms.c.owner_id)
            db.execute(q)
            vms = [self.encode_id(dict(row), 'vms_id')
                   for row in db.fetchall()]
            return vms[::-1]

        # Used internally to get information on only the specified VM
    def __db_get_vm(self, id):
        with DatabaseConnection() as db:
            vms, _ = db.get_table("vms")
            people, _ = db.get_table("people_read")
            q = db.query().\
                add_columns(
                    vms.c.id, vms.c.owner_id, vms.c.name,
                    vms.c.network, vms.c.role, people.c.id, people.c.full_name).\
                filter(vms.c.id == id).\
                outerjoin(people, people.c.id == vms.c.owner_id)
            db.execute(q)
            rows = [self.encode_id(dict(row), 'vms_id')
                    for row in db.fetchall()]
            if len(rows) != 1:
                return None
            return rows[0]

        # Used internally to insert a new VM into the database
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
            if len(lastrowid) != 1:
                return None
            else:
                return lastrowid[0]

        # Used internally to update VM information in the database
    def __db_update_vm(self, data):
        self.__db_delete_vm(data['id'])
        return self.__db_insert_vm(data)

        # Used internally to delete a VM from the database
    def __db_delete_vm(self, id):
        with DatabaseConnection() as db:
            vms, _ = db.get_table("vms")
            q = vms.delete().\
                where(vms.c.id == id)
            db.execute(q)

        # Used internally to verify that all required information is
        # included in the submitted data
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

        # Used internally to verify new VM information and add the
        # VM to the database
    def __create_vm(self, request, session, data):
        v_data, errs = self.__validate_vm(data)
        if errs:
            return render_template('vms/new.html', data=data,
                                   errors=errs, submit_button_text='Create')
        id = self.__db_insert_vm(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('vms_id', id=id))

        # Used internally to verify and update VM information in the
        # database
    def __update_vm(self, request, session, id, data):
        v_data, errs = self.__validate_vm(data)
        if errs:
            return render_template('vms/new.html', data=data,
                                   errors=errs, submit_button_text='Update')
        v_data['id'] = id
        id = self.__db_update_vm(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('vms_id', id=id))

        # Used externally to return a rendered page with a list of
        # all VMs in the database
    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session):
                abort(403)
            vms = self.__db_get_vms()
            return render_template('vms/index.html', vms=vms,
                                   can_create=self.__can_create(session),
                                   can_edit=self.__can_edit(session),
                                   can_delete=self.__can_delete(session))
        abort(405)

        # Used externally to return a rendered page with detailed
        # information on the specified VM
    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session):
                abort(403)
            vm = self.__db_get_vm(id)
            if not vm:
                abort(404)
            return render_template('vms/show.html', vm=vm,
                                   can_edit=self.__can_edit(session),
                                   can_delete=self.__can_delete(session))
        abort(405)

        # Used externally to return a rendered page for the user
        # to imput information for a new VM
    def new(self, request, session):
        if request.method == 'GET':
            if not self.__can_create(session):
                abort(403)
            return render_template('vms/new.html',
                                   data={}, submit_button_text='Create')
        abort(405)

        # Used externally to add a new VM to the database which
        # matches the information provided by the user
    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session):
                abort(403)
            data = request.form
            return self.__create_vm(request, session, data)
        abort(405)

        # Used externally to return a rendered page for the user
        # to edit a VMs information, with the information pre-filled
        # with the current information for the given VM
    def edit(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_edit(session):
                abort(403)
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

        # Used externally to apply updates made by the user to the
        # specified VM
    def update(self, request, session, id):
        if request.method == 'POST':
            if not self.__can_update(session):
                abort(403)
            data = request.form
            return self.__update_vm(request, session, id, data)
        abort(405)

        # Used externally to delete the specified VM from the database
    def delete(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_delete(session):
                abort(403)
            self.__db_delete_vm(id)
            return redirect(url_for('vms_'))
