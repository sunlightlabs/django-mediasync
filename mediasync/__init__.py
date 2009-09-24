from django.conf import settings
import os
import re

DIRS_TO_SYNC = ['images','scripts','styles']

SERVE_REMOTE = getattr(settings, "MEDIASYNC_SERVE_REMOTE", not settings.DEBUG)
BUCKET_CNAME = getattr(settings, "MEDIASYNC_BUCKET_CNAME", False)
AWS_PREFIX = getattr(settings, "MEDIASYNC_AWS_PREFIX", None)

if SERVE_REMOTE:
    assert hasattr(settings, "MEDIASYNC_AWS_BUCKET")
    mu = (BUCKET_CNAME and "http://%s" or "http://%s.s3.amazonaws.com") % settings.MEDIASYNC_AWS_BUCKET
    if AWS_PREFIX:
        mu = "%s/%s" % (mu, AWS_PREFIX)
else:
    mu = settings.MEDIA_URL

MEDIA_URL = mu.rstrip('/')

def listdir_recursive(dir):
    for root, dirs, files in os.walk(dir):
        for file in files:
            if not "/." in root:
                fname = os.path.join(root, file).replace(dir, '')
                if fname.startswith('/'):
                    fname = fname[1:]
                yield fname

def sync(bucket=None, prefix=''):
    """ Let's face it... pushing this stuff to S3 is messy.
        A lot of different things need to be calculated for each file
        and they have to be in a certain order as some variables rely
        on others.
    """
    
    from django.conf import settings
    from mediasync import s3
    import cStringIO
    
    assert hasattr(settings, "MEDIA_ROOT")
    assert hasattr(settings, "MEDIASYNC_AWS_KEY")
    assert hasattr(settings, "MEDIASYNC_AWS_SECRET")
    
    CSS_PATH = getattr(settings, "MEDIASYNC_CSS_PATH", "scripts").strip('/')
    JS_PATH = getattr(settings, "MEDIASYNC_JS_PATH", "scripts").strip('/')
        
    # check for bucket and prefix parameters
    
    if not bucket:
        bucket = getattr(settings, "MEDIASYNC_AWS_BUCKET", None)
        if not bucket:
            raise ValueError("bucket is required")
            
    if not prefix:
        prefix = getattr(settings, "MEDIASYNC_AWS_PREFIX", '').strip('/')
    
    # construct media url
    bucket_cname = getattr(settings, "MEDIASYNC_BUCKET_CNAME", False)
    media_url = (bucket_cname and "http://%s" or "http://%s.s3.amazonaws.com") % bucket
    if prefix:
        media_url = "%s/%s" % (media_url, prefix)
    
    # create s3 connection
    client = s3.Client(settings.MEDIASYNC_AWS_KEY, settings.MEDIASYNC_AWS_SECRET, bucket, prefix)

    #
    # sync joined media
    #
    
    joined = getattr(settings, "MEDIASYNC_JOINED", {})
    
    for destfile, sourcefiles in joined.iteritems():
        
        destfile = destfile.strip('/')
        
        if destfile.endswith('.css'):
            dirname = CSS_PATH
        elif destfile.endswith('.js'):
            dirname = JS_PATH
        else:
            continue # bypass this file since we only join css and js
        
        buffer = cStringIO.StringIO()
        
        for sourcefile in sourcefiles:
            
            sourcepath = os.path.join(settings.MEDIA_ROOT, dirname, sourcefile)
            if os.path.isfile(sourcepath):
                f = open(sourcepath)
                buffer.write(f.read())
                f.close()
                buffer.write('\n')        
        
        filedata = buffer.getvalue()
        buffer.close()
        
        s3filepath = prefix
        if dirname:
            s3filepath = "%s/%s" % (s3filepath, dirname)
        s3filepath = "%s/%s" % (s3filepath, destfile)
        
        _sync_file(client, destfile, s3filepath, filedata)
        
    #
    # sync static media
    #

    #for dirname in DIRS_TO_SYNC:
    for dirname in os.listdir(settings.MEDIA_ROOT):
        
        if dirname.startswith('.') or dirname.startswith('_'):
            continue # ignore hidden or directories that are not meant to be synced
        
        dirpath = os.path.join(settings.MEDIA_ROOT, dirname)
        
        if os.path.isdir(dirpath):
           
            for filename in listdir_recursive(dirpath):
                
                # calculate local and remote paths
                filepath = os.path.join(dirpath, filename)
                s3filepath = "%s/%s/%s" % (prefix, dirname, filename)
                
                if filename.startswith('.') or not os.path.isfile(filepath):
                    continue # hidden file or directory, do not upload
                
                _sync_file(client, filepath, s3filepath)
                

def _sync_file(client, filepath, remote_path, filedata=None):
    
    from django.conf import settings
    import mimetypes
                
    # load file data from local path
    if not filedata:
        filedata = open(filepath, 'rb').read()
    
    # guess the content type
    content_type = mimetypes.guess_type(filepath)[0]
    if not content_type:
        content_type = "text/plain"
    
    # rewrite CSS if the user chooses
    if getattr(settings, "MEDIASYNC_REWRITE_CSS", False): 
        if content_type == "text/css" or filepath.endswith('.htc'):
            MEDIA_URL_RE = re.compile(r"/media/\w+/")
            filedata = MEDIA_URL_RE.sub(r'%s/\1/' % media_url, filedata)
    
    if client.put(filedata, content_type, remote_path):
        print "[%s] %s" % (content_type, remote_path)

__all__ = ['MEDIA_URL','sync']