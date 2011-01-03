from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mediasync import backends
from mediasync.backends import BaseClient
import mediasync
import os
import sys
import unittest

class Client(BaseClient):
    
    def put(self, filedata, content_type, remote_path, force=False):
        return True
        
    def remote_media_url(self, with_ssl=False):
        return ''

#
# tests
#

class BaseTestCase(unittest.TestCase):
    
    def testInvalidBackend(self):
        settings.MEDIASYNC = {
            'BACKEND': 'not.a.backend',
        }
        self.assertRaises(ImproperlyConfigured, backends.client)

class DummyBackendTestCase(unittest.TestCase):
    
    def setUp(self):
        settings.DEBUG = False
        settings.MEDIASYNC = {
            'BACKEND': 'mediasync.backends.dummy',
        }
        self.client = backends.client()
    
    def testPush(self):
        
        def callback(*args):
            pass
        
        self.client.put_callback = callback
        mediasync.sync(self.client)
    
    def testJoinedPush(self):
        pass

class MockClientTestCase(unittest.TestCase):
    
    def setUp(self):
        settings.MEDIASYNC['BACKEND'] = 'mediasync.tests.tests'
        self.client = backends.client()
    
class S3BackendTestCase(unittest.TestCase):

    def setUp(self):
        settings.DEBUG = False
        settings.MEDIASYNC = {
            'BACKEND': 'mediasync.backends.s3',
            'AWS_BUCKET': 'mediasync_test',
            'AWS_KEY': os.environ['AWS_KEY'],
            'AWS_SECRET': os.environ['AWS_SECRET'],
        }
        self.client = backends.client()
        
    def testMediaURL(self):
        
        try:
            del settings.MEDIASYNC['SERVE_REMOTE']
        except KeyError:
            pass
            
        settings.DEBUG = True
        self.assertEqual(backends.client().media_url(), '/media')
        
        settings.DEBUG = False
        self.assertEqual(backends.client().media_url(), 'http://s3.amazonaws.com/mediasync_test')
    
    def testServeRemote(self):
        
        settings.DEBUG = False
        settings.MEDIASYNC['SERVE_REMOTE'] = False
        self.assertEqual(backends.client().media_url(), '/media')
        
        settings.DEBUG = True
        settings.MEDIASYNC['SERVE_REMOTE'] = True
        self.assertEqual(backends.client().media_url(), 'http://s3.amazonaws.com/mediasync_test')
    
    def testMissingBucket(self):
        del settings.MEDIASYNC['AWS_BUCKET']
        self.assertRaises(AssertionError, backends.client)

class ProcessorTestCase(unittest.TestCase):
    
    def setUp(self):
        
        settings.MEDIASYNC['PROCESSORS'] = (
            'mediasync.processors.css_minifier',
            'mediasync.processors.js_minifier',
            lambda fd, ct, rp, r: fd.upper(),
        )
        self.client = backends.client()
    
    def testJSProcessor(self):
        
        try:
            import slimmer
        except ImportError:
            self.skipTest("slimmer not installed, skipping test")
        
        content = """var foo = function() {
            alert(1);
        };"""
        
        ct = 'text/javascript'
        procd = self.client.process(content, ct, 'test.js')
        self.assertEqual(procd, 'VAR FOO = FUNCTION(){ALERT(1)};')
    
    def testCSSProcessor(self):
        
        try:
            import slimmer
        except ImportError:
            self.skipTest("slimmer not installed, skipping test")
        
        content = """html {
            border: 1px solid #000000;
            font-family: "Helvetica", "Arial", sans-serif;
        }"""

        ct = 'text/css'
        procd = self.client.process(content, ct, 'test.css')
        self.assertEqual(procd, 'HTML{BORDER:1PX SOLID #000;FONT-FAMILY:"HELVETICA","ARIAL",SANS-SERIF}')
    
    def testCustomProcessor(self):
        procd = self.client.process('asdf', 'text/plain', 'asdf.txt')
        self.assertEqual(procd, "ASDF")
        