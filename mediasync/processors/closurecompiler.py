from mediasync import JS_MIMETYPES
from urllib import urlencode
import httplib

HEADERS = {"content-type": "application/x-www-form-urlencoded"}

def compile(filedata, content_type, remote_path, is_active):
    
    is_js = (content_type in JS_MIMETYPES or remote_path.lower().endswith('.js'))
    
    if is_js:
        
        params = urlencode({
            'js_code': filedata,
            'compilation_level': 'SIMPLE_OPTIMIZATIONS',
            'output_info': 'compiled_code',
            'output_format': 'text',
        })

        conn = httplib.HTTPConnection('closure-compiler.appspot.com')
        conn.request('POST', '/compile', params, HEADERS)
        response = conn.getresponse()
        data = response.read()
        conn.close
        
        return data