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
    def index(self, request, session):
        if request.method == 'GET':
            if 'person_id' not in session:
                abort(403)
            return render_template('inventory/index.html')
        abort(405)
