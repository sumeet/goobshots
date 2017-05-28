from __future__ import division

from google.appengine.ext import db
from google.appengine.api import images

import itertools
import random
import utils


GAE_BLOB_LIMIT = 1000*1000  # A little less than 1 MB.


class UserProfile(db.Model):
    user = db.UserProperty(required=True)
    secret = db.StringProperty(required=True)


class ShotChunk(db.Model):
    chunk = db.BlobProperty(required=True)


class Shot(db.Model):

    @classmethod
    def get_by_key(cls, key):
        try:
            key = db.Key(key)
        except db.BadKeyError:
            return None
        return cls.get(key)

    user = db.UserProperty(required=True)
    image = db.BlobProperty()
    split_image = db.ListProperty(db.Key)

    pub_date = db.DateTimeProperty(verbose_name='date published',
                                   auto_now_add=True)

    def set_image_and_save(self, image):
        if len(image) <= GAE_BLOB_LIMIT:
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
            return ''.join(ShotChunk.get(chunk_key).chunk for chunk_key in
                           self.split_image)
