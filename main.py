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
		shot = models.Shot.get(db.Key(key)).image
		self.response.headers['Content-Type'] = utils.detect_mime_from_image_data(shot)
		self.response.out.write(shot)

class ThumbHandler(webapp.RequestHandler):
	def get(self, key):
		shot = models.Shot.get(db.Key(key)).thumbnail
		self.response.headers['Content-Type'] = utils.detect_mime_from_image_data(shot)
		self.response.out.write(shot)

class PutHandler(webapp.RequestHandler):
	def put(self, key):
		shot = models.Shot(user=models.UserProfile.all().filter('secret =', key).get().user, image=db.Blob(self.request.body))
		shot.put()
		self.response.headers['Content-Type'] = 'text/plain'
		from google.appengine.api import images
		self.response.out.write(URL % shot.key())

class MainHandler(webapp.RequestHandler):
	@utils.require_login
	def get(self):
		context = {
			'user': models.UserProfile.all().filter('user =', users.get_current_user()).get(),
		}

		self.response.headers['Content-Type'] = 'text/plain'
		self.response.out.write(utils.render('main.txt', context))

def main():
	application = webapp.WSGIApplication(
		[
			('/', MainHandler),
			('/put/(.*)', PutHandler),
			('/(.*)\.thumb', ThumbHandler),
			('/(.*)', ShotHandler),
		],
		debug=False)
	wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
	main()
