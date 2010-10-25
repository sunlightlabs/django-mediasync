from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mediasync import TYPES_TO_COMPRESS
from mediasync.backends import BaseClient
import base64
import cStringIO
import datetime
import gzip
import hashlib

def _checksum(data):
    checksum = hashlib.md5(data)
    hexdigest = checksum.hexdigest()
    b64digest = base64.b64encode(checksum.digest())
    return (hexdigest, b64digest)

def _compress(s):
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    zfile.write(s)
    zfile.close()
    return zbuf.getvalue()

class Client(BaseClient):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        
        self.aws_bucket = self._settings.get('AWS_BUCKET', None)
        self.aws_prefix = self._settings.get('AWS_PREFIX', '').strip('/')
        self.aws_bucket_cname = self._settings.get('AWS_BUCKET_CNAME', False)
        
        assert self.aws_bucket
    
    def open(self):    
        
        key = self._settings.get("AWS_KEY", None)
        secret = self._settings.get("AWS_SECRET", None)
        
        try:
            _conn = S3Connection(key, secret)
        except AttributeError:
            raise ImproperlyConfigured("S3 keys not set and no boto config found.")
                
        self._bucket = _conn.create_bucket(self.aws_bucket)
    
    def remote_media_url(self, with_ssl=False):
        """
        Returns the base remote media URL. In this case, we can safely make
        some assumptions on the URL string based on bucket names, and having
        public ACL on.
        
        args:
          with_ssl: (bool) If True, return an HTTPS url.
        """
        protocol = 'http' if with_ssl is False else 'https'
        url = (self.aws_bucket_cname and "%s://%s" or "%s://s3.amazonaws.com/%s") % (protocol, self.aws_bucket)
        if self.aws_prefix:
            url = "%s/%s" % (url, self.aws_prefix)
        return url

    def put(self, filedata, content_type, remote_path, force=False):

        now = datetime.datetime.utcnow()
        then = now + datetime.timedelta(self.expiration_days)
        expires = then.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        if self.aws_prefix:
            remote_path = "%s/%s" % (self.aws_prefix, remote_path)
            
        (hexdigest, b64digest) = _checksum(filedata)
        raw_b64digest = b64digest # store raw b64digest to add as file metadata

        # create initial set of headers
        headers = {
            "x-amz-acl": "public-read",
            "Content-Type": content_type,
            "Expires": expires,
            "Cache-Control": 'max-age=%d' % (self.expiration_days * 24 * 3600),
        }

        # check to see if file should be gzipped based on content_type
        # also check to see if filesize is greater than 1kb
        if content_type in TYPES_TO_COMPRESS and len(filedata) > 1024:
            filedata = _compress(filedata)
            headers["Content-Encoding"] = "gzip"
            (hexdigest, b64digest) = _checksum(filedata) # update checksum with compressed data
        
        key = self._bucket.get_key(remote_path)
        
        if key is None:
            key = Key(self._bucket)
            key.key = remote_path
        
        if force or key.get_metadata('mediasync-checksum') != raw_b64digest:
            
            key.set_metadata('mediasync-checksum', raw_b64digest)
            key.set_contents_from_string(filedata, headers=headers, md5=(hexdigest, b64digest))
        
            return True
