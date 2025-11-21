# Quick Reference: Celery Integration

## Commands

### Start Services
```bash
# Start PostgreSQL and Redis
docker compose up -d

# Start Celery worker (keep this running)
./scripts/run_celery_worker.sh
# OR
celery -A config worker --loglevel=info

# Start Django development server
python manage.py runserver
```

### Run Crawler
```bash
# Crawl and create RawJobData entries
python manage.py crawl_unjobs

# Celery worker will automatically process each entry
```

### Monitor
```bash
# View processing status in admin
http://127.0.0.1:8000/admin/core/rawjobdata/

# Check Redis
redis-cli ping  # Should return PONG

# View Celery worker logs
# (check the terminal where worker is running)
```

## Files Created/Modified

### New Files
- `config/celery.py` - Celery app configuration
- `core/tasks.py` - Async task to download and parse jobs
- `core/signals.py` - Signal to trigger tasks on RawJobData creation
- `scripts/run_celery_worker.sh` - Helper script to start worker
- `scripts/setup_celery.sh` - Setup validation script
- `docs/CELERY_SETUP.md` - Detailed documentation

### Modified Files
- `requirements.txt` - Added celery, redis, django-celery-beat
- `config/__init__.py` - Import Celery app
- `config/settings.py` - Celery configuration settings
- `core/apps.py` - Connect signals in ready() method
- `docker-compose.yml` - Added Redis service
- `.env.example` - Added Celery environment variables
- `README.md` - Updated with Celery documentation

## Task Retry Behavior

- **Max retries**: 5 attempts
- **Retry interval**: 60 seconds (1 minute)
- **Auto-retry**: Enabled for all exceptions
- **Backoff**: Exponential backoff enabled

### Example Timeline
```
Attempt 1: t=0s (fails)
Attempt 2: t=60s (fails)
Attempt 3: t=120s (fails)
Attempt 4: t=180s (fails)
Attempt 5: t=240s (fails)
Status: FAILED (after 5 attempts)
```

## Status Flow

```
┌─────────┐
│ PENDING │ ← Created by crawler
└────┬────┘
     │ Signal triggers Celery task
     ↓
┌────────────┐
│ PROCESSING │ ← Task started
└─────┬──────┘
      │
      ├─→ Success → ┌───────────┐
      │             │ PROCESSED │
      │             └───────────┘
      │
      └─→ Failure → Retry (up to 5×)
                    ↓
                    ┌────────┐
                    │ FAILED │ ← After 5 attempts
                    └────────┘
```

## Environment Variables

Add to `.env`:
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Troubleshooting

### Tasks not processing
```bash
# Check Redis
docker compose ps redis
redis-cli ping

# Check Celery worker is running
ps aux | grep celery

# Restart worker
pkill -f celery
./scripts/run_celery_worker.sh
```

### View task details
```python
# Django shell
python manage.py shell

from core.models import RawJobData
jobs = RawJobData.objects.filter(status='FAILED')
for job in jobs:
    print(f"{job.post_number}: {job.processing_error}")
    print(f"Attempts: {job.processing_attempts}")
```

## Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Start Redis**: `docker compose up -d redis`
3. **Run migrations**: `python manage.py migrate`
4. **Start worker**: `./scripts/run_celery_worker.sh`
5. **Run crawler**: `python manage.py crawl_unjobs`
6. **Monitor admin**: http://127.0.0.1:8000/admin/core/rawjobdata/
