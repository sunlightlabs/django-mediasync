from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mediasync.utils import load_backend

def client():
    backend_name = getattr(settings, 'MEDIASYNC', {}).get('BACKEND', '')
    if not backend_name:
        raise ImproperlyConfigured('must define a mediasync BACKEND property')
    return load_backend(backend_name)

class BaseClient(object):
    
    def __init__(self, *args, **kwargs):
        
        self._settings = getattr(settings, 'MEDIASYNC', None)
        assert self._settings
        
        # mediasync settings
        self.expiration_days = self._settings.get("EXPIRATION_DAYS", 365)
        self.serve_remote = self._settings.get('SERVE_REMOTE', not settings.DEBUG)
        
        # get settings.MEDIASYNC.MEDIA_URL or settings.MEDIA_URL
        self.local_media_url = self._settings.get('MEDIA_URL', getattr(settings, 'MEDIA_URL', ''))
        # get settings.MEDIASYNC.MEDIA_ROOT or settings.MEDIA_ROOT
        self.media_root = self._settings.get('MEDIA_ROOT', getattr(settings, 'MEDIA_ROOT', ''))
    
    def media_url(self):
        # TODO: PATCH THIS FOR SSL
        if self.serve_remote:
            url = self.remote_media_url()
        else:
            url = self.local_media_url
        return url.rstrip('/')
        
    def remote_media_url(self):
        raise NotImplementedError('remote_media_url not defined in ' + self.__class__.__name__)
        
    def put(self, filedata, content_type, remote_path, force=False):
        raise NotImplementedError('put not defined in ' + self.__class__.__name__)
    
    def open(self):
        pass
    
    def close(self):
        pass
