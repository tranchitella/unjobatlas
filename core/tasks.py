"""
Celery tasks for processing job data.
"""

import json
import logging
import time
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from celery import shared_task
from django.utils.timezone import utc
from markdownify import markdownify as md
from openai import OpenAI
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from config.settings import OPENAI_API_KEY
from core.models import JobAdvertisement, LanguageRequirement, Organization, RawJobData

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5, "countdown": 60},
    retry_backoff=True,
)
def process_raw_job_data(self, raw_job_id):
    """
    Download and parse job details from source URL.

    This task:
    1. Downloads the full job posting page using Playwright
    2. Parses the HTML content
    3. Extracts job details (title, organization, location, content)
    4. Converts HTML description to Markdown
    5. Updates the RawJobData record with extracted information

    Args:
        raw_job_id: ID of the RawJobData record to process

    Raises:
        Exception: Any errors during processing trigger a retry (max 5 attempts)
    """
    raw_job = None
    try:
        # Get the raw job data record
        raw_job = RawJobData.objects.get(id=raw_job_id)
        logger.info(
            f"Processing job {raw_job.post_number} (attempt {raw_job.processing_attempts + 1})"
        )

        # Update status to downloading
        raw_job.status = RawJobData.Statuses.DOWNLOADING
        raw_job.processing_attempts += 1
        raw_job.last_processing_attempt = datetime.now(utc)
        raw_job.save()

        # Download and parse the job page
        job_data = download_and_parse_job(raw_job.post_number, raw_job.source_url)

        # Update the raw job data with parsed information
        raw_job.post_name = job_data.get("post_name", "")
        raw_job.post_content = job_data.get("post_content", "")
        raw_job.organization_name = job_data.get("organization_name", "")
        raw_job.location_country = job_data.get("location_country", "")
        raw_job.location_city = job_data.get("location_city", "")
        raw_job.status = RawJobData.Statuses.DOWNLOADED
        raw_job.processing_error = None
        raw_job.save()

        logger.info(f"Successfully downloaded job {raw_job.post_number}")

        # Wait a couple of seconds before completing to avoid overwhelming the server
        time.sleep(2)

        return f"Successfully downloaded job {raw_job.post_number}"

    except RawJobData.DoesNotExist:
        # Don't retry if the record doesn't exist
        logger.error(f"RawJobData with id {raw_job_id} does not exist")
        return f"RawJobData with id {raw_job_id} does not exist"

    except Exception as e:
        # Update error information
        if raw_job:
            raw_job.processing_error = str(e)
            raw_job.status = RawJobData.Statuses.FAILED
            raw_job.save()
            logger.error(f"Error processing job {raw_job.post_number}: {str(e)}")
        else:
            logger.error(f"Error processing raw_job_id {raw_job_id}: {str(e)}")

        # Check if we've exceeded max retries
        if self.request.retries >= 5:
            logger.error(f"Failed to process job after 5 attempts: {str(e)}")
            return f"Failed to process job after 5 attempts: {str(e)}"

        # Re-raise to trigger retry
        logger.warning(
            f"Retrying job processing (attempt {self.request.retries + 1}/5)"
        )
        raise


