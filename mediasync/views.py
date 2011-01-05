"""
This module contains views used to serve static media if 
msettings['SERVE_REMOTE'] == False. See mediasync.urls to see how
these are shimmed in.

The static_serve() function is where the party starts.
"""
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve
from django.views.generic.simple import redirect_to
from mediasync import combine_files
from mediasync.conf import msettings

def combo_serve(request, path, client):
    """
    Handles generating a 'combo' file for the given path. This is similar to
    what happens when we upload to S3. Processors are applied, and we get
    the value that we would if we were serving from S3. This is a good way
    to make sure combo files work as intended before rolling out
    to production.
    """
    joinfile = path
    sourcefiles = msettings['JOINED'][path]
    # Generate the combo file as a string.
    combo_data, dirname = combine_files(joinfile, sourcefiles, client)
    
    if path.endswith('.css'):
        mime_type = 'text/css'
    elif joinfile.endswith('.js'):
        mime_type = 'application/javascript'

    return HttpResponse(combo_data, mimetype=mime_type)

def _find_combo_match(path):
    """
    Calculate the key to check the MEDIASYNC['JOINED'] dict for, perform the
    lookup, and return the matching key string if a match is found. If no
    match is found, return None instead.
    """
    if not path:
        # _form_key_str() says this isn't even a CSS/JS file.
        return None

    if not msettings['JOINED'].has_key(path):
        # No combo file match found. Must be an single file.
        return None
    else:
        # Combo match found, return the JOINED key.
        return path

def static_serve(request, path, client):
    """
    Given a request for a media asset, this view does the necessary wrangling
    to get the correct thing delivered to the user. This can also emulate the
    combo behavior seen when SERVE_REMOTE == False and EMULATE_COMBO == True.
    """
    if msettings['SERVE_REMOTE']:
        # We're serving from S3, redirect there.
        url = client.remote_media_url().strip('/') + '/%(path)s'
        return redirect_to(request, url, path=path)

    if not msettings['SERVE_REMOTE'] and msettings['EMULATE_COMBO']:
        # Combo emulation is on and we're serving media locally. Try to see if
        # the given path matches a combo file defined in the JOINED dict in
        # the MEDIASYNC settings dict.
        combo_match = _find_combo_match(path)
        if combo_match:
            # We found a combo file match. Combine it and serve the result.
            return combo_serve(request, combo_match, client)

    # No combo file, but we're serving locally. Use the standard (inefficient)
    # Django static serve view.
    resp = serve(request, path, document_root=client.media_root)
    resp.content = client.process(resp.content, resp['Content-Type'], path)
    return resp
