#!/bin/bash
# Cron job script to run the UNjobs crawler
# Make it executable: chmod +x scripts/run_crawler.sh

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Project root is one level up from scripts directory
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment and run crawler
"$PROJECT_DIR/.venv/bin/python" manage.py crawl_unjobs

# Log the execution (create log directory if it doesn't exist)
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
echo "Crawler run completed at $(date)" >> "$LOG_DIR/crawler.log"
