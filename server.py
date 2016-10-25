#!/usr/bin/env python3
from flask import Flask
from flask import abort
from flask import render_template
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from globals import globals
from help import Help
from test import Test
from people import People
from inventory import Inventory

app = Flask(__name__)
# The handler classes for each route type
help = Help()
test = Test()
people = People()
inventory = Inventory()

config = globals.config
b58 = globals.base58_hashids

# here all the valid routes are defined, as well as the valid verbs
# for each

# server.py does as little work as considered resonable and hands off
# control to the appropriate handler class.
# usually the hashed id from the url is checked for validitiy first

@app.route('/')
def index():
    print(session)
    return render_template("index.html")

@app.route('/help', methods=['GET'])
def help_():
    if request.method == 'GET':
        return help.index(request, session)
    else:
        abort(405)

@app.route('/login/', methods=['GET', 'POST'])
def people_login():
    if request.method == 'GET':
        return people.login(request, session)
    else:
        return people.login(request, session)

@app.route('/logout', methods=['GET'])
def people_logout():
    if request.method == 'GET':
        return people.logout(request, session)
    else:
        abort(405)

@app.route('/register/', methods=['GET', 'POST'])
def people_register():
    if request.method == 'GET':
        return people.register(request, session)
    if request.method == 'POST':
        return people.register(request, session)

@app.route('/inventory/', methods=['GET'])
def inventory_():
    if request.method == 'GET':
        return inventory.index(request, session)
    else:
        abort(405)

@app.route('/test', methods=['GET'])
def test_():
    if request.method == 'GET':
        return test.do(request, session)
    else:
        abort(405)

if __name__=='__main__':
    app.debug = True
    app.secret_key = globals.config['common']['secret']
    app.jinja_env.globals['app_name'] = config['common']['name']
    app.jinja_env.globals['app_tagline'] = config['common']['tagline']
    app.run(host='0.0.0.0', threaded=True)
