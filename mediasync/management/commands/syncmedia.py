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
    
def compress(data):
    zbuf = cStringIO.StringIO()
    zfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
    zfile.write(data)
    zfile.close()
    return zbuf.getvalue()

def listdir_recursive(dir):
    for root, dirs, files in os.walk(dir):
        for file in files:
            fname = os.path.join(root, file).replace(dir, '')
            if fname.startswith('/'):
                fname = fname[1:]
            yield fname


class Command(BaseCommand):
    
    help = "Sync local media with S3"
    args = '[bucket] ([prefix])'
    
    requires_model_validation = False
    
    def handle(self, bucket=None, prefix=None, *args, **options):

        import S3

        assert hasattr(settings, "PROJECT_ROOT")
        assert hasattr(settings, "MEDIASYNC_AWS_KEY")
        assert hasattr(settings, "MEDIASYNC_AWS_SECRET")
        
        if not bucket:
            bucket = getattr(settings, "MEDIASYNC_AWS_BUCKET", None)
            if not bucket:
                raise CommandError('Usage is mediasync %s' % self.args)
                
        if not prefix:
            prefix = getattr(settings, "MEDIASYNC_AWS_PREFIX", None)

        now = datetime.datetime.utcnow()
        then = now + datetime.timedelta(EXPIRATION_DAYS)
        expires = then.strftime("%a, %d %b %Y %H:%M:%S UTC")
        
        media_url = "http://%s" % bucket
        if prefix:
            media_url = "%s/%s" % (media_url, prefix.strip('/'))
            
        s3root = prefix and prefix.strip('/') or ''

        # create s3 connection
        conn = S3.AWSAuthConnection(settings.MEDIASYNC_AWS_KEY, settings.MEDIASYNC_AWS_SECRET)
        
        entries = dict([(entry.key, entry.etag.strip('"')) for entry in conn.list_bucket(bucket).entries])

        for dirname in DIRS_TO_SYNC:
            
            dirpath = "%s/media/%s" % (settings.PROJECT_ROOT, dirname)
            s3dirpath = ("%s/%s" % (s3root, dirname)).strip('/')
            
            if os.path.exists(dirpath):
               
                for filename in listdir_recursive(dirpath):
                    
                    filepath = os.path.join(dirpath, filename)
                    s3filepath = os.path.join(s3dirpath, filename)
                    
                    if filename.startswith('.') or not os.path.isfile(filepath):
                        continue
                        
                    filedata = open(filepath, 'rb').read()

                    content_type = mimetypes.guess_type(filename)[0]
                    if not content_type:
                        content_type = "text/plain"
                    
                    if content_type == "text/css" or filename.endswith('.htc'):
                        filedata = MEDIA_URL_RE.sub(r'%s/\1/' % media_url, filedata)
                    
                    if content_type == "text/css":
                        filedata = cssmin.cssmin(filedata)
                    elif content_type == "text/javascript":    
                        filedata = jsmin.jsmin(filedata)
                        
                    headers = {
                        "x-amz-acl": "public-read",
                        "Content-Type": content_type,
                        "Expires": expires,
                    }
                    
                    if content_type in TYPES_TO_COMPRESS:
                        filedata = compress(filedata)
                        headers["Content-Encoding"] = "gzip"
                    checksum = hashlib.md5(filedata).digest()    
                    headers["content-md5"] = b64encode(checksum)
                    
                    etag = entries.get(s3filepath, None)
                    if etag and etag.strip('"') == str(checksum).encode("hex"):
                            continue # files has not changed, do not upload

                    response = conn.put(bucket, s3filepath, S3.S3Object(filedata), headers)
                    print "[%s] %s" % (content_type, s3filepath)
