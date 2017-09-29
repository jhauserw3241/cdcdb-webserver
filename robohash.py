from flask import abort
from flask import Response
from flask import send_file
import os
import requests

from globals import globals

# Handles the Robohash routes.

# We had issues with robohash staying up, so we started caching the images it
# gives us


class Robohash:
    def __init__(self):
        self.cache_dir = os.path.abspath('cache')
        os.makedirs(self.cache_dir, exist_ok=True)

    #####
    # PERMISSION CHECKS
    #####

    def __can_get(self, session):
        return True

    # Determine whether the string is okay
    def s_ok(self, s):
        for c in s:
            if c not in globals.config['b58']['alphabet']:
                return False
        return True

    # Determine if the given size is out of bounds
    def size_ok(self, size):
        try:
            first, second = size.split('x', maxsplit=1)
            first = int(first)
            second = int(second)
        except ValueError:
            return False
        if first < 1 or first > 300:
            return False
        if second < 1 or second > 300:
            return False
        return True

    # Router calls this to fetch an image, from cache if possible. If not in
    # cache already, go get it from robohash.org and save it in the cache for
    # the future before returning it
    def get(self, request, session, s):
        if request.method == 'GET':
            if not self.__can_get(session):
                abort(403)
            if not self.s_ok(s):
                abort(404)
            if 'size' in request.args and request.args['size']:
                size = request.args['size']
            else:
                size = '300x300'
            if not self.size_ok(size):
                abort(404)
            f = os.path.join(self.cache_dir, s + '.' + size + '.png')
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
