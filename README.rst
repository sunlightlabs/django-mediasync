
================
django-mediasync
================

One of the more significant development roadblocks we have relates to local vs. 
deployed media. Ideally all media (graphics, css, scripts) development would 
occur locally and not use production media. Then, when ready to deploy, the 
media should be pushed to production. That way there can be significant changes 
to media without disturbing the production web site.

The goal of mediasync is to develop locally and then flip a switch in production 
that makes all the media URLs point to remote media URLs instead of the local 
media directory.

All code is under a BSD-style license, see LICENSE for details.

Source: http://github.com/sunlightlabs/django-mediasync/


------------
Requirements
------------

* django >= 1.0
* boto >= 1.8d
* slimmer == 0.1.30 (optional)
* python-cloudfiles == 1.7.5 (optional, for Rackspace Cloud Files backend)

----------------------------
Upgrading from mediasync 1.x
----------------------------

#. Update your mediasync settings as described in the next section.
#. Run *./manage.py syncmedia --force* to force updates of all files:
	* gzip instead of deflate compression
	* sync both compressed and original versions of files
#. add "django.core.context_processors.request" to TEMPLATE_CONTEXT_PROCESSORS

-------------
Configuration
-------------

settings.py
===========

Add to *INSTALLED_APPS*::

    'mediasync'

Add to *TEMPLATE_CONTEXT_PROCESSORS*::

	'django.core.context_processors.request'

Make sure your *STATIC_ROOT* setting is the correct path to your media::

    STATIC_ROOT = '/path/to/media'

When media is being served locally (instead of from S3 or Cloud Files), 
mediasync serves media through a Django view. Set your *STATIC_URL* to what 
you'd like that local media URL to be. This can be whatever you'd like, as long 
as you're using the {% media_url %} tag (more details on this later)::

	STATIC_URL = '/devmedia/'

*STATIC_URL* is the URL that will be used in debug mode. Otherwise, 
the *STATIC_URL* will be loaded from the backend settings.

The following settings dict must also be added::

    MEDIASYNC = {
        'BACKEND': 'path.to.backend',
    }

If you want to use a different media URL than that specified 
in *settings.STATIC_URL*, you can add *STATIC_URL* to the *MEDIASYNC* 
settings dict::

    MEDIASYNC = {
        ...
        'STATIC_URL': '/url/to/media/', # becomes http://yourhost.com/url/to/media/
        ...
    }

Same goes for *STATIC_ROOT*::

    MEDIASYNC = {
        ...
        'STATIC_ROOT': '/path/to/media/',
        ...
    }

mediasync supports pluggable backends. Please see below for information on 
the provided backends as well as directions on implementing your own.

Media expiration
----------------

If the client supports media expiration, all files are set to expire 365 days 
after the file was synced. You may override this value by adding 
*EXPIRATION_DAYS* to the MEDIASYNC settings dict.

::

    # Expire in 10 years.
    MEDIASYNC['EXPIRATION_DAYS'] = 365 * 10

Serving media remote (S3/Cloud Files) or locally
------------------------------------------------

The media URL is selected based on the *SERVE_REMOTE* attribute in the
*MEDIASYNC* dict in settings.py. When *True*, media will be served locally 
instead of from S3.

::

    # This would force mediasync to serve all media through the value
    # specified in settings.STATIC_URL.
    MEDIASYNC['SERVE_REMOTE'] = False
    
    # This would serve all media through S3/Cloud Files.
    MEDIASYNC['SERVE_REMOTE'] = True
    
    # This would serve media locally while in DEBUG mode, and remotely when
    # in production (DEBUG == False).
    MEDIASYNC['SERVE_REMOTE'] = not DEBUG
    
When serving files locally, you can emulate the CSS/JS combo/minifying
behavior we get from using media processors by specifying the following.

::

    MEDIASYNC['SERVE_REMOTE'] = False
    MEDIASYNC['EMULATE_COMBO'] = True

Note that this will only work if your *STATIC_URL* is pointing at your
Django dev server. Also keep in mind that some processors may take a while,
and is best used to check things over before rolling out to production.

DOCTYPE
-------

link and script tags are written using XHTML syntax. The rendering can be 
overridden by using the *DOCTYPE* setting. Allowed values are *'html4'*, 
*'html5'*, or *'xhtml'*. The default in mediasync 2.0 is html5, just as
the DOCTYPE on your site should be.

