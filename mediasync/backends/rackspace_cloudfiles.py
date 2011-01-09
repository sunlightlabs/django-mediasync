import cloudfiles

from mediasync.backends import BaseClient
from mediasync.conf import msettings


class Client(BaseClient):

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)

        self.container = msettings['CLOUDFILES_CONTAINER']
        assert self.container

    def open(self):
        "Set up the CloudFiles connection and grab the container."
        username = msettings['CLOUDFILES_USERNAME']
        key = msettings['CLOUDFILES_KEY']

        _conn = cloudfiles.get_connection(username, key)
        self._container = _conn.create_container(self.container)

        if not self._container.is_public():
            self._container.make_public()

    def remote_media_url(self, with_ssl=False):
        return ""

    def put(self, filedata, content_type, remote_path, force=False):

        obj = self._container.create_object(remote_path)
        obj.write(filedata)

        return True
