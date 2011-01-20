try:
    import slimmer
    SLIMMER_INSTALLED = True
except ImportError:
    SLIMMER_INSTALLED = False

def css_minifier(filedata, content_type, remote_path, is_active):
    is_css = content_type == 'text/css' or remote_path.lower().endswith('.css')
    if SLIMMER_INSTALLED and is_active and is_css:
        return slimmer.css_slimmer(filedata)

def js_minifier(filedata, content_type, remote_path, is_active):
    is_js = content_type == 'text/javascript' or remote_path.lower().endswith('.js')
    if SLIMMER_INSTALLED and is_active and is_js:
        return slimmer.css_slimmer(filedata)