::

    MEDIASYNC['DOCTYPE'] = 'html5'

For each doctype, the following tags are rendered:

html4
~~~~~

::

    <link rel="stylesheet" href="..." type="text/css" media="...">
    <script type="text/javascript" charset="utf-8" src="..."></script>

html5
~~~~~

::

    <link rel="stylesheet" href="..." type="text/css" media="...">
    <script src="..."></script>

xhtml
~~~~~

::

    <link rel="stylesheet" href="..." type="text/css" media="..." />
    <script type="text/javascript" charset="utf-8" src="..."></script>


SSL
---

mediasync will attempt to intelligently determine if your media should be
served using HTTPS. In order to use automatic SSL detection,
*django.core.context_processors.request* must be added to
*TEMPLATE_CONTEXT_PROCESSORS* in settings.py::

    TEMPLATE_CONTEXT_PROCESSORS = (
        ...
        'django.core.context_processors.request',
        ...
    )

The *USE_SSL* mediasync setting can be used to override the SSL
URL detection.

::

    # Force HTTPS.
    MEDIASYNC['USE_SSL'] = True 

or

:: 

    # Force HTTP.
    MEDIASYNC['USE_SSL'] = False

Some backends will be unable to use SSL. In these cases *USE_SSL* and SSL
detection will be ignored.

Backends
========

mediasync now supports pluggable backends. A backend is a Python module that 
contains a Client class that implements a mediasync-provided BaseClient class.

S3
--

::

    MEDIASYNC['BACKEND'] = 'mediasync.backends.s3'

Settings
~~~~~~~~

The following settings are required in the mediasync settings dict::

    MEDIASYNC = {
    	'AWS_KEY': "s3_key",
    	'AWS_SECRET': "s3_secret",
    	'AWS_BUCKET': "bucket_name",
    }

Optionally you may specify a path prefix::

	MEDIASYNC['AWS_PREFIX'] = "key_prefix"

Assuming a correct DNS CNAME entry, setting *AWS_BUCKET* to 
*assets.sunlightlabs.com* and *AWS_PREFIX* to *myproject/media* would 
sync the media directory to http://assets.sunlightlabs.com/myproject/media/.

Amazon allows users to create DNS CNAME entries to map custom domain names 
to an AWS bucket. MEDIASYNC can be configured to use the bucket as the media 
URL by setting *AWS_BUCKET_CNAME* to *True*.

::

	MEDIASYNC['AWS_BUCKET_CNAME'] = True

If you would prefer to not use gzip compression with the S3 client, it can be
disabled::

    MEDIASYNC['AWS_GZIP'] = False

Tips
~~~~

Since files are given a far future expires header, one needs a way to do 
"cache busting" when you want the browser to fetch new files before the expire 
date arrives.  One of the best and easiest ways to accomplish this is to alter 
the path to the media files with some sort of version string using the key 
prefix setting::

    MEDIASYNC['AWS_PREFIX'] = "myproject/media/v20001201"

Given that and the above DNS CNAME example, the media directory URL would end 
up being http://assets.sunlightlabs.com/myproject/media/v20001201/.  Whenever 
you need to update the media files, simply update the key prefix with a new 
versioned string.

A *CACHE_BUSTER* settings can be added to the main *MEDIASYNC* settings 
dict to add a query string parameter to all media URLs. The cache buster can 
either be a value or a callable which is passed the media URL as a parameter.

::

	MEDIASYNC['CACHE_BUSTER'] = 1234567890

The above setting will generate a media path similar to::

	http://yourhost.com/url/to/media/image.png?1234567890
	
An important thing to note is that if you're running your Django site in a
multi-threaded or multi-node setup, you'll want to be careful about using a 
time-based cache buster value. Each worker/thread will probably have a slightly 
different value for datetime.now(), which means your users will find themselves
having cache misses randomly from page to page. 

Rackspace Cloud Files
---------------------

::

    MEDIASYNC['BACKEND'] = 'mediasync.backends.cloudfiles'

Settings
~~~~~~~~

The following settings are required in the mediasync settings dict::

    MEDIASYNC = {
    	'CLOUDFILES_CONTAINER': 'container_name',
    	'CLOUDFILES_USERNAME': 'cf_username',
    	'CLOUDFILES_API_KEY': 'cf_apikey',
    }

Tips
~~~~

The Cloud Files backend lacks support for the following features:

