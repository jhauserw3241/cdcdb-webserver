from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the inventory routes.
class Inventory:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.encode_id = globals.encode_id

	# Returns the available items in the inventory
    def __db_is_item_available(self, id):
        with DatabaseConnection() as db:
            inv, _ = db.get_table("available_items")
            q = db.query().\
                add_columns(inv).\
                filter(inv.c.id == id)
            db.execute(q)
            return len([ r for r in db.fetchall()]) > 0

	# Returns all of the items in the inventory
    def __db_get_inventory(self):
        with DatabaseConnection() as db:
            inv, _ = db.get_table("inventory")
            q = db.query().\
                add_columns(
                    inv.c.id, inv.c.description, inv.c.serial_number, inv.c.make,
                    inv.c.model, inv.c.manufacturer, inv.c.location,
                    inv.c.other_notes)
            db.execute(q)
            return [ self.encode_id(dict(row), 'inventory_id') for row in db.fetchall() ]

	# Gets all of the information for the specified item.
    def __db_get_item(self, id):
        with DatabaseConnection() as db:
            inv, _ = db.get_table("inventory")
            q = db.query().add_columns(inv).filter(inv.c.id == id)
            db.execute(q)
            rows = [ self.encode_id(dict(row), 'inventory_id') for row in db.fetchall() ]
            if len(rows) != 1: return None
            return rows[0]

	# Function responsible for updating the specified item 
	# in the inventory to match the provided information.
    def __db_update_item(self, id, data):
        with DatabaseConnection() as db:
            inv, _ = db.get_table("inventory")
            q = inv.update().\
                where(inv.c.id == id).\
                values(
                    description=data['description'], serial_number=data['serial_number'],
                    make=data['make'], model=data['model'],
                    manufacturer=data['manufacturer'],
                    location=data['location'], other_notes=data['other_notes']
                )
            db.execute(q)

	# Function responsible for adding a new item to the 
	# inventory table with the information provided
    def __db_insert_item(self, data):
        with DatabaseConnection() as db:
            inv, _ = db.get_table("inventory")
            q = inv.insert().\
                returning(inv.c.id).\
                values(
                    description=data['description'],
                    serial_number=data['serial_number'],
                    make=data['make'],
                    model=data['model'],
                    manufacturer=data['manufacturer'],
                    category=data['category'],
                    location=data['location'],
                    other_notes=data['other_notes'])
            db.execute(q)
            lastrowid = db.lastrowid()
            if len(lastrowid) != 1: return None
            else: return lastrowid[0]

	# Function responsible for deletion of the specified
	# item from the database
    def __db_delete_item(self, id):
        with DatabaseConnection() as db:
            inv, _ = db.get_table("inventory")
            q = inv.delete().\
                where(inv.c.id == id)
            db.execute(q)

	# Function which verifies that all information required
	# by the database is provided before the information is
	# added to the database
    def __validate_item(self, data):
        d = {}
        errs = []
        d['description'] = data['description']
        d['serial_number'] = data['serial_number']
        d['make'] = data['make']
        d['model'] = data['model']
        d['manufacturer'] = data['manufacturer']
        d['category'] = data['category']
        if not data['location']:
            errs.append('Location is required')
        d['location'] = data['location']
        d['other_notes'] = data['other_notes']
        return d, errs

	# Function responsible for the validiation and addition
	# of a new inventory item.
    def __create_item(self, request, session, data):
        v_data, errs = self.__validate_item(data)
        if errs:
            return render_template('inventory/new.html', data=data,
                errors=errs, submit_button_text='Create')
        id = self.__db_insert_item(v_data)
        id = self.b58.encode(id)
        return redirect(url_for('inventory_id', id=id))

	# Function to determine if the user possesses sufficient
	# permissions to view the list of inventory items
    def __can_index(self, session):
        return 'is_student' in session and session['is_student']

	# Function to determine if the user possesses sufficient
	# permissions to view the detailed information of any 
	# inventory items
    def __can_show(self, session):
        return 'is_student' in session and session['is_student']

	# Function to determine if the user is allowed to view the
	# edit page for inventory items
    def __can_edit(self, session):
        return 'is_officer' in session and session['is_officer']

	# Function to determine if the user is allowed to make changes
	# to inventory items in the database
    def __can_update(self, session):
        return 'is_officer' in session and session['is_officer']
	
	# Function to determine if the user is allowed to create new
	# inventory items
    def __can_create(self, session):
        return 'is_officer' in session and session['is_officer']

	# Determines if the user is allowed to delete inventory items
    def __can_delete(self, session):
        return 'is_officer' in session and session['is_officer']

	# Function which checks permissions and then renders the index page
	# with a list of all inventory items
    def index(self, request, session):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            items = self.__db_get_inventory()
            return render_template('inventory/index.html', items=items,
                can_create=self.__can_create(session),
                can_edit=self.__can_edit(session),
                can_delete=self.__can_delete(session))
        abort(405)

    # used externally to retrieve a list of available inventory items
    def is_item_available(self, request, session, id):
      if not self.__can_show(session): abort(403)
      return self.__db_is_item_available(id)

    # used externally for getting all the info for the given item id
    def get_item_by_id(self, request, session, id):
        if not self.__can_show(session): abort(403)
        return self.__db_get_item(id)

	# Function to check permissions and render a page showing the details
	# for the specified item
    def show(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_show(session): abort(403)
            item = self.__db_get_item(id)
            if item == None:
                abort(404)
            return render_template('inventory/show.html', item=item,
            can_edit=self.__can_edit(session),
            can_delete=self.__can_delete(session),
            is_available=self.__db_is_item_available(id))
        abort(405)

	# Function to render a page to allow a user to change information
	# for a given item
    def edit(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_edit(session): abort(403)
            item = self.__db_get_item(id)
            if not item: abort(404)
            data = {}
            data['description'] = item['inventory_description'] if \
                item['inventory_description'] else ''
            data['serial_number'] = item['inventory_serial_number'] if \
                item['inventory_serial_number'] else ''
            data['make'] = item['inventory_make'] if \
                item['inventory_make'] else ''
            data['model'] = item['inventory_model'] if \
                item['inventory_model'] else ''
            data['manufacturer'] = item['inventory_manufacturer'] if \
                item['inventory_manufacturer'] else ''
            data['location'] = item['inventory_location'] if \
                item['inventory_location'] else ''
            data['other_notes'] = item['inventory_other_notes'] if \
                item['inventory_other_notes'] else ''
            return render_template('inventory/new.html', data=data,
                submit_button_text='Update')
        abort(405)

	# Function to update an item in the inventory based off of the 
	# user provided information
    def update(self, request, session, id):
        if request.method == 'POST':
            if not self.__can_update(session): abort(403)
            self.__db_update_item(id, request.form)
            return redirect(url_for('inventory_id', id=self.b58.encode(id)))
        abort(405)

	# Renders a page where the user can input information for a new 
	# inventory item
    def new(self, request, session):
        if request.method == 'GET':
            if not self.__can_create(session): abort(403)
            return render_template('inventory/new.html',
                data={}, submit_button_text='Create')
        abort(405)

	# Creates a new inventory item based on the user provided information
    def create(self, request, session):
        if request.method == 'POST':
            if not self.__can_create(session): abort(403)
            data = request.form
            return self.__create_item(request, session, data)
        abort(405)

	# Deletes the specified inventory item from the database
    def delete(self, request, session, id):
        if request.method == 'GET':
            if not self.__can_delete(session): abort(403)
            self.__db_delete_item(id)
            return redirect(url_for('inventory_'))
