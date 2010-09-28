
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

-------------
Configuration
-------------


settings.py
===========

Add to *INSTALLED_APPS*::

	'mediasync'

Add the proper *MEDIA_ROOT* setting::

    MEDIA_ROOT = '/path/to/media'

Additionally, replace the existing *MEDIA_URL* setting with::

	MEDIA_URL = '/devmedia/'

*MEDIA_URL* is the URL that will be used in debug mode. Otherwise, 
the *MEDIA_URL* will be loaded from the backend settings.

The following settings dict must also be added::

	MEDIASYNC = {
		'BACKEND': 'path.to.backend',
	}

If you want to use a different media URL than that specified 
in *settings.MEDIA_URL*, you can add *MEDIA_URL* to the *MEDIASYNC* 
settings dict::

	MEDIASYNC = {
		...
		'MEDIA_URL': '/url/to/media/', # becomes http://yourhost.com/url/to/media/
		...
	}

Same goes for *MEDIA_ROOT*::

	MEDIASYNC = {
		...
		'MEDIA_ROOT': '/path/to/media/',
		...
	}

mediasync supports pluggable backends. Please see below for information on 
the provided backends as well as directions on implementing your own.

If the client supports media expiration, all files are set to expire 365 days 
after the file was synced. You may override this value by adding 
*EXPIRATION_DAYS* to the MEDIASYNC settings dict.

::

	'EXPIRATION_DAYS': 365 * 10, # expire in 10 years

The media URL is selected based on the *DEBUG* attribute in settings.py. 
When *True*, media will be served locally instead of from S3. Sometimes it is 
necessary to serve media from S3 even when *DEBUG* is *True*. To force remote 
serving of media, set *SERVE_REMOTE* to *True*.

::

	'SERVE_REMOTE': True,

DOCTYPE
-------

link and script tags are written using XHTML syntax. The rendering can be 
overridden by using the *DOCTYPE* setting. Allowed values are *'html4'*, 
*'html5'*, or *'xhtml'*.

::

	'DOCTYPE': 'xhtml',

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
served using HTTPS. In order to use automatic SSL detection, *django.core.context_processors.request*
must be added to *TEMPLATE_CONTEXT_PROCESSORS* in settings.py::

	TEMPLATE_CONTEXT_PROCESSORS = (
		...
		'django.core.context_processors.request',
		...
	)

The *USE_SSL* mediasync setting can be used to override the SSL
URL detection.

::

	'USE_SSL': True, # force HTTPS

or

:: 

	'USE_SSL': False, # force HTTP

Some backends will be unable to use SSL. In these cases *USE_SSL* and SSL
detection will be ignored.

Backends
========

mediasync now supports pluggable backends. A backend is a Python module that 
contains a Client class that implements a mediasync-provided BaseClient class.

S3
--

::

	'BACKEND': 'mediasync.backends.s3',

Settings
~~~~~~~~

The following settings are required in the mediasync settings dict::

	'AWS_KEY': "s3_key",
	'AWS_SECRET': "s3_secret",
	'AWS_BUCKET': "bucket_name",

Optionally you may specify a path prefix::

	'AWS_PREFIX': "key_prefix",

Assuming a correct DNS CNAME entry, setting *AWS_BUCKET* to 
*assets.sunlightlabs.com* and *AWS_PREFIX* to *myproject/media* would 
sync the media directory to http://assets.sunlightlabs.com/myproject/media/.

Amazon allows users to create DNS CNAME entries to map custom domain names 
to an AWS bucket. MEDIASYNC can be configured to use the bucket as the media 
URL by setting *AWS_BUCKET_CNAME* to *True*.

::

	'AWS_BUCKET_CNAME': True,

Tips
~~~~

Since files are given a far future expires header, one needs a way to do 
"cache busting" when you want the browser to fetch new files before the expire 
date arrives.  One of the best and easiest ways to accomplish this is to alter 
the path to the media files with some sort of version string using the key 
prefix setting::

    'AWS_PREFIX': "myproject/media/v20001201",

