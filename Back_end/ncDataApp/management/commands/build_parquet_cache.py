import os

from django.conf import settings
from django.core.management.base import BaseCommand

from ncDataApp.cache_precompute import run_precompute


class Command(BaseCommand):
    help = "Build Parquet cache entries for nc or mean endpoint by week and location."

    def add_arguments(self, parser):
        parser.add_argument(
            "--endpoint",
            choices=["nc", "mean"],
            required=True,
            help="Endpoint cache to build.",
        )
        parser.add_argument(
            "--points-csv",
            default=None,
            help="Optional CSV path with lat,lon columns (absolute or relative to Back_end).",
        )
        parser.add_argument(
            "--start-date",
            default=None,
            help="ISO date (YYYY-MM-DD). Defaults to 1999-01-04.",
        )
        parser.add_argument(
            "--end-date",
            default=None,
            help="ISO date (YYYY-MM-DD). Defaults to 2021-12-27.",
        )
        parser.add_argument(
            "--shard-count",
            type=int,
            default=1,
            help="Total number of shards for parallel precompute. Default: 1.",
        )
        parser.add_argument(
            "--shard-index",
            type=int,
            default=0,
            help="0-based shard index to execute. Must be < shard-count.",
        )

    def handle(self, *args, **options):
        original_cwd = os.getcwd()
        try:
            # Existing model code opens large datasets via relative paths like "Nc_data/...".
            # Force working dir to BASE_DIR (Back_end) so commands work from repo root too.
            os.chdir(settings.BASE_DIR)
            summary = run_precompute(
                endpoint=options["endpoint"],
                points_csv=options["points_csv"],
                start_date=options["start_date"],
                end_date=options["end_date"],
                shard_count=options["shard_count"],
                shard_index=options["shard_index"],
            )
        finally:
            os.chdir(original_cwd)
        self.stdout.write(
            self.style.SUCCESS(
                f"Done: endpoint={summary['endpoint']} rows={summary['rows_processed']} points={summary['points_count']} shard={summary['shard_index']}/{summary['shard_count']} cache={summary['cache_file']}"
            )
        )
