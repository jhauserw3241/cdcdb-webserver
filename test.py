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

    def login(self, u, p):
        data = { 'username': u, 'password': p}
        r = requests.post(self.base_url+"/login/", data)
        return r.cookies if r.cookies else None

    def gives_return_code(self, code, url):
        url = self.base_url + url
        r = requests.get(url, timeout=2)
        return r.status_code == code

    def cred_gives_return_code(self, code, u, p, url):
        url = self.base_url + url
        cookies = self.login(u, p)
        r = requests.get(url, timeout=2, cookies=cookies)
        return r.status_code == code

    def login_valid(self, u, p, valid):
        cookies = self.login(u, p)
        return (not not cookies) == valid

    def do(self, request, session):
        return_code_tests = []
        cred_return_code_tests = []
        login_tests = []

        test_url_codes = [
            {'url': '/', 'code': 200},
            {'url': '/badurl', 'code': 404},
            {'url': '/login', 'code': 200},
            {'url': '/people', 'code': 403},
            {'url': '/people/'+self.encode_id(0), 'code': 403},
            {'url': '/people/AAAAAAAAAA', 'code': 404},
            {'url': '/people?limit=officers', 'code': 200},
            {'url': '/events', 'code': 200},
            {'url': '/events/'+self.encode_id(0), 'code': 200},
            {'url': '/events/AAAAAAAAAA', 'code': 404},
            {'url': '/inventory', 'code': 403},
            {'url': '/inventory/'+self.encode_id(0), 'code': 403},
            {'url': '/inventory/AAAAAAAAAA', 'code': 404},
        ]
        for tuc in test_url_codes:
            return_code_tests.append({ 'url': tuc['url'],
                'code': tuc['code'],
                'good': self.gives_return_code(tuc['code'], tuc['url'])
            })

        test_cred_url_codes = [
            {'url': '/people', 'code': 200, 'u': 'root', 'p': 'root' },
            {'url': '/people', 'code': 403, 'u': 'admin', 'p': 'admin' },
            {'url': '/people', 'code': 200, 'u': 'officer', 'p': 'officer' },
            {'url': '/people', 'code': 403, 'u': 'student', 'p': 'student' },
            {'url': '/people?limit=officers', 'code': 200, 'u': 'root', 'p': 'root' },
            {'url': '/people?limit=officers', 'code': 200, 'u': 'admin', 'p': 'admin' },
            {'url': '/people?limit=officers', 'code': 200, 'u': 'officer', 'p': 'officer' },
            {'url': '/people?limit=officers', 'code': 200, 'u': 'student', 'p': 'student' },
            {'url': '/people/'+self.encode_id(0), 'code': 200, 'u': 'root', 'p': 'root' },
            {'url': '/people/'+self.encode_id(0), 'code': 403, 'u': 'admin', 'p': 'admin' },
            {'url': '/people/'+self.encode_id(0), 'code': 200, 'u': 'officer', 'p': 'officer' },
            {'url': '/people/'+self.encode_id(0), 'code': 403, 'u': 'student', 'p': 'student' },
            {'url': '/people/AAAAAAAAAA', 'code': 404, 'u': 'root', 'p': 'root' },
            {'url': '/people/AAAAAAAAAA', 'code': 404, 'u': 'admin', 'p': 'admin' },
            {'url': '/people/AAAAAAAAAA', 'code': 404, 'u': 'officer', 'p': 'officer' },
            {'url': '/people/AAAAAAAAAA', 'code': 404, 'u': 'student', 'p': 'student' },
            {'url': '/events', 'code': 200, 'u': 'root', 'p': 'root' },
            {'url': '/events', 'code': 200, 'u': 'admin', 'p': 'admin' },
            {'url': '/events', 'code': 200, 'u': 'officer', 'p': 'officer' },
            {'url': '/events', 'code': 200, 'u': 'student', 'p': 'student' },
            {'url': '/events/'+self.encode_id(0), 'code': 200, 'u': 'root', 'p': 'root' },
            {'url': '/events/'+self.encode_id(0), 'code': 200, 'u': 'admin', 'p': 'admin' },
            {'url': '/events/'+self.encode_id(0), 'code': 200, 'u': 'officer', 'p': 'officer' },
            {'url': '/events/'+self.encode_id(0), 'code': 200, 'u': 'student', 'p': 'student' },
            {'url': '/events/AAAAAAAAAA', 'code': 404, 'u': 'root', 'p': 'root' },
            {'url': '/events/AAAAAAAAAA', 'code': 404, 'u': 'admin', 'p': 'admin' },
            {'url': '/events/AAAAAAAAAA', 'code': 404, 'u': 'officer', 'p': 'officer' },
            {'url': '/events/AAAAAAAAAA', 'code': 404, 'u': 'student', 'p': 'student' },
            {'url': '/inventory', 'code': 200, 'u': 'root', 'p': 'root' },
            {'url': '/inventory', 'code': 200, 'u': 'admin', 'p': 'admin' },
            {'url': '/inventory', 'code': 200, 'u': 'officer', 'p': 'officer' },
            {'url': '/inventory', 'code': 200, 'u': 'student', 'p': 'student' },
            {'url': '/inventory/'+self.encode_id(0), 'code': 200, 'u': 'root', 'p': 'root' },
            {'url': '/inventory/'+self.encode_id(0), 'code': 200, 'u': 'admin', 'p': 'admin' },
            {'url': '/inventory/'+self.encode_id(0), 'code': 200, 'u': 'officer', 'p': 'officer' },
            {'url': '/inventory/'+self.encode_id(0), 'code': 200, 'u': 'student', 'p': 'student' },
            {'url': '/inventory/AAAAAAAAAA', 'code': 404, 'u': 'root', 'p': 'root' },
            {'url': '/inventory/AAAAAAAAAA', 'code': 404, 'u': 'admin', 'p': 'admin' },
            {'url': '/inventory/AAAAAAAAAA', 'code': 404, 'u': 'officer', 'p': 'officer' },
            {'url': '/inventory/AAAAAAAAAA', 'code': 404, 'u': 'student', 'p': 'student' },
        ]
        for tcuc in test_cred_url_codes:
            cred_return_code_tests.append({ 'url': tcuc['url'],
                'code': tcuc['code'], 'u': tcuc['u'], 'p': tcuc['p'],
                'good': self.cred_gives_return_code(
                    tcuc['code'], tcuc['u'], tcuc['p'], tcuc['url']
                )
            })

        test_logins = [
            {'u': 'student', 'p': 'student', 'valid': True},
            {'u': 'root', 'p': 'root', 'valid': True},
            {'u': 'admin', 'p': 'admin', 'valid': True},
            {'u': 'officer', 'p': 'officer', 'valid': True},
            {'u': 'doesnotexist', 'p': 'doesnotexist', 'valid': False},
        ]
        for tl in test_logins:
            login_tests.append({'u': tl['u'], 'p': tl['p'],
                'valid': tl['valid'],
                'good': self.login_valid(tl['u'], tl['p'], tl['valid'])
            })

        return render_template('test/index.html',
            return_code_tests=return_code_tests,
            cred_return_code_tests=cred_return_code_tests,
            login_tests=login_tests
        )




