from django.conf import settings
from django.conf.urls.defaults import *

if (settings.DEBUG):
    from mediasync import backends
    client = backends.client()
    urlpatterns = patterns('',  
        url(r'^%s/(?P<path>.*)$' % client.local_media_url.strip('/'), 'django.views.static.serve', {'document_root': client.media_root}),
    )
