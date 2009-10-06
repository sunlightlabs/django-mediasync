from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from mediasync import MEDIA_URL
import warnings

JOINED = getattr(settings, "MEDIASYNC_JOINED", {})
SERVE_REMOTE = getattr(settings, "MEDIASYNC_SERVE_REMOTE", not settings.DEBUG)
DOCTYPE = getattr(settings, "MEDIASYNC_DOCTYPE", 'xhtml')

register = template.Library()

def mkpath(url, path, filename):
    if path:
        url = "%s/%s" % (url, path)
    return "%s/%s" % (url, filename)

#
# media stuff
#

@register.simple_tag
def media_url():
    return MEDIA_URL

#
# CSS related tags
#

LINK_ENDER = ' />' if DOCTYPE == 'xhtml' else '>'

def linktag(url, path, filename, media):
    params = (mkpath(url, path, filename), media, LINK_ENDER)
    return """<link rel="stylesheet" href="%s" type="text/css" media="%s"%s""" % params
    
@register.simple_tag
def css(filename, media="screen, projection"):
    css_path = getattr(settings, "MEDIASYNC_CSS_PATH", "").strip('/')
    if SERVE_REMOTE and filename in JOINED:
        return linktag(MEDIA_URL, css_path, filename, media)
    else:
        filenames = JOINED.get(filename, (filename,))
        return ' '.join((linktag(MEDIA_URL, css_path, fn, media) for fn in filenames))

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
    js_path = getattr(settings, "MEDIASYNC_JS_PATH", "").strip('/')
    if SERVE_REMOTE and filename in JOINED:
        return scripttag(MEDIA_URL, js_path, filename)
    else:
        filenames = JOINED.get(filename, (filename,))
        return ' '.join((scripttag(MEDIA_URL, js_path, fn) for fn in filenames))