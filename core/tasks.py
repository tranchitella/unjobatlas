"""
Celery tasks for processing job data.
"""

import logging
import time
from datetime import datetime

from bs4 import BeautifulSoup
from celery import shared_task
from django.utils.timezone import utc
from markdownify import markdownify as md
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from core.models import RawJobData

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

        # Update status to processing
        raw_job.status = RawJobData.Statuses.PROCESSING
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
        raw_job.status = RawJobData.Statuses.PROCESSED
        raw_job.processing_error = None
        raw_job.save()

        logger.info(f"Successfully processed job {raw_job.post_number}")

        # Wait a couple of seconds before completing to avoid overwhelming the server
        time.sleep(2)

        return f"Successfully processed job {raw_job.post_number}"

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
