from django.db import models
from django.utils import timezone


class Organization(models.Model):
    """Model representing a UN Organization."""

    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Full name of the organization (e.g., UNICEF, WFP, UNHCR)",
    )
    abbreviation = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="Common abbreviation (e.g., UNICEF, WFP)",
    )
    website = models.URLField(
        max_length=500, blank=True, null=True, help_text="Official website URL"
    )
    description = models.TextField(
        blank=True, null=True, help_text="Brief description of the organization"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="When this record was last updated"
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return self.abbreviation if self.abbreviation else self.name


class JobAdvertisement(models.Model):
    """Model representing a UN Job advertisement."""

    # Basic Information
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="job_advertisements",
        help_text="UN Organization",
    )
    post_number = models.CharField(
        max_length=100, unique=True, help_text="Unique post identifier"
    )
    date_posted = models.DateField(help_text="Date when the job was posted")
    application_deadline = models.DateField(help_text="Application deadline date")
    post_name = models.CharField(max_length=500, help_text="Job title/position name")

    # Contract Information
    CONTRACT_TYPE_CHOICES = [
        ("consultant", "Consultant"),
        ("temporary", "Temporary Appointment"),
        ("fixed_term", "Fixed Term Appointment"),
        ("internship", "Internship"),
        ("volunteering", "Volunteering"),
        ("other", "Other"),
    ]
    contract_type = models.CharField(
        max_length=50, choices=CONTRACT_TYPE_CHOICES, help_text="Type of contract"
    )
    contract_duration = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Duration of contract (e.g., 12 months, 1 year)",
    )
    renewable = models.BooleanField(
        default=False, help_text="Whether the contract is renewable"
    )

    # Location Information
    location_region = models.CharField(
        max_length=200, blank=True, null=True, help_text="Geographic region"
    )
    location_country = models.CharField(
        max_length=200, help_text="Country where the position is based"
    )
    location_city = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="City where the position is based (if available)",
    )

    # Work Arrangement
    WORK_ARRANGEMENT_CHOICES = [
        ("on-site", "On-site"),
        ("remote", "Remote"),
        ("hybrid", "Hybrid"),
    ]
    work_arrangement = models.CharField(
        max_length=50,
        choices=WORK_ARRANGEMENT_CHOICES,
        blank=True,
        null=True,
        help_text="Work arrangement type",
    )

    # Position Details
    thematic_area = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Thematic area/sector (e.g., Emergency, Fund raising, ICT)",
    )

    POSITION_LEVEL_CHOICES = [
        ("consultancy", "Consultancy"),
        ("g-2", "G-2"),
        ("g-3", "G-3"),
        ("g-4", "G-4"),
        ("g-5", "G-5"),
        ("g-6", "G-6"),
        ("g-7", "G-7"),
        ("internship", "Internship"),
        ("no-1", "NO-1"),
        ("no-2", "NO-2"),
        ("no-3", "NO-3"),
        ("no-4", "NO-4"),
        ("p-1", "P-1"),
        ("p-2", "P-2"),
        ("p-3", "P-3"),
        ("p-4", "P-4"),
        ("p-5", "P-5"),
        ("d-1", "D-1"),
        ("d-2", "D-2"),
        ("other", "Other"),
    ]
    position_level = models.CharField(
        max_length=50,
        choices=POSITION_LEVEL_CHOICES,
        blank=True,
        null=True,
        help_text="Position level",
    )

    # Job Description and Requirements
    brief_description = models.TextField(
        blank=True, null=True, help_text="AI-generated summary of the job post"
    )
    main_skills_competencies = models.TextField(
        blank=True, null=True, help_text="Main skills and competencies required"
    )
    technical_skills = models.TextField(
        blank=True, null=True, help_text="Technical skills required"
    )
    minimum_academic_qualifications = models.TextField(
        blank=True, null=True, help_text="Minimum academic qualifications required"
    )
    minimum_experience = models.TextField(
        blank=True, null=True, help_text="Minimum experience required"
    )

    # Tags
    tags = models.JSONField(
        default=list, blank=True, help_text="List of tags for categorization"
    )

    # Metadata
    source_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Original URL of the job posting",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="When this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="When this record was last updated"
    )

    class Meta:
        ordering = ["-date_posted"]
        indexes = [
            models.Index(fields=["organization"]),
            models.Index(fields=["date_posted"]),
            models.Index(fields=["application_deadline"]),
            models.Index(fields=["location_country"]),
            models.Index(fields=["position_level"]),
        ]
        verbose_name = "Job Advertisement"
        verbose_name_plural = "Job Advertisements"

    def __str__(self):
        return f"{self.post_number} - {self.post_name} ({self.organization})"

    @property
    def is_active(self):
        """Check if the job posting is still active."""
        if self.application_deadline:
            return self.application_deadline >= timezone.now().date()
        return False

    @property
    def days_until_deadline(self):
        """Calculate days remaining until application deadline."""
        if self.application_deadline:
            delta = self.application_deadline - timezone.now().date()
            return delta.days
        return None


