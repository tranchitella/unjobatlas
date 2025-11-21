# UNJobAtlas

A Django application built with Django 4.2 LTS.

## Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (for PostgreSQL)
- Make (for running development tasks)

### Installation

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt

# Or use make to set up environment
make .venv
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start PostgreSQL and Redis with Docker:
```bash
docker compose up -d
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:  
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to see your application.

## Database

The project uses PostgreSQL 18 and Redis running in Docker. 

- PostgreSQL data is stored in `postgres_data/` directory (gitignored)
- Redis is used as the Celery message broker and result backend

### Docker Commands

- Start services: `docker compose up -d`
- Stop services: `docker compose down`
- View logs: `docker compose logs -f db` or `docker compose logs -f redis`
- Reset database: `docker compose down -v` (warning: deletes all data)

### Database Connection

Default connection settings (defined in `.env.example`):
- **PostgreSQL:**
  - Host: localhost
  - Port: 5432
  - Database: unjobatlas
  - User: unjobatlas
  - Password: unjobatlas
- **Redis:**
  - Host: localhost
  - Port: 6379

## Project Structure

- `config/` - Project settings and Celery configuration
- `core/` - Main application with models, tasks, and signals
- `manage.py` - Django management script
- `docker-compose.yml` - PostgreSQL and Redis configuration
- `scripts/` - Helper scripts for running Celery worker and crawler

## Web Crawler

The project includes a management command to crawl UNjobs.org and populate the database with job postings. The crawler uses **asynchronous task processing** with Celery to download and parse job details.

### How It Works

1. **Index Crawling**: The `crawl_unjobs` command scrapes the job listing pages and creates `RawJobData` entries with minimal information (post_number, source_url)
2. **Async Processing**: When a new `RawJobData` entry is created with `PENDING` status, a Django signal automatically triggers a Celery task
3. **Job Details**: The Celery task downloads the full job posting page, parses the content, and updates the `RawJobData` entry with complete information
4. **Retry Logic**: If downloading fails, the task automatically retries up to 5 times with 1-minute intervals

### Starting the Celery Worker

Before running the crawler, start the Celery worker to process jobs asynchronously:

```bash
# Option 1: Using the helper script
./scripts/run_celery_worker.sh

# Option 2: Direct command
celery -A config worker --loglevel=info
```

Keep the Celery worker running in a separate terminal window or use a process manager like supervisord.

### Running the Crawler

```bash
# Crawl the first page of job listings
python manage.py crawl_unjobs
```

The crawler will:
1. Scrape job listings from unjobs.org (first page only)
2. Create `RawJobData` entries with `PENDING` status for new jobs
3. Celery workers automatically process each job in the background
4. Monitor processing status in Django admin at `/admin/core/rawjobdata/`

**Note**: Make sure the Celery worker is running before executing the crawler, otherwise jobs won't be processed.

### Features

- **Incremental crawling**: Remembers the last crawled job and only adds new postings
- **Duplicate prevention**: Checks for existing posts before adding
- **Async processing**: Job details are downloaded asynchronously by Celery workers
- **Automatic retries**: Failed downloads retry up to 5 times with 1-minute delays
- **Error handling**: Logs errors and tracks processing attempts
- **State tracking**: Maintains crawler state and processing status in the database
- **Status monitoring**: View processing status in Django admin:
  - `PENDING`: Waiting to be processed
  - `PROCESSING`: Currently being downloaded
  - `PROCESSED`: Successfully downloaded and parsed
  - `FAILED`: Failed after 5 retry attempts
  - `SKIPPED`: Duplicate or invalid data

### Scheduling with Cron

To run the crawler multiple times per day, add to your crontab:

```bash
# Edit crontab
crontab -e

# Add these lines to run crawler every 6 hours
0 */6 * * * /path/to/your/project/scripts/run_crawler.sh

# Or run at specific times (e.g., 6 AM, 12 PM, 6 PM)
0 6,12,18 * * * /path/to/your/project/scripts/run_crawler.sh
```

Make the script executable:
```bash
chmod +x scripts/run_crawler.sh
```

**Important**: Ensure the Celery worker is running as a background service (via supervisord, systemd, or similar) so it can process the jobs created by the cron job.

## Development

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Run all QA checks (format, sort imports, lint)
make qa

# Run QA checks without making changes (CI mode)
make check-qa

# Individual commands
make format          # Format code with black
make sort-imports    # Sort imports with isort
make lint           # Check code with flake8

# Check only (no changes)
make check-format
make check-imports
```

### Testing

```bash
# Run tests
make test

# Run tests only
make test-run

# Generate coverage report
make test-coverage
```

### Available Make Targets

- `make .venv` - Create virtual environment and install dependencies
- `make qa` - Run all QA checks (format, sort imports, lint)
- `make check-qa` - Run QA checks in check mode (for CI)
- `make format` - Format code with black
- `make check-format` - Check code formatting
- `make sort-imports` - Sort imports with isort
- `make check-imports` - Check import sorting
- `make lint` - Run flake8 linter
- `make test` - Run tests and generate coverage
- `make test-run` - Run tests only
- `make test-coverage` - Generate coverage report
