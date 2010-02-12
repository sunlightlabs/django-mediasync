from django.conf import settings
from mediasync.utils import load_backend

def client():
    backend_name = getattr(settings, 'MEDIASYNC', {}).get('BACKEND', '')
    return load_backend(backend_name)

class BaseClient(object):
    
    def __init__(self, *args, **kwargs):
        
        self._settings = getattr(settings, 'MEDIASYNC', None)
        assert self._settings
        
        # mediasync settings
        self.expiration_days = self._settings.get("EXPIRATION_DAYS", 365)
        self.serve_remote = self._settings.get('SERVE_REMOTE', not settings.DEBUG)
        
        # project settings
        self.local_media_url = getattr(settings, 'MEDIA_URL', '')
        
    def media_url(self):
        if self.serve_remote:
            url = self.remote_media_url()
        else:
            url = self.local_media_url
        return url.rstrip('/')
        
    def remote_media_url(self):
        raise NotImplementedError('remote_media_url not defined in ' + self.__class__.__name__)
        
    def put(self, filedata, content_type, remote_path, force=False):
        raise NotImplementedError('put not defined in ' + self.__class__.__name__)