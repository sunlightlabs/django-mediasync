from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import mediasync

class Command(BaseCommand):
    
    help = "Sync local media with S3"
    args = '[options]'
    
    requires_model_validation = False
    
    option_list = BaseCommand.option_list + (
        make_option("-f", "--force", dest="force", help="force files to sync", action="store_true"),
    )
    
    def handle(self, *args, **options):
        
        force = options.get('force') or False
        
        try:
            mediasync.sync(force=force)
        except ValueError, ve:
            raise CommandError('%s\nUsage is mediasync %s' % (ve.message, self.args))