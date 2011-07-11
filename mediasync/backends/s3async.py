from mediasync.backends.s3 import Client as SynchronousClient
from mediasync.conf import msettings
from multiprocessing import Pool

def async_put(filedata, content_type, path, force=False):
    client = SynchronousClient(create_bucket=False)
    client.open()
    client.serve_remote = True
    client.put(filedata, content_type, path, force)
    client.close()
    return "[%s] %s" % (content_type, path)

def async_callback(result):
    if msettings['VERBOSE']:
        print result

class Client(SynchronousClient):
    
    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        self.pool = Pool(msettings.get('AWS_ASYNC_WORKERS', 4))
    
    def put(self, *args):
        self.pool.apply_async(async_put, args, callback=async_callback)
    
    def close(self):
        self.pool.close()
        self.pool.join()
        super(Client, self).close()