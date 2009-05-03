# django-mediasync

One of the more significant development roadblocks we have relates to local vs. deployed media. Ideally all media (graphics, css, scripts) development would occur locally and not use S3. Then, when ready to deploy, the media should be pushed to S3. That way there can be significant changes to media without disturbing the production web site.

To make this easier, I wrote some additions to the sunlightcore module that handles a lot of media tasks. The goal is to develop locally and then flip a switch in production that makes all the media URLs point to S3 instead of the local media directory. Specifically, MEDIASYNC executes the following tasks:

- run gzip+jsmin on javascript files

- run gzip+cssmin on css files

- add expires headers to everything

- rewrite the css files to use settings.MEDIA_URL instead of /media/

One flaw is that the MD5 of a compressed file changes each time it is compressed. This will cause css and js files to be reuploaded each time. Images and other files that are not compressed will only be uploaded when they are created or if they have changed. 

django-mediasync is a project of Sunlight Foundation (c) 2009.
Writen by Jeremy Carbaugh <jcarbaugh@sunlightfoundation.com>

All code is under a BSD-style license, see LICENSE for details.

Source: http://github.com/sunlightlabs/django-mediasync/


## Requirements

python >= 2.4

django >= 1.0

S3.py 
http://developer.amazonwebservices.com/connect/entry.jspa?externalID=134

## Installation

To install run

    python setup.py install

which will install the application into python's site-packages directory.


## Quick Setup


### settings.py

Add to INSTALLED_APPS:

	'mediasync'

Additionally, replace the existing __MEDIA_URL__ setting with:

	MEDIA_URL = '/media/'
	
__MEDIA_URL__ is the URL that will be used in debug mode. Otherwise, the __MEDIA_URL__ will be inferred from the settings listed below.

The following settings must also be added:

	import os  
	PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))  
   
	MEDIASYNC_AWS_KEY = "s3_key"  
	MEDIASYNC_AWS_SECRET = "s3_secret"  
	MEDIASYNC_AWS_BUCKET = "bucket_name"  
	
Optionally you may specify a key prefix:

	MEDIASYNC_AWS_PREFIX = "key_prefix"  

Assuming a correct DNS CNAME entry, setting __MEDIASYNC_AWS_BUCKET__ to __assets.sunlightlabs.com__ and __MEDIASYNC_AWS_PREFIX__ to __myproject/media__ would sync the media directory to http://assets.sunlightlabs.com/myproject/media/.

By default, all files are given an expires header of 365 days after the file was synced to S3. You may override this value by adding __MEDIASYNC_EXPIRATION_DAYS__ to settings.py.

    MEDIASYNC_EXPIRATION_DAYS = 365 * 10    # expire in 10 years

Amazon allows users to create DNS CNAME entries to map custom domain names to an AWS bucket. MEDIASYNC can be configured to use the bucket as the media URL by setting __MEDIASYNC_BUCKET_CNAME__ to *True*.

	MEDIASYNC_BUCKET_CNAME = True


### urls.py

A static media URL needs to be setup in urls.py that enables access to the media directory ONLY IN DEBUG MODE.

	if (settings.DEBUG):  
		urlpatterns += patterns(,  
			url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),  
		)  


### Directory structure

Create a __media__ directory under the root of the project. Create __images__, __scripts__, and __styles__ directories beneath __media__.


## Quick Setup


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

link elements with conditional statements.

	{% css_ie "myfile.css" %}  
	{% css_ie6 "myfile.css" %}  
	{% css_ie7 "myfile.css" %}  


### Writing Style Sheets

Unfortunately, style sheets cannot be dynamic so it is important to use a relative local media URL when writing them.

	background: url(/media/images/arrow_left.png);

When pushed to S3, the local URL is rewritten as the MEDIA_URL from settings.py. If the MEDIA_URL is __http://assets.mysite.com/__ then the CSS rule will be rewritten as:

	background: url(http://assets.mysite.com/images/arrow_left.png);


## Running MEDIASYNC


	./manage.py mediasync