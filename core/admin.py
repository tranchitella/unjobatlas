from django.contrib import admin

from .models import (
    CrawlerState,
    JobAdvertisement,
    LanguageRequirement,
    Organization,
    RawJobData,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organizations."""

    list_display = [
        "name",
        "abbreviation",
        "website",
        "job_count",
    ]

    search_fields = [
        "name",
        "abbreviation",
        "description",
    ]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "abbreviation",
                    "website",
                    "description",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def job_count(self, obj):
        """Display the number of job advertisements for this organization."""
        return obj.job_advertisements.count()

    job_count.short_description = "Job Ads"


class LanguageRequirementInline(admin.TabularInline):
    """Inline admin for language requirements."""

    model = LanguageRequirement
    extra = 1


@admin.register(JobAdvertisement)
class JobAdvertisementAdmin(admin.ModelAdmin):
    """Admin interface for Job Advertisements."""

    list_display = [
        "post_number",
        "post_name",
        "organization",
        "location_country",
        "position_level",
        "date_posted",
        "application_deadline",
        "is_active",
    ]

    list_filter = [
        "organization",
        "contract_type",
        "work_arrangement",
        "position_level",
        "location_country",
        "date_posted",
        "application_deadline",
    ]

    search_fields = [
        "post_number",
        "post_name",
        "organization",
        "location_country",
        "location_city",
        "thematic_area",
        "brief_description",
    ]

    readonly_fields = ["created_at", "updated_at", "is_active", "days_until_deadline"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "organization",
                    "post_number",
                    "post_name",
                    "date_posted",
                    "application_deadline",
                    "source_url",
                )
            },
        ),
        (
            "Contract Details",
            {
                "fields": (
                    "contract_type",
                    "contract_duration",
                    "renewable",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "location_region",
                    "location_country",
                    "location_city",
                    "work_arrangement",
                )
            },
        ),
        (
            "Position Details",
            {
                "fields": (
                    "thematic_area",
                    "position_level",
                )
            },
        ),
        (
            "Description and Requirements",
            {
                "fields": (
                    "brief_description",
                    "main_skills_competencies",
                    "technical_skills",
                    "minimum_academic_qualifications",
                    "minimum_experience",
                )
            },
        ),
        ("Categorization", {"fields": ("tags",)}),
        (
            "Metadata",
            {
                "fields": (
                    "is_active",
                    "days_until_deadline",
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [LanguageRequirementInline]

    date_hierarchy = "date_posted"


@admin.register(LanguageRequirement)
class LanguageRequirementAdmin(admin.ModelAdmin):
    """Admin interface for Language Requirements."""

    list_display = [
        "job",
        "language",
        "requirement_level",
        "proficiency_level",
    ]

    list_filter = [
        "requirement_level",
        "proficiency_level",
        "language",
    ]

    search_fields = [
        "job__post_number",
        "job__post_name",
        "language",
    ]


@admin.register(CrawlerState)
class CrawlerStateAdmin(admin.ModelAdmin):
    """Admin interface for Crawler State."""

    list_display = [
        "source_name",
        "last_crawled_post_number",
        "last_crawl_time",
        "total_jobs_crawled",
    ]

    readonly_fields = [
        "last_crawl_time",
        "total_jobs_crawled",
    ]

    fieldsets = (
        (
            "Source Information",
            {
                "fields": (
                    "source_name",
                    "last_crawled_post_number",
                )
            },
        ),
        (
            "Statistics",
            {
                "fields": (
                    "total_jobs_crawled",
                    "last_crawl_time",
                )
            },
        ),
        ("Error Information", {"fields": ("last_error",), "classes": ("collapse",)}),
    )


@admin.register(RawJobData)
class RawJobDataAdmin(admin.ModelAdmin):
    """Admin interface for Raw Job Data."""

    list_display = [
        "post_number",
        "post_name",
        "organization_name",
        "location_country",
        "status",
        "processing_attempts",
        "crawled_at",
    ]

    list_filter = [
        "status",
        "organization_name",
        "location_country",
        "crawled_at",
    ]

    search_fields = [
        "post_number",
        "post_name",
        "organization_name",
        "location_country",
        "location_city",
    ]

    readonly_fields = [
        "crawled_at",
        "updated_at",
        "processing_attempts",
        "last_processing_attempt",
    ]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "post_number",
                    "post_name",
                    "source_url",
                )
            },
        ),
        (
            "Extracted Data",
            {
                "fields": (
                    "organization_name",
                    "location_country",
                    "location_city",
                    "post_content",
                )
            },
        ),
        (
            "Processing Status",
            {
                "fields": (
                    "status",
                    "job_advertisement",
                    "processing_attempts",
                    "last_processing_attempt",
                    "processing_error",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "crawled_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    date_hierarchy = "crawled_at"

    actions = ["mark_as_pending", "mark_as_downloaded", "mark_as_processed"]

    def mark_as_pending(self, request, queryset):
        """Mark selected items as pending for reprocessing."""
        count = 0
        for item in queryset:
            item.status = RawJobData.Statuses.PENDING
            item.save()  # This triggers the signal that launches process_raw_job_data
            count += 1
        self.message_user(
            request, f"{count} items marked as pending. Processing tasks queued."
        )

    mark_as_pending.short_description = "Mark as pending for processing"

    def mark_as_downloaded(self, request, queryset):
        """Mark selected items as downloaded and trigger data extraction."""
        count = 0
        for item in queryset:
            item.status = RawJobData.Statuses.DOWNLOADED
            item.save()  # This triggers the signal that launches extract_job_data
            count += 1
        self.message_user(
            request,
            f"{count} items marked as downloaded. Data extraction tasks queued.",
        )

    mark_as_downloaded.short_description = (
        "Mark as downloaded and ready for data extraction"
    )

    def mark_as_processed(self, request, queryset):
        """Mark selected items as processed."""
        updated = queryset.update(status=RawJobData.Statuses.PROCESSED)
        self.message_user(request, f"{updated} items marked as processed.")

    mark_as_processed.short_description = "Mark as processed"
