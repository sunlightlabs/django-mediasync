import cloudfiles

from django.core.exceptions import ImproperlyConfigured

from mediasync.backends import BaseClient
from mediasync.conf import msettings


class Client(BaseClient):

    def __init__(self, *args, **kwargs):
        "Set up the CloudFiles connection and grab the container."
        super(Client, self).__init__(*args, **kwargs)

        container_name = msettings['CLOUDFILES_CONTAINER']
        username = msettings['CLOUDFILES_USERNAME']
        key = msettings['CLOUDFILES_API_KEY']

        if not container_name:
            raise ImproperlyConfigured("CLOUDFILES_CONTAINER is a required setting.")

        if not username:
            raise ImproperlyConfigured("CLOUDFILES_USERNAME is a required setting.")

        if not key:
            raise ImproperlyConfigured("CLOUDFILES_API_KEY is a required setting.")

        self.conn = cloudfiles.get_connection(username, key)
        self.container = self.conn.create_container(container_name)

        if not self.container.is_public():
            self.container.make_public()

    def remote_media_url(self, with_ssl=False):
        "Grab the remote URL for the contianer."
        if with_ssl:
            raise UserWarning("""Rackspace CloudFiles does not yet support SSL.
                    See http://bit.ly/hYV502 for more info.""")
        return self.container.public_uri()

    def put(self, filedata, content_type, remote_path, force=False):

        obj = self.container.create_object(remote_path)
        obj.content_type = content_type
        obj.write(filedata)

        return True
