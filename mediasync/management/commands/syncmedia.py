from django.core.management.base import BaseCommand, CommandError
import mediasync

class Command(BaseCommand):
    
    help = "Sync local media with S3"
    args = '[bucket] ([prefix])'
    
    requires_model_validation = False
    
    def handle(self, *args, **options):

        try:
            mediasync.sync()
        except ValueError, ve:
            raise CommandError('%s\nUsage is mediasync %s' % (ve.message, self.args))