#!/usr/bin/env python

import wsgiref.handlers
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

        image = shot.get_image()
        self.response.headers['Content-Type'] = utils.detect_mime_from_image_data(image)
        self.response.out.write(str(image))


class PutHandler(webapp.RequestHandler):
    def put(self, key):
        user = models.UserProfile.get_by_secret(key).user
        shot = models.Shot(user=user)
        image_chunks = chunk_request_data(self.request, models.GAE_BLOB_LIMIT)
        shot.set_image_and_save(image_chunks)
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


app = webapp.WSGIApplication(
    [
        ('/', MainHandler),
        ('/put/(.*)', PutHandler),
        ('/(.*)', ShotHandler),
    ],
    debug=False)
