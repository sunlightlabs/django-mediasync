from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter

register = template.Library()

#
# media stuff
#

@register.simple_tag
def media_url():
    media_url = settings.MEDIA_URL.rstrip('/')
    return media_url

#
# CSS related tags
#

@register.simple_tag
def css(filename, media="screen, projection"):
    css_path = getattr(settings, "MEDIA_CSS_PATH", "/styles").rstrip('/')
    html = """<link rel="stylesheet" href="%s%s/%s" type="text/css" media="%s" />""" % (media_url(), css_path, filename, media)
    return html

@register.simple_tag
def css_print(filename):
    return css(filename, media="print")

@register.simple_tag
def css_ie(filename):
    return """<!--[if IE ]>%s<![endif]-->""" % css(filename)

@register.simple_tag
def css_ie6(filename):
    return """<!--[if IE 6]>%s<![endif]-->""" % css(filename)

@register.simple_tag
def css_ie7(filename):
    return """<!--[if IE 7]>%s<![endif]-->""" % css(filename)

#
# JavaScript related tags
#

@register.simple_tag
def js(filename):
    js_path = getattr(settings, "MEDIA_JS_PATH", "/scripts").rstrip('/')
    html = """<script type="text/javascript" charset="utf-8" src="%s%s/%s"></script>""" % (media_url(), js_path, filename)
    return html