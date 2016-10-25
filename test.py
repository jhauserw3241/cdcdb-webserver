from flask import render_template
import requests

from globals import globals

# Runs tests on the app when the appropriate route is called.

class Test:
    def __init__(self):
        self.b58 = globals.base58_hashids
        self.base_url = "http://localhost:5000"
        pass
    def encode_id(self, id):
        return self.b58.encode(id)
    def decode_id(self, id):
        return self.b58.decode(id)
    def gives_return_code(self, code, url):
        url = self.base_url + url
        r = requests.get(url, timeout=2)
        return r.status_code == code
    def login(self, username, password, valid):
        data = { 'username': username, 'password': password}
        r = requests.post(self.base_url+"/login/", data)
        return (not not r.cookies) == valid
    def do(self, request, session):
        return_code_tests = []
        login_tests = []
        test_url_codes = [
            {'url': '/', 'code': 200},
            {'url': '/badurl', 'code': 404},
            #{'url': '/users', 'code': 200},
            #{'url': '/users/'+self.encode_id(1), 'code': 200},
            #{'url': '/users/aaaa', 'code': 404},
            {'url': '/login', 'code': 200},
            {'url': '/logout', 'code': 200},
        ]
        for tuc in test_url_codes:
            return_code_tests.append({ 'url': tuc['url'],
                'code': tuc['code'],
                'good': self.gives_return_code(tuc['code'], tuc['url'])
            })
        test_logins = [
            {'username': 'test', 'password': 'test', 'valid': True},
            {'username': 'test', 'password': 'nottest', 'valid': False},
            {'username': 'nottest', 'password': 'test', 'valid': False},
        ]
        for tl in test_logins:
            login_tests.append({'username': tl['username'],
                'password': tl['password'],
                'valid': tl['valid'],
                'good': self.login(tl['username'], tl['password'], tl['valid'])
            })
        return render_template('test/index.html', return_code_tests=return_code_tests, login_tests=login_tests)
