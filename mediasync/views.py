"""
This module contains views used to serve static media if 
msettings['SERVE_REMOTE'] == False. See mediasync.urls to see how
these are shimmed in.

The static_serve() function is where the party starts.
"""
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

def _form_key_str(path):
    """
    Given a URL path, massage it into a key we can perform a lookup on the
    MEDIASYNC['JOINED'] dict with.
    
    This mostly involves figuring into account the CSS_PATH and JS_PATH
    settings, if they have been set.
    """
    if path.endswith('.css'):
        media_path_prefix = msettings['CSS_PATH']
    elif path.endswith('.js'):
        media_path_prefix = msettings['JS_PATH']
    else:
        # This isn't a CSS/JS file, no combo for you.
        return None

    if media_path_prefix:
        # CS/JSS path prefix has been set. Factor that into the key lookup.
        if not media_path_prefix.endswith('/'):
            # We need to add this slash so we can lop it off the 'path'
            # variable, to match the value in the JOINED dict.
            media_path_prefix += '/'

        if path.startswith(media_path_prefix):
            # Given path starts with the CSS/JS media prefix. Lop this off
            # so we can perform a lookup in the JOINED dict.
            return path[len(media_path_prefix):]
        else:
            # Path is in a root dir, send along as-is.
            return path

    # No CSS/JS path prefix set. Keep it raw.
    return path

def _find_combo_match(path):
    """
    Calculate the key to check the MEDIASYNC['JOINED'] dict for, perform the
    lookup, and return the matching key string if a match is found. If no
    match is found, return None instead.
    """
    key_str = _form_key_str(path)
    if not key_str:
        # _form_key_str() says this isn't even a CSS/JS file.
        return None

    if not msettings['JOINED'].has_key(key_str):
        # No combo file match found. Must be an single file.
        return None
    else:
        # Combo match found, return the JOINED key.
        return key_str

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