* setting HTTP Expires header
* setting HTTP Cache-Control header
* content compression (gzip)
* SSL support
* conditional sync based on file checksum

Custom backends
---------------

You can create a custom backend by creating a Python module containing a Client 
class. This class must inherit from mediasync.backends.BaseClient. Additionally, 
you must implement two methods::

	def remote_media_url(self, with_ssl):
	    ...

*remote_media_url* returns the full base URL for remote media. This can be 
either a static URL or one generated from mediasync settings::

	def put(self, filedata, content_type, remote_path, force=False):
	    ...

put is responsible for pushing a file to the backend storage.

* filedata - the contents of the file
* content_type - the mime type of the file
* remote_path - the remote path (relative from remote_media_url) to which 
  the file should be written
* force - if True, write file to remote storage even if it already exists

If the client supports gzipped content, you will need to override supports_gzip
to return True::

	def supports_gzip(self):
		return True

File Processors
===============

File processors allow you to modify the content of a file as it is being
synced or served statically. 

Mediasync ships with two processor modules, each of which defines two
processors for minifying both CSS and Javascript files:

1. ``slim`` is a minifier written in Python and requires the
   `slimmer` Python package. The Python package can be found here:
   http://pypi.python.org/pypi/slimmer/

2. ``yuicompressor`` is a minifier written in Java and can be downloaded
   from YUI's download page: http://developer.yahoo.com/yui/compressor/.
   This processor also requires an additional setting, as defined below.
   `yuicompressor` is new and should be considered experimental until 
   the mediasync 2.1 release.

Custom processors can be specified using the *PROCESSORS* entry in the
mediasync settings dict. *PROCESSORS* should be a list of processor entries.
Each processor entry can be a callable or a string path to a callable. If the
path is to a class definition, the class will be instantiated into an object.
The processor callable should return a string of the processed file data, None
if it chooses to not process the file, or raise *mediasync.SyncException* if
something goes terribly wrong. The callable should take the following arguments::

	def proc(filedata, content_type, remote_path, is_active):
		...

filedata
	the content of the file as a string

content_type
	the mimetype of the file being processed

remote_path
	the path to which the file is being synced (contains the file name)

is_active
	True if the processor should... process

If the *PROCESSORS* setting is used, you will need to include the defaults
if you plan on using them::

	'PROCESSORS': (
	    'mediasync.processors.slim.css_minifier',
	    'mediasync.processors.slim.js_minifier',
		...
	),

Mediasync will attempt to use `slimmer` by default if you leave it out of
your settings.  If it is on your Python path it will get used.

**EXPERIMENTAL**

To configure YUI Compressor you need to define a `PROCESSORS` and
`YUI_COMPRESSOR_PATH` as follows, assuming you placed the ".jar" file in
your `~/bin` path::

    'PROCESSORS': ('mediasync.processors.yuicompressor.css_minifier',
                   'mediasync.processors.yuicompressor.js_minifier'),
    'YUI_COMPRESSOR_PATH': '~/bin/yuicompressor.jar',

urls.py
=======

Add a reference to mediasync.urls in your main urls.py file.

