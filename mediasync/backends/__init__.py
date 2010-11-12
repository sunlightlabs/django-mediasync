from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from mediasync import processors

DEFAULT_PROCESSORS = (
    processors.css_minifier,
    processors.js_minifier,
)

def client():
    backend_name = getattr(settings, 'MEDIASYNC', {}).get('BACKEND', '')
    if not backend_name:
        raise ImproperlyConfigured('must define a mediasync BACKEND property')
    return load_backend(backend_name)

def load_backend(backend_name):
    try:
        backend = import_module(backend_name)
        return backend.Client()
    except ImportError, e:
        raise ImproperlyConfigured(("%s is not a valid mediasync backend. \n" +
            "Error was: %s") % (backend_name, e))

class BaseClient(object):

    def __init__(self, *args, **kwargs):

        self._settings = getattr(settings, 'MEDIASYNC', None)
        assert self._settings

        # mediasync settings
        self.expiration_days = self._settings.get("EXPIRATION_DAYS", 365)
        self.serve_remote = self._settings.get('SERVE_REMOTE', False)

        self.local_media_url = self.get_local_media_url()
        self.media_root = self.get_media_root()

        self.processors = []
        for proc in self._settings.get("PROCESSORS", DEFAULT_PROCESSORS):

            if isinstance(proc, basestring):
                (module, attr) = proc.rsplit('.', 1)
                module = import_module(module)
                proc = getattr(module, attr, None)

            if isinstance(proc, type):
                proc = proc()

            if callable(proc):
                self.processors.append(proc)

    def get_local_media_url(self):
        """
        Checks settings.MEDIASYNC['MEDIA_URL'], then settings.MEDIA_URL.
        
        Broken out to allow overriding if need be.
        """
        return self._settings.get('MEDIA_URL', getattr(settings, 'MEDIA_URL', ''))

    def get_media_root(self):
        """
        Checks settings.MEDIASYNC['MEDIA_ROOT'], then settings.MEDIA_ROOT.
        
        Broken out to allow overriding if need be.
        """
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

    def process(self, filedata, content_type, remote_path):
        for proc in self.processors:
            prcssd_filedata = proc(filedata, content_type, remote_path, self.serve_remote)
            if prcssd_filedata is not None:
                filedata = prcssd_filedata
        return filedata

    def process_and_put(self, filedata, content_type, remote_path, force=False):
        filedata = self.process(filedata, content_type, remote_path)
        return self.put(filedata, content_type, remote_path, force)

    def put(self, filedata, content_type, remote_path, force=False):
        raise NotImplementedError('put not defined in ' + self.__class__.__name__)

    def remote_media_url(self, with_ssl=False):
        raise NotImplementedError('remote_media_url not defined in ' + self.__class__.__name__)

    def open(self):
        pass

    def close(self):
        pass
