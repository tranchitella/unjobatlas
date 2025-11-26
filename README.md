# UNJobAtlas

A Django application built with Django 4.2 LTS.

## Setup

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (for PostgreSQL, Redis, and Elasticsearch)
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

4. Start PostgreSQL, Redis, and Elasticsearch with Docker:
```bash
docker compose up -d
```

5. Create Elasticsearch index:
```bash
python manage.py search_index --create
```

6. Run migrations:
```bash
python manage.py migrate
```

7. Create a superuser:
```bash
python manage.py createsuperuser
```

8. Build the frontend:
```bash
cd frontend
npm install
npm run build
cd ..
```

9. Run the development server:
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to see your application.

## Services

The project uses PostgreSQL, Redis, and Elasticsearch running in Docker. 

- **PostgreSQL 18**: Main database for storing job data
  - Data stored in `postgres_data/` directory (gitignored)
- **Redis 8**: Celery message broker and result backend
- **Elasticsearch 8.19**: Search engine for job advertisements
  - Data stored in `elasticsearch_data/` directory (gitignored)
  - Provides full-text search, filtering, and aggregations

### Docker Commands

- Start services: `docker compose up -d`
- Stop services: `docker compose down`
- View logs: `docker compose logs -f [db|redis|elasticsearch]`
- Reset database: `docker compose down -v` (warning: deletes all data)
- Check service health: `docker compose ps`

### Service Connection Details

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
- **Elasticsearch:**
  - Host: http://localhost:9200
  - Ports: 9200 (HTTP), 9300 (Transport)

## Project Structure

- `config/` - Project settings and Celery configuration
- `core/` - Main application with models, tasks, signals, and Elasticsearch documents
- `frontend/` - Next.js application (React, TypeScript, Tailwind CSS, shadcn/ui)
- `manage.py` - Django management script
- `docker-compose.yml` - PostgreSQL, Redis, and Elasticsearch configuration
- `scripts/` - Helper scripts for running Celery worker and crawler
- `docs/` - Documentation for Celery, LLM extraction, Elasticsearch, and frontend

## Elasticsearch Search

The project uses Elasticsearch for powerful search capabilities across job advertisements. All `JobAdvertisement` records are automatically indexed in real-time.

### Features

- **Full-text search**: Search job titles, descriptions, and requirements
- **Filtering**: Filter by organization, location, contract type, position level
- **Aggregations**: Get faceted results (e.g., jobs by country, organization)
- **Autocomplete**: Suggestions for organization names, locations
- **Date range queries**: Find active jobs, jobs posted within date ranges
- **Nested queries**: Search language requirements
- **Real-time indexing**: Jobs are indexed automatically when created/updated

### Quick Start

```bash
# Verify Elasticsearch is running
curl http://localhost:9200

# Create the index
python manage.py search_index --create

# Index existing jobs
python manage.py rebuild_index

# Check indexed documents
curl http://localhost:9200/job_advertisements/_count?pretty
```

### Search Examples

```python
from core.documents import JobAdvertisementDocument

# Search by job title
search = JobAdvertisementDocument.search()
results = search.query("match", post_name="Programme Officer")

# Filter by country
search = JobAdvertisementDocument.search()
results = search.filter("term", location_country__keyword="Kenya")

# Active jobs only
from datetime import date
search = JobAdvertisementDocument.search()
results = search.filter("range", application_deadline={"gte": date.today()})

# Execute and iterate
for hit in results:
    print(f"{hit.post_number}: {hit.post_name}")
```

For detailed documentation, see:
- [Elasticsearch Setup Guide](docs/ELASTICSEARCH_SETUP.md)
- [Elasticsearch Quick Start](docs/ELASTICSEARCH_QUICKSTART.md)

## Web Crawler & Job Processing

The project includes a comprehensive pipeline for crawling job postings from UNjobs.org and extracting structured information using AI:

### Processing Pipeline

1. **Index Crawling**: Scrapes job listing pages and creates `RawJobData` entries
2. **Content Download**: Celery task downloads full job posting HTML and converts to Markdown
3. **LLM Extraction**: OpenAI GPT-4 extracts structured job information from content
4. **Job Creation**: Creates `JobAdvertisement` records with all fields populated
5. **Elasticsearch Indexing**: Jobs are automatically indexed for search

### Status Flow

```
PENDING → DOWNLOADING → DOWNLOADED → PROCESSING → PROCESSED
                                                 ↘ FAILED
```

### Prerequisites

1. **Celery Worker**: Must be running to process jobs
2. **OpenAI API Key**: Required for LLM extraction (add to `.env`)

```bash
# In .env file
OPENAI_API_KEY=sk-your-api-key-here
```

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
- **Two-stage processing**: Separate download and extraction tasks
- **AI-powered extraction**: Uses OpenAI GPT-4 to extract structured job data
- **Automatic retries**: Failed tasks retry with exponential backoff
- **Error handling**: Logs errors and tracks processing attempts
- **Real-time indexing**: Jobs automatically appear in Elasticsearch
- **State tracking**: Maintains crawler state and processing status in the database
- **Status monitoring**: View processing status in Django admin at `/admin/core/rawjobdata/`
  - `PENDING`: Waiting to be processed
  - `DOWNLOADING`: Downloading job content
  - `DOWNLOADED`: Content downloaded, ready for extraction
  - `PROCESSING`: Extracting data with LLM
  - `PROCESSED`: Successfully processed and JobAdvertisement created
  - `FAILED`: Failed after maximum retry attempts
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

For detailed documentation, see:
- [Celery Setup Guide](docs/CELERY_SETUP.md)
- [LLM Extraction Documentation](docs/LLM_EXTRACTION_SETUP.md)

## Frontend

The application includes a **Next.js** single-page application with a three-column desktop interface:

- **Left Column (280px)**: Search filters with faceted search (organization, location, contract type, languages, position level)
- **Center Column (flex)**: Scrollable job list with card-based display
- **Right Column (600px)**: Detailed view of selected job

### Technology Stack

- **Next.js 16**: React framework with App Router and static export
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: High-quality React component library

### Architecture

The frontend is built as a **static export** and served directly by Django:
- No separate Node.js server needed
- All assets compiled to `frontend/build/` directory
- Django serves `index.html` and static files
- Single integrated process for development and production

### Quick Start

```bash
# Build frontend
cd frontend && npm run build && cd ..

# Start Django (serves frontend + API)
python manage.py runserver

# Visit http://127.0.0.1:8000/
```

### Development Workflow

For rapid frontend development with hot reload:

```bash
# Terminal 1: Django API
python manage.py runserver

# Terminal 2: Next.js dev server
cd frontend && npm run dev

# Visit http://localhost:3000/
```

### Current State

The frontend is fully functional with mock data and ready for API integration. Next steps:
1. Create Django REST API endpoints (`/api/jobs/`, `/api/jobs/:id/`, `/api/facets/`)
2. Replace mock data with API calls
3. Implement search and filtering logic
4. Add pagination

For detailed documentation, see [Frontend Setup Guide](docs/FRONTEND_SETUP.md).

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
