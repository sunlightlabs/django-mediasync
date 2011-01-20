from django.conf import settings
import os
from subprocess import Popen, PIPE

def _yui_path(settings):
    if not hasattr(settings, 'MEDIASYNC'):
        return None
    path = settings.MEDIASYNC.get('YUI_COMPRESSOR_PATH', None)
    if path:
        path = os.path.realpath(os.path.expanduser(path))
    return path

def css_minifier(filedata, content_type, remote_path, is_active):
    is_css = (content_type == 'text/css' or remote_path.lower().endswith('.css'))
    yui_path = _yui_path(settings)
    if is_css and yui_path and is_active:
        proc = Popen(['java', '-jar', yui_path, '--type', 'css'], stdout=PIPE,
                     stderr=PIPE, stdin=PIPE)
        stdout, stderr = proc.communicate(input=filedata)
        return str(stdout)

def js_minifier(filedata, content_type, remote_path, is_active):
    is_js = (content_type == 'text/javascript' or remote_path.lower().endswith('.js'))
    yui_path = _yui_path(settings)
    if is_js and yui_path and is_active:
        proc = Popen(['java', '-jar', yui_path, '--type', 'js'], stdout=PIPE,
                     stderr=PIPE, stdin=PIPE)
        stdout, stderr = proc.communicate(input=filedata)
        return str(stdout)
