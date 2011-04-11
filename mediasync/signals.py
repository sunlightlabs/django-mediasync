from django.core import management
from django.core.management.base import CommandError
from django.dispatch import Signal
from mediasync import SyncException, listdir_recursive
from mediasync.conf import msettings
import os
import subprocess

pre_sync = Signal()
post_sync = Signal()

def collectstatic_receiver(sender, **kwargs):
    try:
        management.call_command('collectstatic')
    except CommandError:
        raise SyncException("collectstatic management command not found")

def sass_receiver(sender, **kwargs):
    
    sass_cmd = msettings.get("SASS_COMMAND", "sass")
    
    root = msettings['STATIC_ROOT']
    
    for filename in listdir_recursive(root):
        
        if filename.endswith('.sass') or filename.endswith('.scss'):
            
            sass_path = os.path.join(root, filename)
            css_path = sass_path[:-4] + "css"
            
            cmd = "%s %s %s" % (sass_cmd, sass_path, css_path)
            subprocess.call(cmd.split(' '))