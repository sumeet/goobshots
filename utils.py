import os
from hashlib import md5
from google.appengine.ext.webapp import template
from google.appengine.api import users
import models
import math
import random

def render(template_filename, template_values=None):
    return template.render(os.path.join(os.path.dirname(__file__), 'templates', template_filename), template_values)


def require_login(fn):
    def _dec(view_func):
        def _checklogin(request_handler, *args, **kwargs):
            user = users.get_current_user()
            if user:
                if not models.UserProfile.all().filter('user =', user).get():
                    models.UserProfile(user=users.get_current_user(), secret=md5(os.urandom(3000)).hexdigest()).put()
                return view_func(request_handler, *args, **kwargs)
            else:
                request_handler.redirect(users.create_login_url(request_handler.request.path))

        _checklogin.__doc__ = view_func.__doc__
        _checklogin.__dict__ = view_func.__dict__

        return _checklogin

    return _dec(fn)


def detect_mime_from_image_data(image):
    if image[1:4] == 'PNG':
        return 'image/png'

    if image[0:3] == 'GIF':
        return 'image/gif'

    if image[6:10] == 'JFIF':
        return 'image/jpeg'


def segment(x, n):
    i = 0
    c = len(x)

    while i < c:
        yield x[i:i+n]
        i += n
