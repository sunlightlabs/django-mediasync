from django.core import management
from django.core.management.base import CommandError
from django.dispatch import Signal
from mediasync import SyncException

pre_sync = Signal()
post_sync = Signal()

def collectstatic_receiver(sender, **kwargs):
    try:
        management.call_command('collectstatic')
    except CommandError:
        raise SyncException("collectstatic management command not found")
