from mediasync.backends import BaseClient

class Client(BaseClient):
    
    put_callback = lambda x: None
    
    def remote_media_url(self):
        return "dummy://"
    
    def put(self, *args, **kwargs):
        self.put_callback(*args, **kwargs)