Given that and the above DNS CNAME example, the media directory URL would end 
up being http://assets.sunlightlabs.com/myproject/media/v20001201/.  Whenever 
you need to update the media files, simply update the key prefix with a new 
versioned string.

A *CACHE_BUSTER* settings can be added to the main *MEDIASYNC* settings 
dict to add a query string parameter to all media URLs. The cache buster can 
either be a value or a callable which is passed the media URL as a parameter.

::

	'CACHE_BUSTER': 1234567890,

The above setting will generate a media path similar to::

	http://yourhost.com/url/to/media/image.png?1234567890

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

File Processors
===============

File processors allow you to modify the content of a file as it is being
synced or served statically. mediasync comes with two default filters, CSS
and JavaScript minifiers. These processors require the *slimmer* python
package and will automatically run when syncing media.

Custom processors can be specified using the *PROCESSORS* entry in the
mediasync settings dict. *PROCESSORS* should be a list of processor entries.
Each processor entry can be a callable or a string path to a callable. If the
path is to a class definition, the class will be instantiated into an object.
The processor callable should return a string of the processed file data, None
if it chooses to not process the file, or raise *mediasync.SyncException* if
something goes terribly wrong. The callable should take the following arguments::

	def proc(filedata, content_type, remote_path, is_remote):
		...

filedata
	the content of the file as a string

content_type
	the mimetype of the file being processed

remote_path
	the path to which the file is being synced (contains the file name)

is_remote
	True if the filedata will be pushed remotely, False if it is a static local file

If the *PROCESSORS* setting is used, you will need to include the defaults if you plan on using them::

	'PROCESSORS': (
	    'mediasync.processors.css_minifier',
	    'mediasync.processors.js_minifier',
		...
	),


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

Any directory in *MEDIA_ROOT* that is hidden or starts with an underscore 
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
template context with the key 'request'. This can be done automatically by adding
'django.core.context_processors.request' to *TEMPLATE_CONTEXT_PROCESSORS*
in settings.py

media_url
---------

Renders the MEDIA_URL from settings.py with trailing slashes removed.

::

	<img src="{% media_url %}/images/stuff.png">

MEDIA_URL takes an optional argument that is the media path. Using the argument allows mediasync to add the CACHE_BUSTER to the URL if one is specified.

::

	<img src="{% media_url '/images/stuff.png' %}">

If *CACHE_BUSTER* is set to 12345, the above example will render as::

	<img src="http://assets.example.com/path/to/media/images/stuff.png?12345">


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

Media Path Shortcuts
====================

In some cases, all CSS and JS files will be in their own directory. It can be a 
pain to write full paths from *MEDIA_ROOT* when they can be inferred from the 
type of media being used. Shortcuts can be used in template tags and the joined 
files configuration if the default paths to JS and CSS files are set.

::

    'CSS_PATH': 'styles',
    'JS_PATH': 'scripts',

When these paths are set, you can leave them off of the media paths in template 
tags. Using the above path settings, styles/reset.css and scripts/jquery.js
can be referred to using::

    {% css 'reset.css' %}
    {% js 'jquery.js' %}


-----------------
Running MEDIASYNC
-----------------

::

	./manage.py syncmedia

----------
Change Log
----------

2.0 (in progress)
=================

* add pluggable backends
* add pluggable file processors
* settings refactor
* allow override of *settings.MEDIA_URL*
* Improvements to the logic that decides which files to sync. Safely ignore
  a wider variety of hidden files/directories.
* Make template tags aware of whether the current page is SSL-secured. If it
  is, ask the backend for an SSL media URL (if implemented by your backend).

Thanks to Greg Taylor and Peter Sanchez for their contributions to this release.

1.0.1
=====

* add application/javascript and application/x-javascript to JavaScript mimetypes
* break out of CSS and JS mimetypes
* add support for HTTPS URLs to S3
* allow for storage of S3 keys in ~/.boto configuration file

Thanks to Rob Hudson and Peter Sanchez for their contributions to this release.

1.0
===

Initial release.