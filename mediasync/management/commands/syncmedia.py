from base64 import b64encode
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from mediasync.utils import cssmin, jsmin
import cStringIO
import datetime
import gzip
import hashlib
import mimetypes
import os
import re

TYPES_TO_COMPRESS = (
    "application/javascript",
    "application/x-javascript",
    "application/xml",
    "text/css",
    "text/html",
    "text/plain",
)

DIRS_TO_SYNC = ['images','scripts','styles']

MEDIA_URL_RE = re.compile(r"/media/(images|styles|scripts)/")

EXPIRATION_DAYS = getattr(settings, "MEDIASYNC_EXPIRATION_DAYS", 365)
REWRITE_CSS = getattr(settings, "MEDIASYNC_REWRITE_CSS", False)
    
def compress(data):
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    zfile.write(data)
    zfile.close()
    gzdata = zbuf.getvalue()
    zbuf.close()
    return gzdata

def listdir_recursive(dir):
    for root, dirs, files in os.walk(dir):
        for file in files:
            if not "/." in root:
                fname = os.path.join(root, file).replace(dir, '')
                if fname.startswith('/'):
                    fname = fname[1:]
                yield fname


class Command(BaseCommand):
    
    help = "Sync local media with S3"
    args = '[bucket] ([prefix])'
    
    requires_model_validation = False
    
    def handle(self, bucket=None, prefix=None, *args, **options):
        """ Let's face it... pushing this stuff to S3 is messy.
            A lot of different things need to be calculated for each file
            and they have to be in a certain order as some variables rely
            on others.
        """

        from boto.s3.connection import S3Connection
        from boto.s3.key import Key

        assert hasattr(settings, "PROJECT_ROOT")
        assert hasattr(settings, "MEDIASYNC_AWS_KEY")
        assert hasattr(settings, "MEDIASYNC_AWS_SECRET")
        
        # check for bucket and prefix parameters
        
        if not bucket:
            bucket = getattr(settings, "MEDIASYNC_AWS_BUCKET", None)
            if not bucket:
                raise CommandError('Usage is mediasync %s' % self.args)
                
        if not prefix:
            prefix = getattr(settings, "MEDIASYNC_AWS_PREFIX", '').strip('/')

        # calculate timestamps and expires
        now = datetime.datetime.utcnow()
        then = now + datetime.timedelta(EXPIRATION_DAYS)
        expires = then.strftime("%a, %d %b %Y %H:%M:%S UTC")
        
        # construct media url
        bucket_cname = getattr(settings, "MEDIASYNC_BUCKET_CNAME", False)
        media_url = (bucket_cname and "http://%s" or "http://%s.s3.amazonaws.com") % bucket
        if prefix:
            media_url = "%s/%s" % (media_url, prefix)
        
        # create s3 connection
        s3conn = S3Connection(settings.MEDIASYNC_AWS_KEY, settings.MEDIASYNC_AWS_SECRET)
        s3bucket = s3conn.create_bucket(bucket)
        
        # get list of existing entires on S3
        entries = dict(((entry.key, entry.etag.strip('"')) for entry in s3bucket.list(prefix)))

        for dirname in DIRS_TO_SYNC:
            
            dirpath = "%s/media/%s" % (settings.PROJECT_ROOT, dirname)
            s3dirpath = ("%s/%s" % (prefix, dirname)).strip('/')
            
            if os.path.exists(dirpath):
               
                for filename in listdir_recursive(dirpath):
                    
                    # calculate local and remote paths
                    filepath = os.path.join(dirpath, filename)
                    s3filepath = os.path.join(s3dirpath, filename)
                    
                    if filename.startswith('.') or not os.path.isfile(filepath):
                        continue # hidden file or directory, do not upload
                    
                    # load file data from local path
                    filedata = open(filepath, 'rb').read()
                    
                    # guess the content type
                    content_type = mimetypes.guess_type(filename)[0]
                    if not content_type:
                        content_type = "text/plain"
                    
                    # rewrite CSS if the user chooses
                    if REWRITE_CSS: 
                        if content_type == "text/css" or filename.endswith('.htc'):
                            filedata = MEDIA_URL_RE.sub(r'%s/\1/' % media_url, filedata)
                    
                    # check to see if cssmin or jsmin should be run
                    if content_type == "text/css":
                        filedata = cssmin.cssmin(filedata)
                    elif content_type == "text/javascript":    
                        filedata = jsmin.jsmin(filedata)
                    
                    # create initial set of headers
                    headers = {
                        "x-amz-acl": "public-read",
                        "Content-Type": content_type,
                        "Expires": expires,
                    }
                    
                    # check to see if file should be gzipped based on content_type
                    if content_type in TYPES_TO_COMPRESS:
                        filedata = compress(filedata)
                        headers["Content-Encoding"] = "gzip"  
                    
                    # calculate md5 digest of filedata
                    checksum = hashlib.md5(filedata)
                    hexdigest = checksum.hexdigest()
                    b64digest = b64encode(checksum.digest())

                    # check to see if local file has changed from what is on S3
                    etag = entries.get(s3filepath, '')
                    if etag == hexdigest:
                        continue # files has not changed, do not upload 
                    
                    # upload file
                    key = Key(s3bucket)
                    key.key = s3filepath
                    key.set_contents_from_string(filedata, headers=headers, md5=(hexdigest, b64digest))
          
                    print "[%s] %s" % (content_type, s3filepath)
