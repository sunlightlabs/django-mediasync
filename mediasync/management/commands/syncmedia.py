from django.core.management.base import BaseCommand, CommandError
import mediasync

class Command(BaseCommand):
    
    help = "Sync local media with S3"
    args = '[bucket] ([prefix])'
    
    requires_model_validation = False
    
    def handle(self, bucket=None, prefix='', *args, **options):

        try:
            mediasync.sync(bucket, prefix.strip('/'))
        except ValueError, ve:
            raise CommandError('%s\nUsage is mediasync %s' % (ve.message, self.args))