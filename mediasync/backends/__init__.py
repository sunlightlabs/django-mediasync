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
        
        self.local_media_url = self.get_local_media_url()
        self.media_root = self.get_media_root()
        
    def get_local_media_url(self):
        """
        Checks settings.MEDIASYNC['MEDIA_URL'], then settings.MEDIA_URL.
        
        Broken out to allow overriding if need be.
        """
        # get settings.MEDIASYNC.MEDIA_URL or settings.MEDIA_URL
        return self._settings.get('MEDIA_URL', getattr(settings, 'MEDIA_URL', ''))
    
    def get_media_root(self):
        """
        Checks settings.MEDIASYNC['MEDIA_ROOT'], then settings.MEDIA_ROOT.
        
        Broken out to allow overriding if need be.
        """
        # get settings.MEDIASYNC.MEDIA_ROOT or settings.MEDIA_ROOT
        return self._settings.get('MEDIA_ROOT', getattr(settings, 'MEDIA_ROOT', ''))
    
    def media_url(self, with_ssl=False):
        """
        Used to return a base media URL. Depending on whether we're serving
        media remotely or locally, this either hands the decision off to the
        backend, or just uses the value in settings.MEDIA_URL.
        
        args:
          with_ssl: (bool) If True, return an HTTPS url (depending on how
                           the backend handles it).
        """
        if self.serve_remote:
            # Hand this off to whichever backend is being used.
            url = self.remote_media_url(with_ssl)
        else:
            # Serving locally, just use the value in settings.py.
            url = self.local_media_url
        return url.rstrip('/')
        
    def remote_media_url(self, with_ssl=False):
        raise NotImplementedError('remote_media_url not defined in ' + self.__class__.__name__)
        
    def put(self, filedata, content_type, remote_path, force=False):
        raise NotImplementedError('put not defined in ' + self.__class__.__name__)
    
    def open(self):
        pass
    
    def close(self):
        pass
