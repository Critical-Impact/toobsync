from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext_lazy as _
from background_task.models import Task
from sync.models import Source
from sync.tasks import index_source_task

from common.logger import log


class Command(BaseCommand):
    help = 'Resets tasks for specific sources by name'

    def add_arguments(self, parser):
        parser.add_argument('names', type=str, help='Name(s) of the source(s), comma-separated')

    def handle(self, *args, **options):
        names = options['names'].split(',')
        sources = Source.objects.filter(name__in=names)

        if len(sources) != len(names):
            missing_sources = set(names) - set(sources.values_list('name', flat=True))
            raise CommandError('Source(s) with name(s) "%s" do not exist' % ', '.join(missing_sources))

        for source in sources:
            log.info(f'Resetting tasks for source: {source}')
            verbose_name = _('Index media from source "{}"')
            index_source_task(
                str(source.pk),
                repeat=source.index_schedule,
                queue=str(source.pk),
                priority=5,
                verbose_name=verbose_name.format(source.name)
            )
            source.save()

        log.info('Done')