"""
Management command to rebuild Elasticsearch indices.
"""

from django.core.management.base import BaseCommand

from core.documents import JobAdvertisementDocument


class Command(BaseCommand):
    """Command to rebuild Elasticsearch indices for job advertisements."""

    help = "Rebuild Elasticsearch indices for job advertisements"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the index before rebuilding",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write("Rebuilding Elasticsearch index for JobAdvertisement...")

        if options["delete"]:
            self.stdout.write("Deleting existing index...")
            JobAdvertisementDocument._index.delete(ignore=404)
            self.stdout.write(self.style.SUCCESS("Index deleted"))

        # Create the index
        self.stdout.write("Creating index...")
        JobAdvertisementDocument.init()
        self.stdout.write(self.style.SUCCESS("Index created"))

        # Index all documents
        self.stdout.write("Indexing all JobAdvertisement records...")
        count = 0
        doc = JobAdvertisementDocument()
        for instance in doc.get_queryset():
            doc.update(instance)
            count += 1
            if count % 100 == 0:
                self.stdout.write(f"Indexed {count} records...")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully indexed {count} JobAdvertisement records")
        )
