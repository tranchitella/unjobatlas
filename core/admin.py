from django.contrib import admin
from .models import Organization, JobAdvertisement, LanguageRequirement


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin interface for Organizations."""
    
    list_display = [
        'name',
        'abbreviation',
        'website',
        'job_count',
    ]
    
    search_fields = [
        'name',
        'abbreviation',
        'description',
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'abbreviation',
                'website',
                'description',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def job_count(self, obj):
        """Display the number of job advertisements for this organization."""
        return obj.job_advertisements.count()
    job_count.short_description = 'Job Ads'


class LanguageRequirementInline(admin.TabularInline):
    """Inline admin for language requirements."""
    model = LanguageRequirement
    extra = 1


@admin.register(JobAdvertisement)
class JobAdvertisementAdmin(admin.ModelAdmin):
    """Admin interface for Job Advertisements."""
    
    list_display = [
        'post_number',
        'post_name',
        'organization',
        'location_country',
        'position_level',
        'date_posted',
        'application_deadline',
        'is_active',
    ]
    
    list_filter = [
        'organization',
        'contract_type',
        'work_arrangement',
        'position_level',
        'location_country',
        'date_posted',
        'application_deadline',
    ]
    
    search_fields = [
        'post_number',
        'post_name',
        'organization',
        'location_country',
        'location_city',
        'thematic_area',
        'brief_description',
    ]
    
    readonly_fields = ['created_at', 'updated_at', 'is_active', 'days_until_deadline']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'organization',
                'post_number',
                'post_name',
                'date_posted',
                'application_deadline',
                'source_url',
            )
        }),
        ('Contract Details', {
            'fields': (
                'contract_type',
                'contract_duration',
                'renewable',
            )
        }),
        ('Location', {
            'fields': (
                'location_region',
                'location_country',
                'location_city',
                'work_arrangement',
            )
        }),
        ('Position Details', {
            'fields': (
                'thematic_area',
                'position_level',
            )
        }),
        ('Description and Requirements', {
            'fields': (
                'brief_description',
                'main_skills_competencies',
                'technical_skills',
                'minimum_academic_qualifications',
                'minimum_experience',
            )
        }),
        ('Categorization', {
            'fields': ('tags',)
        }),
        ('Metadata', {
            'fields': (
                'is_active',
                'days_until_deadline',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [LanguageRequirementInline]
    
    date_hierarchy = 'date_posted'


@admin.register(LanguageRequirement)
class LanguageRequirementAdmin(admin.ModelAdmin):
    """Admin interface for Language Requirements."""
    
    list_display = [
        'job',
        'language',
        'requirement_level',
        'proficiency_level',
    ]
    
    list_filter = [
        'requirement_level',
        'proficiency_level',
        'language',
    ]
    
    search_fields = [
        'job__post_number',
        'job__post_name',
        'language',
    ]
