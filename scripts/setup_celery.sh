#!/bin/bash
# Complete setup and test script for Celery integration

echo "=== UNJobAtlas Celery Setup and Test ==="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
echo "✓ Checking dependencies..."
if ! python -c "import celery" 2>/dev/null; then
    echo "❌ Celery not installed. Run: pip install -r requirements.txt"
    exit 1
fi

if ! python -c "import redis" 2>/dev/null; then
    echo "❌ Redis not installed. Run: pip install -r requirements.txt"
    exit 1
fi

# Check if Redis is running
echo "✓ Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis not running. Run: docker compose up -d redis"
    exit 1
fi

# Check if PostgreSQL is running
echo "✓ Checking PostgreSQL connection..."
if ! docker compose ps db | grep -q "Up"; then
    echo "❌ PostgreSQL not running. Run: docker compose up -d db"
    exit 1
fi

# Run migrations
echo "✓ Running migrations..."
python manage.py migrate --no-input

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To test the Celery integration:"
echo ""
echo "1. Start Celery worker in a separate terminal:"
echo "   ./scripts/run_celery_worker.sh"
echo ""
echo "2. Run the crawler:"
echo "   python manage.py crawl_unjobs"
echo ""
echo "3. Monitor processing in Django admin:"
echo "   http://127.0.0.1:8000/admin/core/rawjobdata/"
echo ""
echo "4. Check Celery worker logs for task execution"
echo ""
