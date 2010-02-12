from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
from mediasync import JS_MIMETYPES, CSS_MIMETYPES, TYPES_TO_COMPRESS
from mediasync.backends import BaseClient
import base64
import datetime
import hashlib
import zlib

class Client(BaseClient):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        
        self.aws_key = self._settings.get("AWS_KEY", None)
        self.aws_secret = self._settings.get("AWS_SECRET", None)        
        self.aws_bucket = self._settings.get('AWS_BUCKET', None)
        self.aws_prefix = self._settings.get('AWS_PREFIX', '').strip('/')
        self.bucket_cname = self._settings.get('BUCKET_CNAME', False)
        
        assert self.aws_bucket
    
    def remote_media_url(self):
        url = (self.bucket_cname and "http://%s" or "http://%s.s3.amazonaws.com") % self.aws_bucket
        if self.aws_prefix:
            url = "%s/%s" % (url, self.aws_prefix)
        return url        
            
    def put(self, filedata, content_type, remote_path, force=False):

        now = datetime.datetime.utcnow()
        then = now + datetime.timedelta(EXPIRATION_DAYS)
        expires = then.strftime("%a, %d %b %Y %H:%M:%S GMT")

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
