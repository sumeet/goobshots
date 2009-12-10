from google.appengine.ext import db
from google.appengine.api import images
import utils
import random

THUMBNAIL_SIZE = 300

class UserProfile(db.Model):
	user = db.UserProperty(required=True)
	secret = db.StringProperty(required=True)
	
class Shot(db.Model):
	user = db.UserProperty(required=True)
	image = db.BlobProperty(required=True)
	thumbnail = db.BlobProperty()
	pub_date = db.DateTimeProperty(verbose_name='date published', auto_now_add=True)
	
	def put(self):
		image = images.Image(self.image)
		if image.width >= image.height:
			image.resize(height=THUMBNAIL_SIZE)
			image.execute_transforms()
			p = (float(THUMBNAIL_SIZE) / float(image.width))
			r = random.uniform(0.0, 1.0 - p)
			image.crop(r, 0.0, r+p, 1.0)
		else:
			image.resize(width=THUMBNAIL_SIZE)
			image.execute_transforms()
			p = (float(THUMBNAIL_SIZE) / float(image.height))
			r = random.uniform(0.0, 1.0 - p)
			image.crop(0.0, r, 1.0, r+p)
		self.thumbnail = image.execute_transforms()
		super(Shot, self).put()