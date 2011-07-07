# -*- coding: utf-8 -*-

import os
import mimetypes


def upload(path, name, fobject, client=None, force=False):
    """Uploads a file to the configured storage backend."""

    from . import backends
    from .conf import msettings
    from .signals import pre_sync, post_sync

    # create client connection
    if client is None:
        client = backends.client()

    client.open()

    # client it up
    _cached_client_serve_remote = client.serve_remote
    client.serve_remote = True

    # send pre-sync signal
    pre_sync.send(sender=client)


    # sync static media

    # calculate local and remote paths
    # filepath = os.path.join(dirpath, filename)
    remote_path = "%s/%s" % (path, name)

    content_type = mimetypes.guess_type(name)[0] or msettings['DEFAULT_MIMETYPE']

    filedata = fobject.read()

    client.process_and_put(filedata, content_type, remote_path, force=force)

    # send post-sync signal while client is still open
    post_sync.send(sender=client)

    client.serve_remote = _cached_client_serve_remote
    client.close()
