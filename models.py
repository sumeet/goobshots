from google.appengine.ext import ndb


GAE_BLOB_LIMIT = 1000*1000  # A little less than 1 MB.


class UserProfile(ndb.Model):
    @classmethod
    def get_by_user(cls, user):
        return cls.query(cls.user == user).get()

    @classmethod
    def get_by_secret(cls, secret):
        return cls.query(cls.secret == secret).get()

    user = ndb.UserProperty(required=True)
    secret = ndb.StringProperty(required=True)


class ShotChunk(ndb.Model):
    chunk = ndb.BlobProperty(required=True)


class Shot(ndb.Model):

    @classmethod
    def get_by_key(cls, key):
        key = ndb.Key(urlsafe=key)
        return cls.query(cls.key == key).get()

    user = ndb.UserProperty(required=True)
    image = ndb.BlobProperty()
    split_image = ndb.KeyProperty(repeated=True)

    pub_date = ndb.DateTimeProperty(verbose_name='date published',
                                   auto_now_add=True)

    def set_image_and_save(self, chunks):
        self.key = allocate_key(type(self))
        self.split_image = []
        futures = []
        # Cut the image into chunks.
        for chunk in chunks:
            shot_chunk = ShotChunk(chunk=chunk, key=allocate_key(ShotChunk))
            futures.append(shot_chunk.put_async())
            self.split_image.append(shot_chunk.key)

        futures.append(self.put_async())
        # wait for all futures to complete
        for future in futures:
            future.get_result()

    def get_image(self):
        # legacy unchunked images. we only create chunked ones now for a simpler
        # codepath
        if self.image:
            return self.image
        # Reassemble the chunked image.
        chunks = ndb.get_multi(self.split_image)
        return ''.join(chunk.chunk for chunk in chunks)


def allocate_key(model_cls):
    return ndb.Key(model_cls, model_cls.allocate_ids(1)[0])
