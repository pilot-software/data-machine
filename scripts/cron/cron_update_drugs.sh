#!/bin/bash
# Cron job to auto-update drug database

set -e

echo "🔄 Starting drug database update..."
echo "Time: $(date)"

cd /Users/samirkolhe/Desktop/New\ folder/data-machine

# Activate virtual environment if needed
# source venv/bin/activate

# Download latest data
echo "📥 Downloading latest data..."
python download_expanded_data.py >> logs/cron_update.log 2>&1

# Load into database
echo "💾 Loading into database..."
python load_expanded_data.py >> logs/cron_update.log 2>&1

# Cleanup old logs (keep last 30 days)
find logs/ -name "cron_update.log.*" -mtime +30 -delete

echo "✅ Update completed at $(date)"
echo "---"
