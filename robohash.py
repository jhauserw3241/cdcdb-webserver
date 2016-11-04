from flask import abort
from flask import Response
from flask import send_file
import os
import requests

from globals import globals

# Handles the Robohash routes.

class Robohash:
    def __init__(self):
        self.cache_dir = os.path.abspath('cache')
        os.makedirs(self.cache_dir, exist_ok=True)

    def __can_get(self, session):
        return True

    def s_ok(self, s):
        for c in s:
            if c not in globals.config['b58']['alphabet']:
                return False
        return True

    def size_ok(self, size):
        try:
            first, second = size.split('x', maxsplit=1)
            first = int(first)
            second = int(second)
        except ValueError:
            return False
        if first < 1 or first > 200: return False
        if second < 1 or second > 200: return False
        return True

    def get(self, request, session, s):
        if request.method == 'GET':
            if not self.__can_get(session): abort(403)
            if not self.s_ok(s): abort(404)
            if 'size' in request.args and request.args['size']:
                size = request.args['size']
            else:
                size = '50x50'
            if not self.size_ok(size): abort(404)
            f = os.path.join(self.cache_dir, s+'.'+size+'.png')
            if os.path.isfile(f):
                return send_file(f, mimetype='image/png', conditional=True)
            else:
                r = requests.get('http://robohash.org/{}?size={}'.format(s, size),
                    verify=True)
                if r.status_code == requests.codes.ok:
                    with open(f, 'wb') as fp:
                        fp.write(r.content)
                    return Response(r.content, mimetype='image/png')
                else:
                    abort(404)
        abort(405)
