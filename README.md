# django-mediasync

One of the more significant development roadblocks we have relates to local vs. 
deployed media. Ideally all media (graphics, css, scripts) development would 
occur locally and not use production media. Then, when ready to deploy, the 
media should be pushed to production. That way there can be significant changes 
to media without disturbing the production web site.

The goal of mediasync is to develop locally and then flip a switch in production 
that makes all the media URLs point to remote media URLs instead of the local 
media directory. Specifically, mediasync executes the following tasks:

- run deflate+jsmin on javascript files

- run deflate+cssmin on css files

- add expires headers to everything (if supported by the backend)

All code is under a BSD-style license, see LICENSE for details.

Source: http://github.com/sunlightlabs/django-mediasync/

## Requirements

- python >= 2.4 (with zlib)

- django >= 1.0

- boto >= 1.8d


## Installation

To install run

    python setup.py install

which will install the application into python's site-packages directory.


## Configuration


### settings.py

Add to INSTALLED_APPS:

	'mediasync'

Add the proper __MEDIA\_ROOT__ setting:

    MEDIA_ROOT = '/path/to/media'

Additionally, replace the existing __MEDIA\_URL__ setting with:

	MEDIA_URL = '/devmedia/'

__MEDIA\_URL__ is the URL that will be used in debug mode. Otherwise, 
the __MEDIA\_URL__ will be loaded from the backend settings.

The following settings dict must also be added: 
   
	MEDIASYNC = {
		'BACKEND': 'path.to.backend',
	}

If you want to use a different media URL than that specified 
in __settings.MEDIA\_URL__, you can add __MEDIA\_URL__ to the __MEDIASYNC__ 
settings dict:

	MEDIASYNC = {
		...
		'MEDIA_URL': '/url/to/media/', # becomes http://yourhost.com/url/to/media/
		...
	}

Same goes for __MEDIA\_ROOT__:

	MEDIASYNC = {
		...
		'MEDIA_ROOT': '/path/to/media/',
		...
	}

mediasync supports pluggable backends. Please see below for information on 
the provided backends as well as directions on implementing your own.

If the client supports media expiration, all files are set to expire 365 days 
after the file was synced. You may override this value by adding 
__EXPIRATION\_DAYS__ to the MEDIASYNC settings dict.

	'EXPIRATION_DAYS': 365 * 10, # expire in 10 years

The media URL is selected based on the __DEBUG__ attribute in settings.py. 
When *True*, media will be served locally instead of from S3. Sometimes it is 
necessary to serve media from S3 even when __DEBUG__ is *True*. To force remote 
serving of media, set __SERVE\_REMOTE__ to *True*.

	'SERVE_REMOTE': True,

#### DOCTYPE

link and script tags are written using XHTML syntax. The rendering can be 
overridden by using the __DOCTYPE__ setting. Allowed values are *'html4'*, 
*'html5'*, or *'xhtml'*.

	'DOCTYPE': 'xhtml',

For each doctype, the following tags are rendered:

##### html4

    <link rel="stylesheet" href="..." type="text/css" media="...">
    <script type="text/javascript" charset="utf-8" src="..."></script>

##### html5

    <link rel="stylesheet" href="..." type="text/css" media="...">
    <script src="..."></script>

##### xhtml

    <link rel="stylesheet" href="..." type="text/css" media="..." />
    <script type="text/javascript" charset="utf-8" src="..."></script>


### Backends

mediasync now supports pluggable backends. A backend is a Python module that 
contains a Client class that implements a mediasync-provided BaseClient class.

#### S3

	'BACKEND': 'mediasync.backends.s3',

##### Settings

The following settings are required in the mediasync settings dict.

	'AWS_KEY': "s3_key",
	'AWS_SECRET': "s3_secret",
	'AWS_BUCKET': "bucket_name",

Optionally you may specify a path prefix:

	'AWS_PREFIX': "key_prefix",

Assuming a correct DNS CNAME entry, setting __AWS\_BUCKET__ to 
__assets.sunlightlabs.com__ and __AWS\_PREFIX__ to __myproject/media__ would 
sync the media directory to http://assets.sunlightlabs.com/myproject/media/.

Amazon allows users to create DNS CNAME entries to map custom domain names 
to an AWS bucket. MEDIASYNC can be configured to use the bucket as the media 
URL by setting __AWS\_BUCKET\_CNAME__ to *True*.

	'AWS_BUCKET_CNAME': True,

##### Tips

Since files are given a far future expires header, one needs a way to do 
"cache busting" when you want the browser to fetch new files before the expire 
date arrives.  One of the best and easiest ways to accomplish this is to alter 
the path to the media files with some sort of version string using the key 
prefix setting:

    'AWS_PREFIX': "myproject/media/v20001201",

Given that and the above DNS CNAME example, the media directory URL would end 
up being http://assets.sunlightlabs.com/myproject/media/v20001201/.  Whenever 
you need to update the media files, simply update the key prefix with a new 
versioned string.

