"""
Management command to crawl UNjobs.org and populate the database.
"""

from datetime import datetime

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from core.models import CrawlerState, RawJobData


class Command(BaseCommand):
    help = "Crawl the first page of UNjobs.org and add new job postings to the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pages",
            type=int,
            default=5,
            help="Number of pages to crawl looking for the latest crawled post (default: 5)",
        )

    def handle(self, **options):
        self.stdout.write(self.style.SUCCESS("Starting UNjobs.org crawler..."))

        # Get or create crawler state
        crawler_state, _ = CrawlerState.objects.get_or_create(
            source_name=CrawlerState.Sources.UNJOBS, defaults={"total_jobs_crawled": 0}
        )

        try:
            new_jobs = self.crawl_jobs(
                crawler_state=crawler_state, pages=options["pages"]
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully crawled {new_jobs} new job(s). "
                    f"Total crawled: {crawler_state.total_jobs_crawled}"
                )
            )

        except Exception as e:
            crawler_state.last_error = str(e)
            crawler_state.save()
            raise CommandError(f"Crawling failed: {str(e)}")

    def crawl_jobs(self, crawler_state, pages=1):
        """Crawl job listings from unjobs.org using Playwright"""
        base_url = "https://unjobs.org"
        jobs = []

        # Iterate through pages
        page_num = 1
        while page_num <= pages:
            # Use Playwright
            with sync_playwright() as p:
                # Launch browser (headless mode)
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
                pw_page = context.new_page()

                try:
                    # Construct URL for pagination
                    url = f"{base_url}/page/{page_num}" if page_num > 1 else base_url

                    self.stdout.write(
                        self.style.SUCCESS(f"Crawling page {page_num}...")
                    )

                    try:
                        # Navigate to the page and wait for content
                        pw_page.goto(url, wait_until="domcontentloaded", timeout=60000)

                        # Wait for job listings to load
                        pw_page.wait_for_selector(
                            "article div[id].job a.jtitle", timeout=30000
                        )

                        # Get page content
                        content = pw_page.content()

                    except PlaywrightTimeoutError:
                        self.stdout.write(
                            self.style.ERROR(f"Timeout loading page {page_num}")
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f"Failed to fetch page {page_num}: {str(e)}"
                            )
                        )

                    soup = BeautifulSoup(content, "lxml")

                    # Find job listings
                    job_rows = soup.select("article div[id].job a.jtitle")

                    if not job_rows:
                        self.stdout.write(
                            self.style.WARNING(f"No job rows found on page {page_num}")
                        )

                    found_jobs = 0
                    for row in job_rows:
                        source_url = row.get("href", "")
                        post_number = source_url.rsplit("/")[-1]
                        if post_number == crawler_state.last_crawled_post_number:
                            break
                        found_jobs += 1
                        jobs.append(
                            {
                                "post_number": post_number,
                                "source_url": source_url,
                            }
                        )
                    # if less than 25 jobs found, likely last page
                    if found_jobs < 25:
                        break
                    else:
                        page_num += 1
                finally:
                    browser.close()

        # Bulk create new raw data job entries
        new_jobs = 0
        last_post_number = None
        for job_data in reversed(jobs):
            job = RawJobData.objects.filter(
                post_number=job_data["post_number"],
                source_url=job_data["source_url"],
            ).first()
            if job is None:
                new_jobs += 1
                last_post_number = job_data["post_number"]
                RawJobData.objects.create(
                    status=RawJobData.Statuses.PENDING,
                    **job_data,
                )

        # Update crawler state
        if jobs:
            crawler_state.last_crawl_time = datetime.now(utc)
            crawler_state.last_crawled_post_number = last_post_number
            crawler_state.total_jobs_crawled += new_jobs
            crawler_state.save()

        # Return the number of new jobs crawled
        return new_jobs
