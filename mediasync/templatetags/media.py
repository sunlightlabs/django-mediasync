from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from mediasync import backends
import warnings

mediasync_settings = getattr(settings, 'MEDIASYNC', {})

client = backends.client()

DOCTYPE = mediasync_settings.get("DOCTYPE", "xhtml")
JOINED = mediasync_settings.get("JOINED", {})
MEDIA_URL = client.media_url()
SERVE_REMOTE = client.serve_remote or not settings.DEBUG
URL_PROCESSOR = mediasync_settings.get("URL_PROCESSOR", lambda x: x)
CACHE_BUSTER = mediasync_settings.get("CACHE_BUSTER", None)

CSS_PATH = mediasync_settings.get("CSS_PATH", "")
JS_PATH = mediasync_settings.get("JS_PATH", "")

register = template.Library()

def mkpath(url, path, filename=None):
    if path:
        url = "%s/%s" % (url.rstrip('/'), path.strip('/'))
    if filename:
        url = "%s/%s" % (url, filename.lstrip('/'))
    if CACHE_BUSTER:
        url = "%s?%s" % (url, CACHE_BUSTER(url) if callable(CACHE_BUSTER) else CACHE_BUSTER)
    return URL_PROCESSOR(url)

#
# media stuff
#

def do_media_url2(parser, token):
    print "RAW", token.split_contents()
    tokens = token.split_contents()

    if len(tokens) > 1:
        # Tag only takes one argument. Discard the rest. Also, first and
        # last characters are quotes when a string is passed, lop those off.
        url_str = tokens[1][1:-1]
    else:
        url_str = None
    
    return MediaUrlNode(url_str)
register.tag('media_url2', do_media_url2)

class MediaUrlNode(template.Node):
    def __init__(self, url_str):
        self.url_str = url_str
    def render(self, context):
        is_secure = context['request'].is_secure()
        print "CONTEXT", is_secure

        if not self.url_str:
            print "RVAL", MEDIA_URL
            return MEDIA_URL
        print "RVAL", mkpath(MEDIA_URL, self.url_str, is_secure=is_secure)
        return mkpath(MEDIA_URL, self.url_str, is_secure=is_secure)

@register.simple_tag
def media_url(path=None):
    if not path:
        return MEDIA_URL
    return mkpath(MEDIA_URL, path)

#
# CSS related tags
#

def linktag(url, path, filename, media):
    if DOCTYPE == 'xhtml':
        markup = """<link rel="stylesheet" href="%s" type="text/css" media="%s" />"""
    else:
        markup = """<link rel="stylesheet" href="%s" type="text/css" media="%s">"""
    return  markup % (mkpath(url, path, filename), media)
    
@register.simple_tag
def css(filename, media="screen, projection"):
    if SERVE_REMOTE and filename in JOINED:
        return linktag(MEDIA_URL, CSS_PATH, filename, media)
    else:
        filenames = JOINED.get(filename, (filename,))
        return ' '.join((linktag(MEDIA_URL, CSS_PATH, fn, media) for fn in filenames))

@register.simple_tag
def css_print(filename):
    return css(filename, media="print")

#
# JavaScript related tags
#

def scripttag(url, path, filename):
    if DOCTYPE == 'html5':
        markup = """<script src="%s"></script>"""
    else:
        markup = """<script type="text/javascript" charset="utf-8" src="%s"></script>"""
    return markup % mkpath(url, path, filename)
    
@register.simple_tag
def js(filename):
    if SERVE_REMOTE and filename in JOINED:
        return scripttag(MEDIA_URL, JS_PATH, filename)
    else:
        filenames = JOINED.get(filename, (filename,))
        return ' '.join((scripttag(MEDIA_URL, JS_PATH, fn) for fn in filenames))