def download_and_parse_job(post_number, url):
    """
    Download job posting page and extract relevant information.

    Args:
        post_number: Unique identifier of the job posting
        url: URL of the job posting

    Returns:
        dict: Extracted job data including post_name, post_content, organization_name, etc.

    Raises:
        Exception: If download or parsing fails
    """
    logger.info(f"Downloading job {post_number} from {url}")

    # Use Playwright to download the page
    with sync_playwright() as p:
        # Launch browser (headless mode)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        pw_page = context.new_page()

        try:
            # Navigate to the job detail page
            pw_page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Wait for main content to load
            pw_page.wait_for_selector("div.fp-snippet", timeout=30000)

            # Get page content
            content = pw_page.content()

        except PlaywrightTimeoutError as e:
            logger.warning(f"Timeout loading job {post_number}: {str(e)}")
            raise Exception(f"Timeout loading page: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading job {post_number}: {str(e)}")
            raise
        finally:
            browser.close()

    # Parse the HTML content
    soup = BeautifulSoup(content, "lxml")

    # Extract job title
    title_tag = soup.select_one(".container>table>tbody>tr>td>h2")
    if not title_tag:
        logger.warning(f"Could not find title for job {post_number}")
        raise Exception(f"Could not find title for job {post_number}")

    post_name = title_tag.get_text(strip=True)
    logger.info(f"Found job title: {post_name}")

    # Extract job details
    post_content = soup.select_one("div.fp-snippet")
    post_content_html = str(post_content) if post_content else ""

    # Convert HTML to markdown
    post_content_md = md(post_content_html) if post_content_html else ""

    # Extract categories
    location_tag = soup.select_one(".list-group")
    categories = []
    if location_tag:
        list_items = location_tag.find_all("li", class_="list-group-item")
        for item in list_items:
            # Get the text before the <a> tag (the label)
            label = (
                item.get_text(strip=True).split(":")[0]
                if ":" in item.get_text()
                else None
            )
            # Get the <a> tag text (the value)
            link = item.find("a")
            value = link.get_text(strip=True) if link else None

            if label and value:
                categories.append((label, value))

    category_dict = dict(categories)
    logger.info(f"Extracted categories: {category_dict}")

    return {
        "post_number": post_number,
        "post_name": post_name,
        "post_content": post_content_md,
        "source_url": url,
        "organization_name": category_dict.get("Organization", ""),
        "location_country": category_dict.get("Country", ""),
        "location_city": category_dict.get("City", ""),
    }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 120},
    retry_backoff=True,
)
def extract_job_data(self, raw_job_id):
    """
    Extract structured job information from raw job data using OpenAI LLM.

    This task:
    1. Gets the raw job data with markdown content
    2. Uses OpenAI to extract structured information
    3. Creates or updates JobAdvertisement and related records
    4. Updates the RawJobData status to PROCESSED

    Args:
        raw_job_id: ID of the RawJobData record to process

    Raises:
        Exception: Any errors during extraction trigger a retry (max 3 attempts)
    """
    raw_job = None
    try:
        # Get the raw job data record
        raw_job = RawJobData.objects.get(id=raw_job_id)
        logger.info(f"Extracting job data for {raw_job.post_number}")

        # Update status to processing
        raw_job.status = RawJobData.Statuses.PROCESSING
        raw_job.save()

        # Check if content is available
        if not raw_job.post_content:
            raise Exception(f"No content available for job {raw_job.post_number}")

        # Extract structured data using OpenAI
        extracted_data = extract_with_llm(
            post_number=raw_job.post_number,
            post_content=raw_job.post_content,
            organization_name=raw_job.organization_name,
            location_country=raw_job.location_country,
            location_city=raw_job.location_city,
        )

        # Create or get the organization
        organization = get_or_create_organization(
            extracted_data.get("organization_name", raw_job.organization_name)
        )

        # Create the JobAdvertisement
        job_ad = create_job_advertisement(
            raw_job=raw_job, organization=organization, extracted_data=extracted_data
        )

        # Update raw job status
        raw_job.status = RawJobData.Statuses.PROCESSED
        raw_job.job_advertisement = job_ad
        raw_job.processing_error = None
        raw_job.save()

        logger.info(
            f"Successfully extracted and created JobAdvertisement for {raw_job.post_number}"
        )
        return f"Successfully extracted job {raw_job.post_number}"

    except RawJobData.DoesNotExist:
        logger.error(f"RawJobData with id {raw_job_id} does not exist")
        return f"RawJobData with id {raw_job_id} does not exist"

    except Exception as e:
        # Update error information
        if raw_job:
            raw_job.processing_error = str(e)
            raw_job.status = RawJobData.Statuses.FAILED
            raw_job.save()
            logger.error(f"Error extracting job {raw_job.post_number}: {str(e)}")
        else:
            logger.error(f"Error extracting raw_job_id {raw_job_id}: {str(e)}")

        # Check if we've exceeded max retries
        if self.request.retries >= 3:
            logger.error(f"Failed to extract job after 3 attempts: {str(e)}")
            return f"Failed to extract job after 3 attempts: {str(e)}"

        # Re-raise to trigger retry
        logger.warning(
            f"Retrying job extraction (attempt {self.request.retries + 1}/3)"
        )
        raise


