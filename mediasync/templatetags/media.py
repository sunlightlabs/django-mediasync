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

CSS_PATH = mediasync_settings.get("CSS_PATH", "")
JS_PATH = mediasync_settings.get("JS_PATH", "")

register = template.Library()

def mkpath(url, path, filename):
    if path:
        url = "%s/%s" % (url.rstrip('/'), path.strip('/'))
    url = "%s/%s" % (url, filename.lstrip('/'))
    return URL_PROCESSOR(url)

#
# media stuff
#

@register.simple_tag
def media_url():
    return MEDIA_URL

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