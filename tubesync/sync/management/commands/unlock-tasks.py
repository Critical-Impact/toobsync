from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from background_task.models import Task
from common.logger import log

class Command(BaseCommand):
    help = 'Unlocks jobs, which are locked by dead processes.'

    def handle(self, *args, **options):
        log.info('Fetching locked tasks...')
        # Iter all locked tasks
        locked_tasks = Task.objects.locked(timezone.now())
        for locked_task in locked_tasks:
            if locked_task.locked_by_pid_running():
                log.info(f'Tasks is still fine: {locked_task}')
            else:
                log.info(f'Tasks needs unlocking: {locked_task}')
                if locked_task.is_repeating_task():
                    # Deleting repeating tasks is bad (would result in no more source
                    # index tasks), so we schedule them before deletion.
                    # This matches the flow in the bg_runner (w/o signals).
                    log.info(f'Re-schedule repeating task: {locked_task}')
                    locked_task.create_repetition()

                # Deleting a locked, non-repeating task should not be too bad,
                # as it should be re-created on the source index task again.
                log.info(f'Deleting task: {locked_task}')
                locked_task.delete()

                ## Unlocking by setting locked_by and locked_at to None
                ## results in source index tasks being repeated over and over,
                ## since those seem to be the ones crashing process_tasks for me.
                ## Re-execution of the same source index task results in duplicate
                ## download tasks being scheduled, without them ever being executed
                # locked = locked_tasks.filter(pk=locked_task.pk)
                # locked.update(locked_by=None, locked_at=None)

        log.info('Done')