def extract_with_llm(
    post_number, post_content, organization_name, location_country, location_city
):
    """
    Use OpenAI to extract structured job information from markdown content.

    Args:
        post_number: Job post number
        post_content: Full job description in markdown format
        organization_name: Organization name from raw data
        location_country: Country from raw data
        location_city: City from raw data

    Returns:
        dict: Extracted job data in structured format

    Raises:
        Exception: If LLM extraction fails
    """
    logger.info(f"Calling OpenAI API for job {post_number}")

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Create the prompt with few-shot examples to prevent hallucination
    system_prompt = """You are a specialized AI assistant for extracting structured information from UN job postings. Your task is to extract specific information from job descriptions and return it as valid JSON.

CRITICAL RULES:
1. ONLY extract information that is explicitly stated in the job posting
2. If a field's information is not found, use null (not "not specified" or empty string)
3. For dates, use YYYY-MM-DD format
4. Return ONLY valid JSON, no additional text or explanation
5. Do not invent or assume information that is not in the text"""  # noqa: E501

    user_prompt = f"""Extract the following information from this UN job posting and return as valid JSON:

**Job Post Number:** {post_number}
**Organization:** {organization_name}
**Location:** {location_city}, {location_country}

**Job Description (Markdown):**
{post_content[:8000]}

Return a JSON object with these exact fields:
{{
  "organization_name": "string - exact organization name",
  "post_number": "string - job post number",
  "date_posted": "YYYY-MM-DD or null",
  "application_deadline": "YYYY-MM-DD or null",
  "post_name": "string - job title",
  "contract_type": "one of: consultant, temporary, fixed_term, internship, volunteering, other",
  "contract_duration": "string or null",
  "renewable": true/false,
  "location_region": "string or null",
  "location_country": "string",
  "location_city": "string or null",
  "work_arrangement": "one of: on-site, remote, hybrid, or null",
  "thematic_area": "string or null",
  "position_level": "string (e.g., P-3, NO-2, G-5, Consultancy, Internship) or null",
  "brief_description": "string - brief 2-3 sentence summary of the position",
  "main_skills_competencies": "string - main competencies required, or null",
  "technical_skills": "string - technical skills required, or null",
  "minimum_academic_qualifications": "string - education requirements, or null",
  "minimum_experience": "string - experience requirements, or null",
  "language_requirements": [
    {{
      "language": "string - language name",
      "requirement_level": "required or preferred",
      "proficiency_level": "basic, intermediate, advanced, fluent, or native (or null)"
    }}
  ],
  "tags": ["string array of relevant tags like 'Emergency', 'ICT', 'Finance', etc."]
}}

EXAMPLE OUTPUT FORMAT:
{{
  "organization_name": "UNICEF",
  "post_number": "12345",
  "date_posted": "2025-01-15",
  "application_deadline": "2025-02-28",
  "post_name": "Programme Officer",
  "contract_type": "fixed_term",
  "contract_duration": "2 years",
  "renewable": true,
  "location_region": "East Asia and Pacific",
  "location_country": "Thailand",
  "location_city": "Bangkok",
  "work_arrangement": "on-site",
  "thematic_area": "Programme",
  "position_level": "P-3",
  "brief_description": "The Programme Officer will support UNICEF's programme development and implementation in Thailand, focusing on child protection and education initiatives.",
  "main_skills_competencies": "Programme management, stakeholder engagement, monitoring and evaluation",
  "technical_skills": "Results-based management, project planning, budget management",
  "minimum_academic_qualifications": "Advanced university degree in social sciences, international development, or related field",
  "minimum_experience": "5 years of relevant professional experience in programme management",
  "language_requirements": [
    {{"language": "English", "requirement_level": "required", "proficiency_level": "fluent"}},
    {{"language": "Thai", "requirement_level": "preferred", "proficiency_level": "intermediate"}}
  ],
  "tags": ["Programme", "Child Protection", "Education", "Thailand"]
}}

Now extract the information from the provided job posting above. Return ONLY valid JSON."""  # noqa: E501

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for more consistent, less creative output
            response_format={"type": "json_object"},  # Ensure JSON response
        )

        # Extract the response content
        content = response.choices[0].message.content
        logger.info(f"Received OpenAI response for job {post_number}")

        # Parse JSON response
        extracted_data = json.loads(content)
        logger.info(f"Successfully parsed JSON for job {post_number}")

        return extracted_data

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response for job {post_number}: {str(e)}")
        raise Exception(f"Invalid JSON response from LLM: {str(e)}")
    except Exception as e:
        logger.error(f"OpenAI API error for job {post_number}: {str(e)}")
        raise


def get_or_create_organization(organization_name):
    """
    Get or create an Organization record.

    Args:
        organization_name: Name of the organization

    Returns:
        Organization: The organization instance
    """
    if not organization_name:
        organization_name = "Unknown Organization"

    organization, created = Organization.objects.get_or_create(
        name=organization_name, defaults={"abbreviation": organization_name}
    )

    if created:
        logger.info(f"Created new organization: {organization_name}")
    else:
        logger.info(f"Found existing organization: {organization_name}")

    return organization


