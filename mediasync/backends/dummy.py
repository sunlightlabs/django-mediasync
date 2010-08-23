from mediasync.backends import BaseClient

class Client(BaseClient):
    
    remote_media_url_callback = lambda x: "dummy://"
    put_callback = lambda x: None
    
    def remote_media_url(self, with_ssl=False):
        return self.remote_media_url_callback()
    
    def put(self, *args, **kwargs):
        self.put_callback(*args)