from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from mediasync.conf import msettings
import mediasync

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
            mediasync.sync(force=force)
        except ValueError, ve:
            raise CommandError('%s\nUsage is mediasync %s' % (ve.message, self.args))