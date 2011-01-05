from django.conf import settings
from mediasync import processors

_settings = {
    'DOCTYPE': 'html5',
    'EMULATE_COMBO': False,
    'EXPIRATION_DAYS': 365,
    'JOINED': {},
    'MEDIA_ROOT': settings.MEDIA_ROOT,
    'MEDIA_URL': settings.MEDIA_URL,
    'PROCESSORS': (processors.css_minifier, processors.js_minifier),
    'SERVE_REMOTE': not settings.DEBUG,
    'URL_PROCESSOR': lambda x: x,
}

class Settings(object):
    
    def __init__(self, conf):
        for k, v in conf.iteritems():
            self[k] = v
    
    def __delitem__(self, name):
        del _settings[name]
    
    def __getitem__(self, name):
        return self.get(name)
    
    def __setitem__(self, name, val):
        _settings[name] = val
        
    def __str__(self):
        return repr(_settings)
    
    def get(self, name, default=None):
        return _settings.get(name, default)

msettings = Settings(settings.MEDIASYNC)