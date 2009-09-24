# django-mediasync

One of the more significant development roadblocks we have relates to local vs. deployed media. Ideally all media (graphics, css, scripts) development would occur locally and not use S3. Then, when ready to deploy, the media should be pushed to S3. That way there can be significant changes to media without disturbing the production web site.

To make this easier, I wrote some additions to the sunlightcore module that handles a lot of media tasks. The goal is to develop locally and then flip a switch in production that makes all the media URLs point to S3 instead of the local media directory. Specifically, MEDIASYNC executes the following tasks:

- run gzip+jsmin on javascript files

- run gzip+cssmin on css files

- add expires headers to everything

One flaw is that the MD5 of a compressed file changes each time it is compressed. This will cause css and js files to be reuploaded each time. Images and other files that are not compressed will only be uploaded when they are created or if they have changed. 

django-mediasync is a project of Sunlight Foundation (c) 2009.
Writen by Jeremy Carbaugh <jcarbaugh@sunlightfoundation.com>

All code is under a BSD-style license, see LICENSE for details.

Source: http://github.com/sunlightlabs/django-mediasync/


## Requirements

python >= 2.4

django >= 1.0

boto >= 1.8d

## Installation

To install run

    python setup.py install

which will install the application into python's site-packages directory.


## Quick Setup


### settings.py

Add to INSTALLED_APPS:

	'mediasync'

Add the proper __MEDIA\_ROOT__ setting:

    MEDIA_ROOT = '/path/to/media'

Additionally, replace the existing __MEDIA\_URL__ setting with:

	MEDIA_URL = '/media/'

And change the __ADMIN\_MEDIA\_PREFIX__ to something other than *'media'*:

    ADMIN_MEDIA_PREFIX = '/media/admin/'

__MEDIA\_URL__ is the URL that will be used in debug mode. Otherwise, the __MEDIA\_URL__ will be inferred from the settings listed below.

The following settings must also be added: 
   
	MEDIASYNC_AWS_KEY = "s3_key"  
	MEDIASYNC_AWS_SECRET = "s3_secret"  
	MEDIASYNC_AWS_BUCKET = "bucket_name"  
	
Optionally you may specify a key prefix:

	MEDIASYNC_AWS_PREFIX = "key_prefix"  

Assuming a correct DNS CNAME entry, setting __MEDIASYNC\_AWS\_BUCKET__ to __assets.sunlightlabs.com__ and __MEDIASYNC\_AWS\_PREFIX__ to __myproject/media__ would sync the media directory to http://assets.sunlightlabs.com/myproject/media/.

By default, all files are given an expires header of 365 days after the file was synced to S3. You may override this value by adding __MEDIASYNC\_EXPIRATION\_DAYS__ to settings.py.

    MEDIASYNC_EXPIRATION_DAYS = 365 * 10    # expire in 10 years

Amazon allows users to create DNS CNAME entries to map custom domain names to an AWS bucket. MEDIASYNC can be configured to use the bucket as the media URL by setting __MEDIASYNC\_BUCKET\_CNAME__ to *True*.

	MEDIASYNC_BUCKET_CNAME = True

Previous versions of mediasync rewrote URLs in CSS files to use the correct __MEDIA\_URL__. Now users are encouraged to use relative paths in their CSS so that URL rewriting is not necessary. URL rewriting can be enabled by setting __MEDIASYNC\_REWRITE\_CSS__ to *True*.

	MEDIASYNC_REWRITE_CSS = True

The media URL is selected based on the __DEBUG__ attribute in settings.py. When *True*, media will be served locally instead of from S3. Sometimes it is necessary to serve media from S3 even when __DEBUG__ is *True*. To force remote serving of media, set __MEDIASYNC\_SERVE\_REMOTE__ to *True*.

	MEDIASYNC_SERVE_REMOTE = True

link and script tags are written using XHTML syntax. The rendering can be overridden by using the __MEDIASYNC\_DOCTYPE__ setting. Allowed values are *'html4'*, *'html5'*, or *'xhtml'*.

	MEDIASYNC_DOCTYPE = 'xhtml'

For each doctype, the tags are rendered:

__MEDIASYNC_DOCTYPE__ = "html4"

    <link rel="stylesheet" href="..." type="text/css" media="...">
    <script type="text/javascript" charset="utf-8" src="..."></script>

__MEDIASYNC_DOCTYPE__ = "html5"

    <link rel="stylesheet" href="..." type="text/css" media="...">
    <script src="..."></script>

__MEDIASYNC_DOCTYPE__ = "xhtml"

    <link rel="stylesheet" href="..." type="text/css" media="..." />
    <script type="text/javascript" charset="utf-8" src="..."></script>


### urls.py

