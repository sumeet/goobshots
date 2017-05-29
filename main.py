from __future__ import division

import math

from google.appengine.ext import webapp
from google.appengine.api import users
import utils
import models

URL = 'http://s.goobtown.net/%s'


class ShotHandler(webapp.RequestHandler):
    def get(self, key):
        shot = models.Shot.get_by_key(key)
        if not shot:
            self.error(404)
            self.response.out.write("404")
            return

        try:
            image = shot.get_image()
        except models.ChunkStillUploadingError as e:
            self.response.headers['Content-Type'] = 'text/html'
            self.response.out.write(str(utils.render('incomplete.html', {'error': e})))
            return

        self.response.headers['Content-Type'] = utils.detect_mime_from_image_data(image)
        self.response.out.write(str(image))


class PutHandler(webapp.RequestHandler):
    def put(self, key):
        user = models.UserProfile.get_by_secret(key).user
        shot = models.Shot(user=user)
        shot.set_image_and_save(UploadRequest(self.request))
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(URL % shot.key.urlsafe())

    post = put

class MainHandler(webapp.RequestHandler):
    @utils.require_login
    def get(self):
        context = {
            'user': models.UserProfile.get_by_user(users.get_current_user()),
        }

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(str(utils.render('main.txt', context)))


def chunk_request_data(request, chunk_size):
    total_length = int(request.headers['Content-Length'])
    for _ in xrange(0, total_length, chunk_size):
        yield request.body_file.read(chunk_size)


class UploadRequest(object):

    def __init__(self, request):
        self._request = request

    def chunks(self, chunk_size):
        for _ in xrange(0, self._total_length, chunk_size):
            yield self._request.body_file.read(chunk_size)

    def num_chunks(self, chunk_size):
        return int(math.ceil(self._total_length / chunk_size))

    @property
    def _total_length(self):
        return int(self._request.headers['Content-Length'])


app = webapp.WSGIApplication(
    [
        ('/', MainHandler),
        ('/put/(.*)', PutHandler),
        ('/(.*)', ShotHandler),
    ],
    debug=False)
