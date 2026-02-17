from django.core.management.base import BaseCommand

from ncDataApp.request_cache import merge_cache_shards


class Command(BaseCommand):
    help = "Merge shard cache files into the main endpoint cache file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--endpoint",
            choices=["nc", "mean"],
            required=True,
            help="Endpoint cache shards to merge.",
        )

    def handle(self, *args, **options):
        shard_count, row_count = merge_cache_shards(options["endpoint"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Merged endpoint={options['endpoint']} shard_files={shard_count} merged_rows={row_count}"
            )
        )
