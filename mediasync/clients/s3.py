from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mediasync.utils import cssmin, jsmin
import base64
import datetime
import hashlib
import zlib

JS_MIMETYPES = (
    "application/javascript",
    "text/javascript", # obsolete, see RFC 4329
)
CSS_MIMETYPES = (
    "text/css",
)
TYPES_TO_COMPRESS = (
    "application/json",
    "application/xml",
    "text/html",
    "text/plain",
    "text/xml",
) + JS_MIMETYPES + CSS_MIMETYPES

EXPIRATION_DAYS = getattr(settings, "MEDIASYNC_EXPIRATION_DAYS", 365)

class Client(object):
    
    def __init__(self, bucket_name, prefix=''):
        key = getattr(settings, "MEDIASYNC_AWS_KEY", None)
        secret = getattr(settings, "MEDIASYNC_AWS_SECRET", None)

        if key and secret:
            self._conn = S3Connection(key, secret)
        else:
            try:
                self._conn = S3Connection()
            except AttributeError:
                raise ImproperlyConfigured("S3 keys not set and no boto config found.")

        self._bucket = self._conn.create_bucket(bucket_name)
        self._prefix = prefix
                
        self._entries = { }
        for entry in self._bucket.list(self._prefix):
            self._entries[entry.key] = entry.etag.strip('"')
    
    def put(self, filedata, content_type, remote_path, force=False):
        
        now = datetime.datetime.utcnow()
        then = now + datetime.timedelta(EXPIRATION_DAYS)
        expires = then.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        # check to see if cssmin or jsmin should be run
        if content_type in CSS_MIMETYPES:
            filedata = cssmin.cssmin(filedata)
        elif content_type in JS_MIMETYPES:
            filedata = jsmin.jsmin(filedata)
        
        # create initial set of headers
        headers = {
            "x-amz-acl": "public-read",
            "Content-Type": content_type,
            "Expires": expires,
            "Cache-Control": 'max-age %d' % (EXPIRATION_DAYS * 24 * 3600),
        }
        
        # check to see if file should be gzipped based on content_type
        # also check to see if filesize is greater than 1kb
        if content_type in TYPES_TO_COMPRESS and len(filedata) > 1024:
            filedata = zlib.compress(filedata)[2:-4] # strip zlib header and checksum
            headers["Content-Encoding"] = "deflate"
        
        # calculate md5 digest of filedata
        checksum = hashlib.md5(filedata)
        hexdigest = checksum.hexdigest()
        b64digest = base64.b64encode(checksum.digest())

        # check to see if local file has changed from what is on S3
        etag = self._entries.get(remote_path, '')
        if force or etag != hexdigest:
        
            # upload file
            key = Key(self._bucket)
            key.key = remote_path
            key.set_contents_from_string(filedata, headers=headers, md5=(hexdigest, b64digest))
        
            self._entries[remote_path] = etag

            return True
        