class LanguageRequirement(models.Model):
    """Model representing language requirements for a job."""

    job = models.ForeignKey(
        JobAdvertisement,
        on_delete=models.CASCADE,
        related_name="language_requirements",
        help_text="Associated job advertisement",
    )

    language = models.CharField(
        max_length=100, help_text="Language name (e.g., English, Spanish, French)"
    )

    REQUIREMENT_LEVEL_CHOICES = [
        ("required", "Required"),
        ("preferred", "Preferred"),
    ]
    requirement_level = models.CharField(
        max_length=50,
        choices=REQUIREMENT_LEVEL_CHOICES,
        help_text="Level of requirement for this language",
    )

    PROFICIENCY_LEVEL_CHOICES = [
        ("basic", "Basic"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
        ("fluent", "Fluent"),
        ("native", "Native"),
    ]
    proficiency_level = models.CharField(
        max_length=50,
        choices=PROFICIENCY_LEVEL_CHOICES,
        blank=True,
        null=True,
        help_text="Required proficiency level",
    )

    class Meta:
        ordering = ["requirement_level", "language"]
        verbose_name = "Language Requirement"
        verbose_name_plural = "Language Requirements"

    def __str__(self):
        return f"{self.language} - {self.get_requirement_level_display()}"


class CrawlerState(models.Model):
    """Model to track the state of the web crawler."""

    class Sources(models.TextChoices):
        UNJOBS = "unjobs.org"

    source_name = models.CharField(
        max_length=100,
        choices=Sources.choices,
        unique=True,
        help_text="Name of the crawling source",
    )
    last_crawled_post_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Last post number successfully crawled",
    )
    last_crawl_time = models.DateTimeField(
        auto_now=True, help_text="When the last crawl was performed"
    )
    total_jobs_crawled = models.IntegerField(
        default=0, help_text="Total number of jobs crawled from this source"
    )
    last_error = models.TextField(
        blank=True, null=True, help_text="Last error encountered during crawling"
    )

    class Meta:
        verbose_name = "Crawler State"
        verbose_name_plural = "Crawler States"

    def __str__(self):
        return f"{self.source_name}"


class RawJobData(models.Model):
    """Model to store raw crawled job data before processing."""

    # Identifiers
    post_number = models.CharField(
        max_length=100, unique=True, help_text="Unique post identifier from source"
    )
    source_url = models.URLField(
        max_length=500, help_text="Original URL of the job posting"
    )

    # Basic Information
    post_name = models.CharField(
        max_length=500,
        help_text="Job title/position name",
        null=True,
        blank=True,
    )
    post_content = models.TextField(
        help_text="Full job description in markdown format",
        null=True,
        blank=True,
    )

    # Raw extracted fields (not yet parsed/validated)
    organization_name = models.CharField(
        max_length=200,
        help_text="Organization name as extracted from source",
        null=True,
        blank=True,
    )
    location_country = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Country as extracted from source",
    )
    location_city = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="City as extracted from source",
    )

    # Processing status
    class Statuses(models.TextChoices):
        PENDING = "Pending Processing"
        PROCESSING = "Currently Processing"
        PROCESSED = "Successfully Processed"
        FAILED = "Processing Failed"
        SKIPPED = "Skipped (duplicate or invalid)"

    status = models.CharField(
        max_length=30,
        choices=Statuses.choices,
        default=Statuses.PENDING,
        help_text="Processing status",
    )

    # Relationship to processed job (if created)
    job_advertisement = models.OneToOneField(
        JobAdvertisement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_data",
        help_text="Linked processed job advertisement",
    )

    # Processing metadata
    processing_error = models.TextField(
        blank=True, null=True, help_text="Error message if processing failed"
    )
    processing_attempts = models.IntegerField(
        default=0, help_text="Number of processing attempts"
    )
    last_processing_attempt = models.DateTimeField(
        null=True, blank=True, help_text="When last processing attempt was made"
    )

    # Timestamps
    crawled_at = models.DateTimeField(
        auto_now_add=True, help_text="When this data was crawled"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="When this record was last updated"
    )

    class Meta:
        ordering = ["-crawled_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["post_number"]),
            models.Index(fields=["crawled_at"]),
        ]
        verbose_name = "Raw Job Data"
        verbose_name_plural = "Raw Job Data"

    def __str__(self):
        return f"{self.post_number} - {self.post_name} [{self.status}]"
