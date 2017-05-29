from itertools import izip

from google.appengine.ext import ndb
from google.appengine.ext.deferred import defer

from deferred_util import BatchQueuer
from deferred_util import create_task
from deferred_util import enqueue_async
from deferred_util import wait_on_futures


GAE_BLOB_LIMIT = 1000*1000  # A little less than 1 MB.
TASK_QUEUE_SIZE_LIMIT = 1000*100 # 100KB


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

    @classmethod
    def create(cls, key, chunkstr):
        cls(chunk=chunkstr, key=key).put()


    chunk = ndb.BlobProperty(required=True)


class Shot(ndb.Model):

    @classmethod
    def get_by_key(cls, key):
        try:
            key = ndb.Key(urlsafe=key)
        except TypeError:
            return None
        return cls.query(cls.key == key).get()

    user = ndb.UserProperty(required=True)
    image = ndb.BlobProperty()
    split_image = ndb.KeyProperty(repeated=True)

    pub_date = ndb.DateTimeProperty(verbose_name='date published',
                                   auto_now_add=True)

    def set_image_and_save(self, upload_request):
        chunk_tasks = []
        self.key = allocate_key(type(self))
        self.split_image = []

        num_chunks = upload_request.num_chunks(TASK_QUEUE_SIZE_LIMIT)
        chunks = upload_request.chunks(TASK_QUEUE_SIZE_LIMIT)
        keys = allocate_keys(ShotChunk, num_chunks)
        with BatchQueuer(batch_size=30) as batch_queuer:
            for chunk, shot_chunk_key in izip(chunks, keys):
                batch_queuer.add(create_task(ShotChunk.create, shot_chunk_key, chunk))
                self.split_image.append(shot_chunk_key)
        wait_on_futures(batch_queuer.enqueued_task_futures + [self.put_async()])

    def get_image(self):
        # legacy unchunked images. we only create chunked ones now for a simpler
        # codepath
        if self.image:
            return self.image
        # Reassemble the chunked image.
        chunks = ndb.get_multi(self.split_image)
        incomplete_chunks = [chunk for chunk in chunks if not chunk]
        if incomplete_chunks:
            num_uploaded_chunks = len(chunks) - len(incomplete_chunks)
            raise ChunkStillUploadingError(len(chunks), num_uploaded_chunks)
        return ''.join(chunk.chunk for chunk in chunks)


class ChunkStillUploadingError(Exception):
    def __init__(self, num_total_chunks, num_uploaded_chunks):
        self.num_total_chunks = num_total_chunks
        self.num_uploaded_chunks = num_uploaded_chunks

def allocate_keys(model_cls, num_keys):
    first, last = model_cls.allocate_ids(num_keys)
    return [ndb.Key(model_cls, id) for id in xrange(first, last + 1)]


def allocate_key(model_cls):
    return allocate_keys(model_cls, 1)[0]
