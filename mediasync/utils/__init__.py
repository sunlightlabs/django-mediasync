from django.core.exceptions import ImproperlyConfigured
from django.utils.importlib import import_module

def load_backend(backend_name):
    try:
        backend = import_module(backend_name)
        return backend.Client()
    except ImportError, e:
        raise ImproperlyConfigured(("%s is not a valid mediasync backend. \n" +
            "Error was: %s") % (backend_name, e))