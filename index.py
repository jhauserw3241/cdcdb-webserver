from flask import abort
from flask import redirect
from flask import render_template
from flask import url_for
from os import urandom
import json

from database_connection import DatabaseConnection
from globals import globals

# Handles the inventory routes.

class Index:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.encode_id = globals.encode_id

    def __can_index(self, session):
        return True

    def future_events(self, request, session):
        if not self.__can_index(session): abort(403)
        return self.__db.get_events(future_only=True)

    def index(self, request, session, events):
        if request.method == 'GET':
            if not self.__can_index(session): abort(403)
            evts = events.future_events(request, session)
            return render_template('index.html', events=evts)
        abort(405)

