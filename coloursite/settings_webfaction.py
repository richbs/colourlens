# Django settings for coloursite project.
from settings import *

import os
BASE_DIR = os.path.dirname(__file__)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['colourlens.org', 'www.colourlens.org']

CACHES = {
    'default': {
       'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),
        'TIMEOUT': 60 * 60,
        'OPTIONS': {
            'MAX_ENTRIES': 5000,
            'CULL_FREQUENCY': 5,
        }
    }
}

