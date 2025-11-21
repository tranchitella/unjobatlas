# Celery Integration Summary

## What Was Implemented

### 1. Dependencies Added
- `celery>=5.3.0` - Distributed task queue
- `redis>=5.0.0` - Message broker and result backend
- `django-celery-beat>=2.5.0` - Periodic task scheduler

### 2. Celery Configuration

**config/celery.py**
- Main Celery application configuration
- Auto-discovery of tasks from Django apps
- Task serialization and timezone settings

**config/__init__.py**
- Imports Celery app to ensure it's loaded when Django starts

**config/settings.py**
- `CELERY_BROKER_URL`: Redis connection for task queue
- `CELERY_RESULT_BACKEND`: Redis for storing task results
- Task serialization, timezone, and time limits configured

### 3. Async Task Processing

**core/tasks.py**
- `process_raw_job_data(raw_job_id)`: Main task to download and parse job details
  - Downloads job page using Playwright with Cloudflare handling
  - Parses HTML content with BeautifulSoup
  - Extracts job title, organization, location, and description
  - Converts HTML description to Markdown
  - Updates RawJobData with extracted information
  - **Retry logic**: Automatically retries up to 5 times with 60-second countdown between attempts
  - Updates processing status and error tracking

- `download_and_parse_job(url)`: Helper function to scrape job details
  - Uses Playwright for browser automation
  - Handles Cloudflare Turnstile challenges
  - Extracts structured data from job posting page

- `handle_cloudflare_challenge(pw_page)`: Detects and waits for Cloudflare verification

### 4. Django Signals

**core/signals.py**
- `trigger_job_processing`: Post-save signal on RawJobData model
- Automatically launches Celery task when new RawJobData is created with PENDING status
- Prevents circular imports by importing task function inside signal handler

**core/apps.py**
- Updated `CoreConfig.ready()` to import signals when Django starts
- Ensures signals are connected before any models are created

### 5. Infrastructure Updates

**docker-compose.yml**
- Added Redis 7 service
- Container name: `unjobatlas_redis`
- Port: 6379
- Health checks configured

**.env.example**
- Added `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` settings

**scripts/run_celery_worker.sh**
- Helper script to start Celery worker
- Activates virtual environment if present
- Runs worker with info log level

### 6. Documentation

**README.md** updated with:
- Celery worker startup instructions
- Explanation of async processing workflow
- Job processing status descriptions
- Redis connection information

## How It Works

### Workflow

1. **Crawler runs**: `python manage.py crawl_unjobs`
   - Scrapes job listing index pages
   - Creates `RawJobData` entries with `post_number` and `source_url`
   - Sets status to `PENDING`

2. **Signal triggered**: When `RawJobData` is saved with `PENDING` status
   - Django signal `trigger_job_processing` fires
   - Calls `process_raw_job_data.delay(instance.id)` to queue async task

3. **Celery worker processes**: Task executes asynchronously
   - Updates status to `PROCESSING`
   - Downloads full job page with Playwright
   - Parses HTML and extracts job details
   - Converts description to Markdown
   - Updates RawJobData with complete information
   - Sets status to `PROCESSED` or `FAILED`

4. **Retry on failure**: If task fails
   - Celery automatically retries (max 5 attempts)
   - Waits 60 seconds between retries
   - Updates `processing_attempts` counter
   - Stores error message in `processing_error` field
   - Final status set to `FAILED` after 5 attempts

### Status Flow

```
PENDING (created by crawler)
   ↓
PROCESSING (task started)
   ↓
PROCESSED (success) or FAILED (after 5 retries)
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Redis

```bash
docker compose up -d redis
```

### 3. Update Environment Variables

Add to your `.env` file:
```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Start Celery Worker

In a separate terminal:
```bash
./scripts/run_celery_worker.sh
```

Or directly:
```bash
celery -A config worker --loglevel=info
```

### 6. Run Crawler

```bash
python manage.py crawl_unjobs
```

## Monitoring

### Check Task Status in Django Admin

Navigate to the admin panel and view `Raw Job Data`:
- Filter by status to see pending/processing/processed/failed jobs
- View `processing_attempts` to see retry count
- Check `processing_error` for error messages
- See `last_processing_attempt` for timing

### Celery Worker Logs

The worker terminal will show:
- Task received messages
- Task execution progress
- Retry attempts
- Success/failure notifications

### Redis Connection

Check Redis is running:
```bash
docker compose ps redis
redis-cli ping  # Should return PONG
```

## Troubleshooting

### Task Not Processing

1. Check Celery worker is running
2. Verify Redis is accessible: `redis-cli ping`
3. Check `.env` has correct `CELERY_BROKER_URL`
4. Look for errors in worker terminal

### Task Failing

1. Check `processing_error` field in admin
2. Verify Playwright is installed: `playwright install chromium`
3. Check internet connectivity for downloading job pages
4. Look for Cloudflare challenges (may need manual verification)

### Signal Not Triggering

1. Ensure `core/apps.py` imports signals in `ready()` method
2. Check Django logs for import errors
3. Verify signal is registered: should see import during Django startup

## Future Enhancements

- Add Celery Beat for periodic crawling
- Implement task result monitoring dashboard
- Add task priority queue for urgent jobs
- Create task to convert RawJobData → JobAdvertisement
- Add rate limiting to respect unjobs.org server
- Implement dead letter queue for permanently failed tasks
