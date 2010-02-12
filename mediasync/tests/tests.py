from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import mediasync
import unittest

class BaseTestCase(unittest.TestCase):
    
    def testInvalidBackend(self):
        settings.MEDIASYNC = {
            'BACKEND': 'not.a.backend',
        }
        self.assertRaises(ImproperlyConfigured, mediasync.client)

class DummyBackendTestCase(unittest.TestCase):
    
    def setUp(self):
        settings.DEBUG = False
        settings.MEDIASYNC = {
            'BACKEND': 'mediasync.backends.dummy',
        }
        self.client = mediasync.client()
    
    def testPush():
        pass

class S3BackendTestCase(unittest.TestCase):

    def setUp(self):
        settings.DEBUG = False
        settings.MEDIASYNC = {
            'BACKEND': 'mediasync.backends.s3',
            'AWS_BUCKET': 'mediasync_test',
        }
        self.client = mediasync.client()
        
    def testMediaURL(self):
        
        try:
            del settings.MEDIASYNC['SERVE_REMOTE']
        except KeyError:
            pass
            
        settings.DEBUG = True
        self.assertEqual(mediasync.client().media_url(), '/media')
        
        settings.DEBUG = False
        self.assertEqual(mediasync.client().media_url(), 'http://mediasync_test.s3.amazonaws.com')
    
    def testServeRemote(self):
        
        settings.DEBUG = False
        settings.MEDIASYNC['SERVE_REMOTE'] = False
        self.assertEqual(mediasync.client().media_url(), '/media')
        
        settings.DEBUG = True
        settings.MEDIASYNC['SERVE_REMOTE'] = True
        self.assertEqual(mediasync.client().media_url(), 'http://mediasync_test.s3.amazonaws.com')
    
    def testMissingBucket(self):
        del settings.MEDIASYNC['AWS_BUCKET']
        self.assertRaises(AssertionError, mediasync.client)
        
        