# Extract valid values from model choices
VALID_CONTRACT_TYPES = {choice[0] for choice in JobAdvertisement.CONTRACT_TYPE_CHOICES}
VALID_WORK_ARRANGEMENTS = {
    choice[0] for choice in JobAdvertisement.WORK_ARRANGEMENT_CHOICES
}
VALID_POSITION_LEVELS = {
    choice[0] for choice in JobAdvertisement.POSITION_LEVEL_CHOICES
}
VALID_REQUIREMENT_LEVELS = {
    choice[0] for choice in LanguageRequirement.REQUIREMENT_LEVEL_CHOICES
}
VALID_PROFICIENCY_LEVELS = {
    choice[0] for choice in LanguageRequirement.PROFICIENCY_LEVEL_CHOICES
}


# Validation helper function
def validate_choice_field(value, valid_values, default, field_name):
    """Validate and normalize choice field values."""
    if not value:
        return default
    # Normalize to lowercase and remove extra spaces
    normalized = str(value).lower().strip()
    if normalized in valid_values:
        return normalized
    logger.warning(f"Invalid {field_name} value: '{value}'. Using default: '{default}'")
    return default


def create_job_advertisement(raw_job, organization, extracted_data):
    """
    Create a JobAdvertisement record from extracted data.

    Args:
        raw_job: RawJobData instance
        organization: Organization instance
        extracted_data: Dictionary of extracted job data

    Returns:
        JobAdvertisement: The created job advertisement instance
    """
    logger.info(f"Creating JobAdvertisement for {raw_job.post_number}")

    # Parse dates (handle None values)
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse date: {date_str}")
            return None

    date_posted = parse_date(extracted_data.get("date_posted"))
    application_deadline = parse_date(extracted_data.get("application_deadline"))

    # If dates are missing, use fallback values
    if not date_posted:
        date_posted = raw_job.crawled_at.date()
    if not application_deadline:
        application_deadline = datetime.now(utc).date() + timedelta(days=30)

    # Validate choice fields
    contract_type = validate_choice_field(
        extracted_data.get("contract_type"),
        VALID_CONTRACT_TYPES,
        "other",
        "contract_type",
    )
    work_arrangement = validate_choice_field(
        extracted_data.get("work_arrangement"),
        VALID_WORK_ARRANGEMENTS,
        "on-site",
        "work_arrangement",
    )
    position_level = validate_choice_field(
        extracted_data.get("position_level"),
        VALID_POSITION_LEVELS,
        None,
        "position_level",
    )

    # Create the JobAdvertisement
    job_ad = JobAdvertisement.objects.create(
        organization=organization,
        post_number=extracted_data.get("post_number", raw_job.post_number),
        date_posted=date_posted,
        application_deadline=application_deadline,
        post_name=extracted_data.get("post_name", raw_job.post_name or "Unknown"),
        contract_type=contract_type,
        contract_duration=extracted_data.get("contract_duration"),
        renewable=extracted_data.get("renewable", False),
        location_region=extracted_data.get("location_region"),
        location_country=extracted_data.get(
            "location_country", raw_job.location_country
        ),
        location_city=extracted_data.get("location_city", raw_job.location_city),
        work_arrangement=work_arrangement,
        thematic_area=extracted_data.get("thematic_area"),
        position_level=position_level,
        brief_description=extracted_data.get("brief_description"),
        main_skills_competencies=extracted_data.get("main_skills_competencies"),
        technical_skills=extracted_data.get("technical_skills"),
        minimum_academic_qualifications=extracted_data.get(
            "minimum_academic_qualifications"
        ),
        minimum_experience=extracted_data.get("minimum_experience"),
        tags=extracted_data.get("tags", []),
        source_url=raw_job.source_url,
    )

    logger.info(f"Created JobAdvertisement: {job_ad.id}")

    # Create language requirements
    language_requirements = extracted_data.get("language_requirements", [])
    for lang_req in language_requirements:
        if lang_req.get("language"):
            requirement_level = validate_choice_field(
                lang_req.get("requirement_level"),
                VALID_REQUIREMENT_LEVELS,
                "preferred",
                "requirement_level",
            )
            proficiency_level = validate_choice_field(
                lang_req.get("proficiency_level"),
                VALID_PROFICIENCY_LEVELS,
                None,
                "proficiency_level",
            )

            LanguageRequirement.objects.create(
                job=job_ad,
                language=lang_req["language"],
                requirement_level=requirement_level,
                proficiency_level=proficiency_level,
            )
            logger.info(f"Created language requirement: {lang_req['language']}")

    return job_ad
