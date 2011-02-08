from django import template
from mediasync import backends
from mediasync.conf import msettings
import mediasync
import mimetypes

# Instance of the backend you configured in settings.py.
client = backends.client()

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
        'django.core.context_processors.request' must be added to
        TEMPLATE_CONTEXT_PROCESSORS in settings.py.
        """
        return 'request' in context and context['request'].is_secure()
    
    def supports_gzip(self, context):
        """
        Looks at the RequestContext object and determines if the client
        supports gzip encoded content. If the client does, we will send them
        to the gzipped version of files that are allowed to be compressed.
        Clients without gzip support will be served the original media.
        """
        if 'request' in context and client.supports_gzip():
            enc = context['request'].META.get('HTTP_ACCEPT_ENCODING', '')
            return 'gzip' in enc and msettings['SERVE_REMOTE']
        return False

    def get_media_url(self, context):
        """
        Checks to see whether to use the normal or the secure media source,
        depending on whether the current page view is being sent over SSL.
        The USE_SSL setting can be used to force HTTPS (True) or HTTP (False).
        
        NOTE: Not all backends implement SSL media. In this case, they'll just
        return an unencrypted URL.
        """
        use_ssl = msettings['USE_SSL']
        is_secure = use_ssl if use_ssl is not None else self.is_secure(context)
        return client.media_url(with_ssl=True) if is_secure else client.media_url()

    def mkpath(self, url, path, filename=None, gzip=False):
        """
        Assembles various components to form a complete resource URL.
        
        args:
          url: (str) A base media URL.
          path: (str) The path on the host (specified in 'url') leading up
                      to the file.
          filename: (str) The file name to serve.
          gzip: (bool) True if client should receive *.gz version of file.
        """
        if path:
            url = "%s/%s" % (url.rstrip('/'), path.strip('/'))

        if filename:
            url = "%s/%s" % (url, filename.lstrip('/'))
        
        content_type = mimetypes.guess_type(url)[0]
        if gzip and content_type in mediasync.TYPES_TO_COMPRESS:
            url = "%s.gz" % url

        cb = msettings['CACHE_BUSTER']
        if cb:
            # Cache busters help tell the client to re-download the file after
            # a change. This can either be a callable or a constant defined
            # in settings.py.
            cb_val = cb(url) if callable(cb) else cb
            url = "%s?%s" % (url, cb_val)

        return msettings['URL_PROCESSOR'](url)

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
    If msettings['SERVE_REMOTE'] == False, returns your STATIC_URL. 
    When msettings['SERVE_REMOTE'] == True, returns your storage 
    backend's remote URL (IE: S3 URL). 
    
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
            return self.mkpath(media_url, self.path, gzip=self.supports_gzip(context))

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
        css_path = msettings['CSS_PATH']
        joined = msettings['JOINED']
        
        if msettings['SERVE_REMOTE'] and self.path in joined:
            # Serving from S3/Cloud Files.
            return self.linktag(media_url, css_path, self.path, self.media_type, context)
        elif not msettings['SERVE_REMOTE'] and msettings['EMULATE_COMBO']:
            # Don't split the combo file into its component files. Emulate
            # the combo behavior, but generate/serve it locally. Useful for
            # testing combo CSS before deploying.
            return self.linktag(media_url, css_path, self.path, self.media_type, context)
        else:
            # If this is a combo file seen in the JOINED key on the
            # MEDIASYNC dict, break it apart into its component files and
            # write separate <link> tags for each.
            filenames = joined.get(self.path, (self.path,))
            return ' '.join((self.linktag(media_url, css_path, fn, self.media_type, context) for fn in filenames))

    def linktag(self, url, path, filename, media, context):
        """
        Renders a <link> tag for the stylesheet(s).
        """
        if msettings['DOCTYPE'] == 'xhtml':
            markup = """<link rel="stylesheet" href="%s" type="text/css" media="%s" />"""
        else:
            markup = """<link rel="stylesheet" href="%s" type="text/css" media="%s">"""
        return markup % (self.mkpath(url, path, filename, gzip=self.supports_gzip(context)), media)

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
        js_path = msettings['JS_PATH']
        joined = msettings['JOINED']

        if msettings['SERVE_REMOTE'] and self.path in joined:
            # Serving from S3/Cloud Files.
            return self.scripttag(media_url, js_path, self.path, context)
        elif not msettings['SERVE_REMOTE'] and msettings['EMULATE_COMBO']:
            # Don't split the combo file into its component files. Emulate
            # the combo behavior, but generate/serve it locally. Useful for
            # testing combo JS before deploying.
            return self.scripttag(media_url, js_path, self.path, context)
        else:
            # If this is a combo file seen in the JOINED key on the
            # MEDIASYNC dict, break it apart into its component files and
            # write separate <link> tags for each.
            filenames = joined.get(self.path, (self.path,))
            return ' '.join((self.scripttag(media_url, js_path, fn, context) for fn in filenames))

    def scripttag(self, url, path, filename, context):
        """
        Renders a <script> tag for the JS file(s).
        """
        if msettings['DOCTYPE'] == 'html5':
            markup = """<script src="%s"></script>"""
        else:
            markup = """<script type="text/javascript" charset="utf-8" src="%s"></script>"""
        return markup % self.mkpath(url, path, filename, gzip=self.supports_gzip(context))
