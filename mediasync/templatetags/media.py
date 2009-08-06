from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from mediasync import MEDIA_URL

JOINED = getattr(settings, "MEDIASYNC_JOINED", {})
SERVE_REMOTE = getattr(settings, "MEDIASYNC_SERVE_REMOTE", not settings.DEBUG)

register = template.Library()

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
    return """<link rel="stylesheet" href="%s%s/%s" type="text/css" media="%s" />""" % (url, path, filename, media)
    
@register.simple_tag
def css(filename, media="screen, projection"):
    css_path = getattr(settings, "MEDIA_CSS_PATH", "/styles").rstrip('/')
    if SERVE_REMOTE and filename in JOINED:
        return linktag(MEDIA_URL, css_path, filename, media)
    else:
        filenames = JOINED.get(filename, (filename,))
        return ' '.join((linktag(MEDIA_URL, css_path, fn, media) for fn in filenames))

@register.simple_tag
def css_print(filename):
    return css(filename, media="print")

@register.simple_tag
def css_ie(filename):
    return """<!--[if IE]>%s<![endif]-->""" % css(filename)

@register.simple_tag
def css_ie6(filename):
    return """<!--[if IE 6]>%s<![endif]-->""" % css(filename)

@register.simple_tag
def css_ie7(filename):
    return """<!--[if IE 7]>%s<![endif]-->""" % css(filename)

#
# JavaScript related tags
#

def scripttag(url, path, filename):
    return """<script type="text/javascript" charset="utf-8" src="%s%s/%s"></script>""" % (url, path, filename)
    
@register.simple_tag
def js(filename):
    js_path = getattr(settings, "MEDIA_JS_PATH", "/scripts").rstrip('/')
    if SERVE_REMOTE and filename in JOINED:
        return scripttag(MEDIA_URL, js_path, filename)
    else:
        filenames = JOINED.get(filename, (filename,))
        return ' '.join((scripttag(MEDIA_URL, js_path, fn) for fn in filenames))

#
# conditional tags
#

@register.tag
def ie(parser, token):
    condition_format = """<!--[if IE]>%s<![endif]-->"""
    return conditional(parser, token, condition_format, "endie")
    
@register.tag
def ie6(parser, token):
    condition_format = """<!--[if IE 6]>%s<![endif]-->"""
    return conditional(parser, token, condition_format, "endie6")
    
@register.tag
def ie7(parser, token):
    condition_format = """<!--[if IE 7]>%s<![endif]-->"""
    return conditional(parser, token, condition_format, "endie7")

def conditional(parser, token, condition_format, endtag):    
    newline = 'newline' in token.split_contents()
    nodelist = parser.parse((endtag,))
    parser.delete_first_token()
    return ConditionalNode(nodelist, condition_format, newline)

class ConditionalNode(template.Node):
    
    def __init__(self, nodelist, condition_format, newline=False):
        self.nodelist = nodelist
        self.condition_format = condition_format
        self.newline = newline

    def render(self, context):
        inner = self.nodelist.render(context)
        if self.newline:
            inner = "\n%s\n" % inner
        return self.condition_format % inner