::

    urlpatterns = ('',
        ...
        url(r'^', include('mediasync.urls)),
        ...
    )


--------
Features
--------

Ignored Directories
===================

Any directory in *STATIC_ROOT* that is hidden or starts with an underscore 
will be ignored during syncing.


Template Tags
=============

When referring to media in HTML templates you can use custom template tags. 
These tags can by accessed by loading the media template tag collection.

::

	{% load media %}

If you'd like to make the mediasync tags global, you can add the following to
your master urls.py file::

    from django.template import add_to_builtins
    add_to_builtins('mediasync.templatetags.media')

Some backends (S3) support https URLs when the requesting page is secure.
In order for the https to be detected, the request must be placed in the
template context with the key 'request'. This can be done automatically by
adding 'django.core.context_processors.request' to *TEMPLATE_CONTEXT_PROCESSORS*
in settings.py

media_url
---------

Renders the STATIC_URL from settings.py with trailing slashes removed.

::

	<img src="{% media_url %}/images/stuff.png">

STATIC_URL takes an optional argument that is the media path. Using the argument
allows mediasync to add the CACHE_BUSTER to the URL if one is specified.

::

	<img src="{% media_url '/images/stuff.png' %}">

If *CACHE_BUSTER* is set to 12345, the above example will render as::

	<img src="http://assets.example.com/path/to/media/images/stuff.png?12345">
	
*NOTE*: Don't use this tag to serve CSS or JS files. Use the js and css tags
that were specifically designed for the purpose.


js
--

Renders a script tag with the correct include.

::

	{% js "myfile.js" %}


css
---

Renders a <link> tag to include the stylesheet. It takes an optional second 
parameter for the media attribute; the default media is "screen, projector".

::

	{% css "myfile.css" %}  
	{% css "myfile.css" "screen" %}  


css_print
---------

Shortcut to render as a print stylesheet.

::

	{% css_print "myfile.css" %}

which is equivalent to

::

	{% css "myfile.css" "print" %}

Writing Style Sheets
====================

Users are encouraged to write stylesheets using relative URLS. The media 
directory is synced with S3 as is, so relative local paths will still work 
when pushed remotely.

::

	background: url(../images/arrow_left.png);


Joined files
============

When serving media in production, it is beneficial to combine JavaScript and 
CSS into single files. This reduces the number of connections the browser needs 
to make to the web server. Fewer connections can dramatically decrease page 
load times and reduce the server-side load.

Joined files are specified in the *MEDIASYNC* dict using *JOINED*. This is
a dict that maps individual media to an alias for the joined files. 

::

    'JOINED': {
        'styles/joined.css': ['styles/reset.css','styles/text.css'],
        'scripts/joined.js': ['scripts/jquery.js','scripts/processing.js'],
    },

Files listed in *JOINED* will be combined and pushed to S3 with the name of 
the alias. The individual CSS files will also be pushed to S3. Aliases must end 
in either .css or .js in order for the content-type to be set appropriately.

The existing template tags may be used to refer to the joined media. Simply use 
the joined alias as the argument::

	{% css_print "joined.css" %}

When served locally, template tags will render an HTML tag for each of the files 
that make up the joined file::

	<link rel="stylesheet" href="/media/styles/reset.css" type="text/css" media="screen, projection" />
	<link rel="stylesheet" href="/media/styles/text.css" type="text/css" media="screen, projection" />

When served remotely, one HTML tag will be rendered with the name of the joined file::

	<link rel="stylesheet" href="http://bucket.s3.amazonaws.com/styles/joined.css" type="text/css" media="screen, projection" />

Smart GZIP for S3
=================

In previous versions of mediasync's S3 client, certain content was always pushed
in a compressed format. This can cause major issues with clients that do not
support gzip. New in version 2.0, mediasync will push both a gzipped and an
uncompressed version of the file to S3. The template tags look at the request
and direct the user to the appropriate file based on the ACCEPT_ENCODING HTTP
header. Assuming a file styles/layout.css, the following would be synced to S3::

	styles/layout.css
	styles/layout.css.gz

-----------------
Running MEDIASYNC
-----------------

::

    ./manage.py syncmedia

----------
Change Log
----------

2.1.0
=====

* default to using STATIC_URL and STATIC_ROOT (Django 1.3), falling back
  to MEDIA_URL and MEDIA_ROOT if the STATIC_* settings are not set
* add AWS_GZIP setting to optionally disable gzip compression in S3 client

Thanks to Rob Hudson and Dolan Antenucci for their contributions to this
release.

2.0.0
=====

* updated Rackspace Cloud Files backend
* use gzip instead of deflate for compression (better browser support)
* smart gzip client support detection
* add pluggable backends
* add pluggable file processors
* experimental YUI Compressor
* settings refactor
* allow override of *settings.MEDIA_URL*
* Improvements to the logic that decides which files to sync. Safely ignore
  a wider variety of hidden files/directories.
* Make template tags aware of whether the current page is SSL-secured. If it
  is, ask the backend for an SSL media URL (if implemented by your backend).
* made SERVE_REMOTE setting the sole factor in determining if
  media should be served locally or remotely
* add many more tests
* deprecate CSS_PATH and JS_PATH

Thanks to Greg Taylor, Peter Sanchez, Jonathan Drosdeck, Rich Leland,
and Rob Hudson for their contributions to this release.

1.0.1
=====

* add application/javascript and application/x-javascript to JavaScript
  mimetypes
* break out of CSS and JS mimetypes
* add support for HTTPS URLs to S3
* allow for storage of S3 keys in ~/.boto configuration file

Thanks to Rob Hudson and Peter Sanchez for their contributions.

1.0.0
=====

Initial release.
