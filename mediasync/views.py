from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render_to_response

MIMETYPES = {
    'css': 'text/css',
    'js': 'text/javascript',
}

def static(request, filename, extension):
    path = "%s.%s" % (filename, extension)
    return render_to_response(path, mimetype=MIMETYPES.get(extension, 'text/plain'))