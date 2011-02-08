import os
TEST_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'mediasynctest.db'

STATIC_ROOT = os.path.join(TEST_ROOT, 'media')
STATIC_URL = '/media/'

MEDIASYNC = {
    'BACKEND': 'mediasync.backends.dummy',
}

INSTALLED_APPS = ('mediasync.tests',)
