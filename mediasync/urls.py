from django.conf import settings
from django.conf.urls.defaults import *

from mediasync import backends
client = backends.client()

if settings.DEBUG:
    view = 'django.views.static.serve'
    params = {'document_root': client.media_root}
else:
    view = 'django.views.generic.simple.redirect_to'
    params = {'url': client.remote_media_url().strip('/') + '/%(path)s'}

urlpatterns = patterns('',  
    url(r'^%s/(?P<path>.*)$' % client.local_media_url.strip('/'), view, params),
)