from boto.s3.connection import S3Connection
from boto.s3.key import Key
from django.core.exceptions import ImproperlyConfigured
from mediasync import TYPES_TO_COMPRESS
from mediasync.backends import BaseClient
from mediasync.conf import msettings
import mediasync
import datetime

class Client(BaseClient):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        
        self.aws_bucket = msettings['AWS_BUCKET']
        self.aws_prefix = msettings.get('AWS_PREFIX', '').strip('/')
        self.aws_bucket_cname =  msettings.get('AWS_BUCKET_CNAME', False)
        
        assert self.aws_bucket
    
    def supports_gzip(self):
        return msettings.get('AWS_GZIP', True)
    
    def get_connection(self):
        return self._conn
    
    def open(self):    
        
        key = msettings['AWS_KEY']
        secret = msettings['AWS_SECRET']
        
        try:
            self._conn = S3Connection(key, secret)
        except AttributeError:
            raise ImproperlyConfigured("S3 keys not set and no boto config found.")
                
        self._bucket = self._conn.create_bucket(self.aws_bucket)
    
    def close(self):
        self._bucket = None
        self._conn = None
    
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
            
        (hexdigest, b64digest) = mediasync.checksum(filedata)
        raw_b64digest = b64digest # store raw b64digest to add as file metadata

        # create initial set of headers
        headers = {
            "x-amz-acl": "public-read",
            "Content-Type": content_type,
            "Expires": expires,
            "Cache-Control": 'max-age=%d' % (self.expiration_days * 24 * 3600),
        }
        
        key = self._bucket.get_key(remote_path)
        
        if key is None:
            key = Key(self._bucket, remote_path)
        
        key_meta = key.get_metadata('mediasync-checksum') or ''
        s3_checksum = key_meta.replace(' ', '+')
        if force or s3_checksum != raw_b64digest:
            
            key.set_metadata('mediasync-checksum', raw_b64digest)
            key.set_contents_from_string(filedata, headers=headers, md5=(hexdigest, b64digest))
        
            # check to see if file should be gzipped based on content_type
            # also check to see if filesize is greater than 1kb
            if content_type in TYPES_TO_COMPRESS:
                
                key = Key(self._bucket, "%s.gz" % remote_path)
                
                filedata = mediasync.compress(filedata)
                (hexdigest, b64digest) = mediasync.checksum(filedata) # update checksum with compressed data
                headers["Content-Disposition"] = 'inline; filename="%sgz"' % remote_path.split('/')[-1]
                headers["Content-Encoding"] = 'gzip'
                
                key.set_metadata('mediasync-checksum', raw_b64digest)
                key.set_contents_from_string(filedata, headers=headers, md5=(hexdigest, b64digest))
            
            return True