A __CACHE\_BUSTER__ settings can be added to the main __MEDIASYNC__ settings 
dict to add a query string parameter to all media URLs. The cache buster can 
either be a value or a callable which is passed the media URL as a parameter.

	'CACHE_BUSTER': 1234567890,

The above setting will generate a media path similar to:

	http://yourhost.com/url/to/media/image.png?1234567890

#### Custom backends

You can create a custom backend by creating a Python module containing a Client 
class. This class must inherit from mediasync.backends.BaseClient. Additionally, 
you must implement two methods:

	def remote_media_url(self):
	    ...

remote\_media\_url returns the full base URL for remote media. This can be 
either a static URL or one generated from mediasync settings.

	def put(self, filedata, content_type, remote_path, force=False):
	    ...

put is responsible for pushing a file to the backend storage.

* filedata - the contents of the file
* content\_type - the mime type of the file
* remote\_path - the remote path (relative from remote\_media\_url) to which 
  the file should be written
* force - if True, write file to remote storage even if it already exists

### urls.py

Add a reference to mediasync.urls in your main urls.py file.

	urlpatterns = ('',
		...
		url(r'^', include('mediasync.urls)),
		...
	)


## Features

### Ignored Directories

Any directory in __MEDIA\_ROOT__ that is hidden or starts with an underscore 
will be ignored during syncing.


### Template Tags

When referring to media in HTML templates you can use custom template tags. 
These tags can by accessed by loading the media template tag collection.

	{% load media %}

If you'd like to make the mediasync tags global, you can add the following to
your master urls.py file:

    from django.template import add_to_builtins
    add_to_builtins('mediasync.templatetags.media')

#### media_url

Renders the MEDIA_URL from settings.py with trailing slashes removed.

	<img src="{% media_url %}/images/stuff.png">


#### js

Renders a script tag with the correct include.

	{% js "myfile.js" %}


#### css

Renders a <link> tag to include the stylesheet. It takes an optional second 
parameter for the media attribute; the default media is "screen, projector".

	{% css "myfile.css" %}  
	{% css "myfile.css" "screen" %}  


#### css_print

Shortcut to render as a print stylesheet.

	{% css_print "myfile.css" %}

which is equivalent to

	{% css "myfile.css" "print" %}


### Writing Style Sheets

Users are encouraged to write stylesheets using relative URLS. The media 
directory is synced with S3 as is, so relative local paths will still work 
when pushed remotely.

	background: url(../images/arrow_left.png);


### Joined files

When serving media in production, it is beneficial to combine JavaScript and 
CSS into single files. This reduces the number of connections the browser needs 
to make to the web server. Fewer connections can dramatically decrease page 
load times and reduce the server-side load.

Joined files are specified in the __MEDIASYNC__ dict using __JOINED__. This is
a dict that maps individual media to an alias for the joined files. 

	'JOINED': {
		'styles/joined.css': ['styles/reset.css','styles/text.css'],
		'scripts/joined.js': ['scripts/jquery.js','scripts/processing.js'],
	},

Files listed in __JOINED__ will be combined and pushed to S3 with the name of 
the alias. The individual CSS files will also be pushed to S3. Aliases must end 
in either .css or .js in order for the content-type to be set appropriately.

The existing template tags may be used to refer to the joined media. Simply use 
the joined alias as the argument:

	{% css_print "joined.css" %}

When served locally, template tags will render an HTML tag for each of the files 
that make up the joined file:

	<link rel="stylesheet" href="/media/styles/reset.css" type="text/css" media="screen, projection" />
	<link rel="stylesheet" href="/media/styles/text.css" type="text/css" media="screen, projection" />

When served remotely, one HTML tag will be rendered with the name of the joined file:

	<link rel="stylesheet" href="http://bucket.s3.amazonaws.com/styles/joined.css" type="text/css" media="screen, projection" />

### Media Path Shortcuts

In some cases, all CSS and JS files will be in their own directory. It can be a 
pain to write full paths from __MEDIA\_ROOT__ when they can be inferred from the 
type of media being used. Shortcuts can be used in template tags and the joined 
files configuration if the default paths to JS and CSS files are set.

    'CSS_PATH': 'styles',
    'JS_PATH': 'scripts',

When these paths are set, you can leave them off of the media paths in template 
tags. Using the above path settings, _styles/reset.css_ and _scripts/jquery.js_ 
can be referred to using: 

    {% css 'reset.css' %}
    {% js 'jquery.js' %}


## Running MEDIASYNC

	./manage.py syncmedia

## Change Log

### 2.0 (in progress)

* add pluggable backends
* settings refactor
* allow override of __settings.MEDIA\_URL__
* Improvements to the logic that decides which files to sync. Safely ignore
  a wider variety of hidden files/directories.
* Make template tags aware of whether the current page is SSL-secured. If it
  is, ask the backend for an SSL media URL (if implemented by your backend).

### 1.0.1

* add application/javascript and application/x-javascript to JavaScript mimetypes
* break out of CSS and JS mimetypes
* add support for HTTPS URLs to S3
* allow for storage of S3 keys in ~/.boto configuration file

Thanks to Rob Hudson and Peter Sanchez for the changes in this release.

### 1.0

Initial release.