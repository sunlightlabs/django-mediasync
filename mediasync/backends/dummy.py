from mediasync.backends import BaseClient

class Client(BaseClient):
    
    def remote_media_url(self):
        return ""
    
    def put(self, *args, **kwargs):
        pass