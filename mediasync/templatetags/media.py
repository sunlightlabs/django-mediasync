from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from mediasync import backends
import warnings

mediasync_settings = getattr(settings, 'MEDIASYNC', {})

# Instance of the backend you configured in settings.py.
client = backends.client()

DOCTYPE = mediasync_settings.get("DOCTYPE", "xhtml")
JOINED = mediasync_settings.get("JOINED", {})
# Intelligently determines your base MEDIA_URL depending on your settings.
MEDIA_URL = client.media_url()
# This where to get SSL media for SSL pages.
SECURE_MEDIA_URL = client.media_url(with_ssl=True)
SERVE_REMOTE = client.serve_remote or not settings.DEBUG
URL_PROCESSOR = mediasync_settings.get("URL_PROCESSOR", lambda x: x)
CACHE_BUSTER = mediasync_settings.get("CACHE_BUSTER", None)

CSS_PATH = mediasync_settings.get("CSS_PATH", "")
JS_PATH = mediasync_settings.get("JS_PATH", "")

register = template.Library()

class BaseTagNode(template.Node):
    """
    Base class for all mediasync nodes.
    """
    def __init__(self, path):
        super(BaseTagNode, self).__init__()
        # This is the filename or path+filename supplied by the template call.
        self.path = path
        
    def is_secure(self, context):
        """
        Looks at the RequestContext object and determines if this page is
        secured with SSL. Linking unencrypted media on an encrypted page will
        show a warning icon on some browsers. We need to be able to serve from
        an encrypted source for encrypted pages, if our backend supports it.
        """
        return context['request'].is_secure()
    
    def get_media_url(self, context):
        """
        Checks to see whether to use the normal or the secure media source,
        depending on whether the current page view is being sent over SSL.
        
        NOTE: Not all backends implement SSL media. In this case, they'll just
        return an unencrypted URL.
        """
        return SECURE_MEDIA_URL if self.is_secure(context) else MEDIA_URL
        
    def mkpath(self, url, path, filename=None):
        """
        Assembles various components to form a complete resource URL.
        
        args:
          url: (str) A base media URL.
          path: (str) The path on the host (specified in 'url') leading up
                      to the file.
          filename: (str) The file name to serve.
        """
        if path:
            url = "%s/%s" % (url.rstrip('/'), path.strip('/'))

        if filename:
            url = "%s/%s" % (url, filename.lstrip('/'))

        if CACHE_BUSTER:
            # Cache busters help tell the client to re-download the file after
            # a change. This can either be a callable or a constant defined
            # in settings.py.
            cache_buster_val = CACHE_BUSTER(url) if callable(CACHE_BUSTER) else CACHE_BUSTER
            url = "%s?%s" % (url, cache_buster_val)

        return URL_PROCESSOR(url)
        
def get_path_from_tokens(token):
    """
    Just yanks the path out of a list of template tokens. Ignores any
    additional arguments.
    """
    tokens = token.split_contents()

    if len(tokens) > 1:
        # At least one argument. Only interested in the path, though.
        return tokens[1][1:-1]
    else:
        # No path provided in the tag call.
        return None

def media_url_tag(parser, token):
    """
    If developing locally, returns your MEDIA_URL. When DEBUG == False, or
    settings.MEDIASYNC['serve_remote'] == True, returns your storage backend's
    remote URL (IE: S3 URL). 
    
    If an argument is provided with the tag, it will be appended on the end
    of your media URL.
    
    *NOTE:* This tag returns a URL, not any kind of HTML tag.
    
    Usage:: 
    
        {% media_url ["path/and/file.ext"] %}
    
    Examples::
    
        {% media_url %}
        {% media_url "images/bunny.gif" %}
        {% media_url %}/themes/{{ theme_variable }}/style.css
    """
    return MediaUrlTagNode(get_path_from_tokens(token))
register.tag('media_url', media_url_tag)

class MediaUrlTagNode(BaseTagNode):
    """
    Node for the {% media_url %} tag. See the media_url_tag method above for
    documentation and examples.
    """
    def render(self, context):
        media_url = self.get_media_url(context)

        if not self.path:
            # No path provided, just return the base media URL.
            return media_url
        else:
            # File/path provided, return the assembled URL.
            return self.mkpath(media_url, self.path)

"""
# CSS related tags
"""

def css_tag(parser, token):
    """
    Renders a tag to include the stylesheet. It takes an optional second 
    parameter for the media attribute; the default media is "screen, projector".
    
    Usage::

        {% css "<somefile>.css" ["<projection type(s)>"] %}

    Examples::

        {% css "myfile.css" %}
        {% css "myfile.css" "screen, projection"%}
    """
    path = get_path_from_tokens(token)

    tokens = token.split_contents()    
    if len(tokens) > 2:
        # Get the media types from the tag call provided by the user.
        media_type = tokens[2][1:-1]
    else:
        # Default values.
        media_type = "screen, projection"

    return CssTagNode(path, media_type=media_type)
register.tag('css', css_tag)

def css_print_tag(parser, token):
    """
    Shortcut to render CSS as a print stylesheet.
    
    Usage::
    
        {% css_print "myfile.css" %}
        
    Which is equivalent to
    
        {% css "myfile.css" "print" %}
    """
    path = get_path_from_tokens(token)
    # Hard wired media type, since this is for media type of 'print'.
    media_type = "print"

    return CssTagNode(path, media_type=media_type)
register.tag('css_print', css_print_tag)

class CssTagNode(BaseTagNode):
    """
    Node for the {% css %} tag. See the css_tag method above for
    documentation and examples.
    """
    def __init__(self, *args, **kwargs):
        super(CssTagNode, self).__init__(*args)
        self.media_type = kwargs.get('media_type', "screen, projection")

    def render(self, context):
        media_url = self.get_media_url(context)

        if SERVE_REMOTE and self.path in JOINED:
            return self.linktag(media_url, CSS_PATH, self.path, self.media_type)
        else:
            filenames = JOINED.get(self.path, (self.path,))
            return ' '.join((self.linktag(media_url, CSS_PATH, fn, self.media_type) for fn in filenames))
        
    def linktag(self, url, path, filename, media):
        """
        Renders a <link> tag for the stylesheet(s).
        """
        if DOCTYPE == 'xhtml':
            markup = """<link rel="stylesheet" href="%s" type="text/css" media="%s" />"""
        else:
            markup = """<link rel="stylesheet" href="%s" type="text/css" media="%s">"""
        return markup % (self.mkpath(url, path, filename), media)

"""
# JavaScript related tags
"""

def js_tag(parser, token):
    """
    Renders a tag to include a JavaScript file.
    
    Usage::
    
        {% js "somefile.js" %}
        
    """
    return JsTagNode(get_path_from_tokens(token))
register.tag('js', js_tag)

class JsTagNode(BaseTagNode):
    """
    Node for the {% js %} tag. See the js_tag method above for
    documentation and examples.
    """
    def render(self, context):
        media_url = self.get_media_url(context)

        if SERVE_REMOTE and self.path in JOINED:
            return self.scripttag(media_url, JS_PATH, self.path)
        else:
            filenames = JOINED.get(self.path, (self.path,))
            return ' '.join((self.scripttag(media_url, JS_PATH, fn) for fn in filenames))
        
    def scripttag(self, url, path, filename):
        """
        Renders a <script> tag for the JS file(s).
        """
        if DOCTYPE == 'html5':
            markup = """<script src="%s"></script>"""
        else:
            markup = """<script type="text/javascript" charset="utf-8" src="%s"></script>"""
        return markup % self.mkpath(url, path, filename)
