#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
import utils
import models
from google.appengine.ext import db

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
        user = models.UserProfile.all().filter('secret =', key).get().user
        shot = models.Shot(user=user)
        image_chunks = chunk_request_data(self.request, models.GAE_BLOB_LIMIT)
        shot.set_image_and_save(image_chunks)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(URL % shot.key())

    post = put

class MainHandler(webapp.RequestHandler):
    @utils.require_login
    def get(self):
        context = {
            'user': models.UserProfile.all().filter('user =', users.get_current_user()).get(),
        }

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(str(utils.render('main.txt', context)))

def main():
    application = webapp.WSGIApplication(
        [
            ('/', MainHandler),
            ('/put/(.*)', PutHandler),
            ('/(.*)', ShotHandler),
        ],
        debug=False)
    wsgiref.handlers.CGIHandler().run(application)


def chunk_request_data(request, chunk_size):
    total_length = int(request.headers['Content-Length'])
    for _ in xrange(0, total_length, chunk_size):
        yield request.body_file.read(chunk_size)



if __name__ == '__main__':
    main()
