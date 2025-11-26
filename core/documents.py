"""
Elasticsearch document definitions for core models.
"""

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from .models import JobAdvertisement, LanguageRequirement, Organization


@registry.register_document
class JobAdvertisementDocument(Document):
    """Elasticsearch document for JobAdvertisement model."""

    # Organization fields
    organization = fields.ObjectField(
        properties={
            "id": fields.IntegerField(),
            "name": fields.TextField(
                fields={
                    "keyword": fields.KeywordField(),
                    "suggest": fields.CompletionField(),
                }
            ),
            "abbreviation": fields.TextField(
                fields={
                    "keyword": fields.KeywordField(),
                    "suggest": fields.CompletionField(),
                }
            ),
        }
    )

    # Language requirements
    language_requirements = fields.NestedField(
        properties={
            "language": fields.TextField(
                fields={
                    "keyword": fields.KeywordField(),
                }
            ),
            "requirement_level": fields.KeywordField(),
            "proficiency_level": fields.KeywordField(),
        }
    )

    # Text fields with multi-field mapping for exact matches and suggestions
    post_number = fields.TextField(
        fields={
            "keyword": fields.KeywordField(),
        }
    )

    post_name = fields.TextField(
        analyzer="english",
        fields={
            "keyword": fields.KeywordField(),
            "suggest": fields.CompletionField(),
        },
    )

    # Date fields
    date_posted = fields.DateField()
    application_deadline = fields.DateField()

    # Choice fields as keywords
    contract_type = fields.KeywordField()
    work_arrangement = fields.KeywordField()
    position_level = fields.KeywordField()

    # Location fields with keyword and suggest fields
    location_region = fields.TextField(
        fields={
            "keyword": fields.KeywordField(),
            "suggest": fields.CompletionField(),
        }
    )

    location_country = fields.TextField(
        fields={
            "keyword": fields.KeywordField(),
            "suggest": fields.CompletionField(),
        }
    )

    location_city = fields.TextField(
        fields={
            "keyword": fields.KeywordField(),
            "suggest": fields.CompletionField(),
        }
    )

    # Text fields for full-text search
    contract_duration = fields.TextField()
    thematic_area = fields.TextField(
        fields={
            "keyword": fields.KeywordField(),
        }
    )

    brief_description = fields.TextField(analyzer="english")
    main_skills_competencies = fields.TextField(analyzer="english")
    technical_skills = fields.TextField(analyzer="english")
    minimum_academic_qualifications = fields.TextField(analyzer="english")
    minimum_experience = fields.TextField(analyzer="english")

    # Boolean field
    renewable = fields.BooleanField()

    # Tags as keywords for filtering
    tags = fields.KeywordField(multi=True)

    # Metadata
    source_url = fields.KeywordField()
    created_at = fields.DateField()
    updated_at = fields.DateField()

    # Computed fields
    is_active = fields.BooleanField()
    days_until_deadline = fields.IntegerField()

    class Index:
        """Elasticsearch index configuration."""

        name = "job_advertisements"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "english": {
                        "type": "english",
                    }
                }
            },
        }

    class Django:
        """Django model configuration."""

        model = JobAdvertisement
        fields = []  # We explicitly define all fields above

        # Related models to fetch
        related_models = [Organization, LanguageRequirement]

    def get_queryset(self):
        """Return the queryset to be indexed."""
        return (
            super()
            .get_queryset()
            .select_related("organization")
            .prefetch_related("language_requirements")
        )

    def get_instances_from_related(self, related_instance):
        """
        Update JobAdvertisement documents when related models change.

        If an Organization or LanguageRequirement is updated,
        re-index all related JobAdvertisement documents.
        """
        if isinstance(related_instance, Organization):
            return related_instance.job_advertisements.all()
        elif isinstance(related_instance, LanguageRequirement):
            return JobAdvertisement.objects.filter(pk=related_instance.job.pk)
        return JobAdvertisement.objects.none()

    def prepare_organization(self, instance):
        """Prepare organization data for indexing."""
        if instance.organization:
            return {
                "id": instance.organization.id,
                "name": instance.organization.name,
                "abbreviation": instance.organization.abbreviation or "",
            }
        return None

    def prepare_language_requirements(self, instance):
        """Prepare language requirements data for indexing."""
        return [
            {
                "language": lr.language,
                "requirement_level": lr.requirement_level,
                "proficiency_level": lr.proficiency_level or "",
            }
            for lr in instance.language_requirements.all()
        ]

    def prepare_is_active(self, instance):
        """Prepare is_active computed property."""
        return instance.is_active

    def prepare_days_until_deadline(self, instance):
        """Prepare days_until_deadline computed property.

        Returns None if days_until_deadline is not set, so jobs with missing deadlines
        can be distinguished from those whose deadline is today (0).
        """
        days = instance.days_until_deadline
        return days if days is not None else None