A static media URL needs to be setup in urls.py that enables access to the media directory ONLY IN DEBUG MODE.

    import settings
	if (settings.DEBUG):  
		urlpatterns += patterns('',  
			url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),  
		)  


### Directory structure

mediasync assumes a __MEDIA\_ROOT__ structure in which CSS files will be located under *styles* and JavaScript files will be located under *scripts*. Images and other media can be located anywhere under __MEDIA\_ROOT__. If you would prefer to have your CSS and JavaScript in different directories you can override the defaults in settings.py:

    MEDIASYNC_CSS_PATH = 'styles'
    MEDIASYNC_JS_PATH = 'scripts'

If the CSS and JavaScript files live in the same directory, you can set __MEDIASYNC\_CSS\_PATH__ and __MEDIASYNC\_JS\_PATH__ to the same path.


## Features

### Ignored Directories

Any directory in __MEDIA\_ROOT__ that is hidden or starts with an underscore will be ignored during syncing.


### Template Tags

When referring to media in HTML templates you can use custom template tags. These tags can by accessed by loading the media template tag collection.

	{% load media %}


#### media_url

Renders the MEDIA_URL from settings.py with trailing slashes removed.

	<img src="{% media_url %}/images/stuff.png">


#### js

Renders a script tag with the correct include.

	{% js "myfile.js" %}


#### css

Renders a <link> tag to include the stylesheet. It takes an optional second parameter for the media attribute; the default media is "screen, projector".

	{% css "myfile.css" %}  
	{% css "myfile.css" "screen" %}  


#### css_print

Shortcut to render as a print stylesheet.

	{% css_print "myfile.css" %}

which is equivalent to

	{% css "myfile.css" "print" %}


#### css_ie, css_ie6, css_ie7

**Deprecated** and will be removed before a 1.0 release.


### Writing Style Sheets

Users are encouraged to write stylesheets using relative URLS. The media directory is synced with S3 as is, so relative local paths will still work when pushed remotely.

	background: url(../images/arrow_left.png);
	
#### Deprecated URL rewriting

Previous versions of mediasync rewrote absolute paths to use the correct __MEDIA\_URL__. If you would prefer to use this old method, write URLs using absolute paths and set __MEDIASYNC\_REWRITE\_CSS__ = *True* in settings.py.

	background: url(/media/images/arrow_left.png);

When pushed to S3, the local URL is rewritten as the MEDIA\_URL from settings.py. If the MEDIA_URL is __http://assets.mysite.com/__ then the CSS rule will be rewritten as:

	background: url(http://assets.mysite.com/images/arrow_left.png);


### Joined files

When serving media in production, it is beneficial to combine JavaScript and CSS into single files. This reduces the number of connections the browser needs to make to the web server. Fewer connections can dramatically decrease page load times and reduce the server-side load.

Joined files are specified in settings.py using the __MEDIASYNC\_JOINED__. This is a dict that maps individual media to an alias for the joined files. 

	MEDIASYNC_JOINED = {
		'joined.css': ['reset.css','text.css'],
		'joined.js': ['jquery.js','mediasync.js','processing.js'],
	}

Files listed in __MEDIASYNC\_JOINED__ will be combined and pushed to S3 with the name of the alias. The individual CSS files will also be pushed to S3. Aliases must end in either .css or .js; mediasync will look for the source files in the appropriate directories based on the alias extension.

The existing template tags may be used to refer to the joined media. Simply use the joined alias as the argument:

	{% css_print "joined.css" %}

When served locally, template tags will render an HTML tag for each of the files that make up the joined file:

	<link rel="stylesheet" href="/media/styles/reset.css" type="text/css" media="screen, projection" />
	<link rel="stylesheet" href="/media/styles/text.css" type="text/css" media="screen, projection" />

When served remotely, one HTML tag will be rendered with the name of the joined file:

	<link rel="stylesheet" href="http://bucket.s3.amazonaws.com/styles/joined.css" type="text/css" media="screen, projection" />


### Custom Media Directory Structure

On the off chance you have a really weird directory structure that does not align with mediasync's expectations, you can default all paths to __MEDIA\_ROOT__ by setting the CSS and JS paths to an empty string.

    MEDIASYNC_CSS_PATH = ''
    MEDIASYNC_JS_PATH = ''

This means that no path assumptions are being made and all paths must be relative from __MEDIA\_ROOT__. All template tags and MEDIASYNC_JOINED settings must contain the entire path.

    {% css 'css_external/reset.css' %}
    {% css 'css_internal/mysite.css' %}

And when __MEDIASYNC\_JOINED__ is used:

    MEDIASYNC_JOINED = {
	    'css/joined.css': ['css_external/reset.css','css_internal/mysite.css'],
    }


## Running MEDIASYNC

	./manage.py syncmedia