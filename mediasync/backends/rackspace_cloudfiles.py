from django.conf import settings
from mediasync.backends import BaseClient
import cloudfiles

class Client(BaseClient):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        
        self.container = self._settings.get('CLOUDFILES_CONTAINER', None)
        assert self.container
    
    def open(self):
        
        username = self._settings.get("CLOUDFILES_USERNAME", None)
        key = self._settings.get("CLOUDFILES_KEY", None)
        
        _conn = cloudfiles.get_connection(username, key)
        self._container = _conn.create_container(self.container)
    
    def remote_media_url(self, with_ssl=False):
        return ""
            
    def put(self, filedata, content_type, remote_path, force=False):
        
        obj = self._container.create_object(remote_path)
        obj.write(filedata)
        
        return True