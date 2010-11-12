"""
Mediasync can serve media locally when MEDIASYNC['SERVE_REMOTE'] == False.
The following urlpatterns are shimmed in, in that case.
"""
from django.conf.urls.defaults import *
from mediasync import backends

client = backends.client()
local_media_url = client.local_media_url.strip('/')

urlpatterns = patterns('mediasync.views',
    url(r'^%s/(?P<path>.*)$' % local_media_url, 'static_serve',
        {'client': client}),
)
