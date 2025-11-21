"""
Django signals for the core app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import RawJobData


@receiver(post_save, sender=RawJobData)
def trigger_job_processing(sender, instance, created, **kwargs):
    """
    Trigger async processing when a new RawJobData record is created with PENDING status.

    This signal:
    - Fires after a RawJobData record is saved
    - Only triggers for new records (created=True) with PENDING status
    - Launches a Celery task to download and parse the job details

    Args:
        sender: The model class (RawJobData)
        instance: The actual RawJobData instance being saved
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    # Only process new records with PENDING status
    if created and instance.status == RawJobData.Statuses.PENDING:
        # Import here to avoid circular imports
        from core.tasks import process_raw_job_data

        # Launch the async task
        process_raw_job_data.delay(instance.id)
