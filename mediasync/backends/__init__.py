from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module
from mediasync.conf import msettings

def client():
    backend_name = msettings['BACKEND']
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

        # mediasync settings
        self.expiration_days = msettings['EXPIRATION_DAYS']
        self.serve_remote = msettings['SERVE_REMOTE']

        self.local_media_url = self.get_local_media_url()
        self.media_root = self.get_media_root()

        self.processors = []
        for proc in msettings['PROCESSORS']:

            if isinstance(proc, basestring):
                try:
                    dot = proc.rindex('.')
                except ValueError:
                    raise exceptions.ImproperlyConfigured, '%s isn\'t a processor module' % (proc,)
                module, attr = proc[:dot], proc[dot+1:]
                module = import_module(module)
                proc = getattr(module, attr, None)

            if isinstance(proc, type):
                proc = proc()

            if callable(proc):
                self.processors.append(proc)
    
    def supports_gzip(self):
        return False

    def get_local_media_url(self):
        """
        Checks msettings['STATIC_URL'], then settings.STATIC_URL.
        
        Broken out to allow overriding if need be.
        """
        return msettings['STATIC_URL']

    def get_media_root(self):
        """
        Checks msettings['STATIC_ROOT'], then settings.STATIC_ROOT.
        
        Broken out to allow overriding if need be.
        """
        return msettings['STATIC_ROOT']

    def media_url(self, with_ssl=False):
        """
        Used to return a base media URL. Depending on whether we're serving
        media remotely or locally, this either hands the decision off to the
        backend, or just uses the value in settings.STATIC_URL.
        
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
            is_active = msettings['SERVE_REMOTE'] or msettings['EMULATE_COMBO']
            prcssd_filedata = proc(filedata, content_type, remote_path, is_active)
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
