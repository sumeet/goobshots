from __future__ import division

from google.appengine.ext import db
from google.appengine.api import images

import itertools
import random
import utils

THUMBNAIL_SIZE = 300

GAE_BLOB_LIMIT = 1000*1000  # A little less than 1 MB.

class UserProfile(db.Model):
    user = db.UserProperty(required=True)
    secret = db.StringProperty(required=True)


class ShotChunk(db.Model):
    chunk = db.BlobProperty(required=True)


class Shot(db.Model):
    user = db.UserProperty(required=True)
    image = db.BlobProperty()
    split_image = db.ListProperty(db.Key)

    thumbnail = db.BlobProperty()
    pub_date = db.DateTimeProperty(verbose_name='date published',
                                   auto_now_add=True)

    def set_thumbnail(self, image):
        image = images.Image(image)

        if image.width >= image.height:
            image.resize(height=THUMBNAIL_SIZE)
            #image.execute_transforms()
            p = THUMBNAIL_SIZE / image.width
            r = random.uniform(0.0, 1.0 - p)
            image.crop(r, 0.0, r+p, 1.0)

        else:
            image.resize(width=THUMBNAIL_SIZE)
            #image.execute_transforms()
            p = THUMBNAIL_SIZE / image.height
            r = random.uniform(0.0, 1.0 - p)
            image.crop(0.0, r, 1.0, r+p)

        self.thumbnail = image.execute_transforms()

    def set_image_and_save(self, image):

        if len(image) <= GAE_BLOB_LIMIT:
            self.set_thumbnail(image)
            self.image = db.Blob(image)

        else:
            self.split_image = []
            # Cut the image into chunks.
            for chunk in utils.segment(image, GAE_BLOB_LIMIT):
                shot_chunk = ShotChunk(chunk=chunk)
                shot_chunk.put()
                self.split_image.append(shot_chunk.key())

        self.put()

    def get_image(self):
        if self.image:
            return self.image

        else:
            # Reassemble the chunked image.
            reassembled_image = ''

            for chunk_key in self.split_image:
                reassembled_image += ShotChunk.get(chunk_key).chunk

            return reassembled_image


