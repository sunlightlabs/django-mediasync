from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.views.static import serve
from mediasync import backends

client = backends.client()

def static_serve(request, path):
    
    if not settings.DEBUG:
        url = client.remote_media_url().strip('/') + '/%(path)s'
        return redirect_to(request, url, path=path)
    
    resp = serve(request, path, document_root=client.media_root)
    resp.content = client.process(resp.content, resp['Content-Type'], path)
    
    return resp

urlpatterns = patterns('',  
    url(r'^%s/(?P<path>.*)$' % client.local_media_url.strip('/'), static_serve),
)