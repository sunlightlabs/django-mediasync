from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from mediasync.conf import msettings
import mediasync
import time

class Command(BaseCommand):
    
    help = "Sync local media with remote client"
    args = '[options]'
    
    requires_model_validation = False
    
    option_list = BaseCommand.option_list + (
        make_option("-F", "--force", dest="force", help="force files to sync", action="store_true"),
        make_option("-q", "--quiet", dest="verbose", help="disable output", action="store_false", default=True),
    )
    
    def handle(self, *args, **options):
        
        msettings['SERVE_REMOTE'] = True
        msettings['VERBOSE'] = options.get('verbose')
        
        force = options.get('force') or False
        
        try:
            
            start_time = time.time()
            mediasync.sync(force=force)
            end_time = time.time()
            
            secs = (end_time - start_time)
            print 'sync finished in %0.3f seconds' % secs
            
        except ValueError, ve:
            raise CommandError('%s\nUsage is mediasync %s' % (ve.message, self.args))