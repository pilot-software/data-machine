#!/bin/bash
# Setup cron job for drug database updates

echo "🔄 Setting up auto-update cron job..."

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create cron job entry
CRON_JOB="0 2 * * 0 $SCRIPT_DIR/cron_update_drugs.sh"

# Check if cron job already exists
(crontab -l 2>/dev/null | grep -F "$SCRIPT_DIR/cron_update_drugs.sh") && {
    echo "⚠️  Cron job already exists"
    echo "Current cron jobs:"
    crontab -l | grep "cron_update_drugs"
    exit 0
}

# Add cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "📅 Schedule: Every Sunday at 2 AM"
echo "📝 Command: $CRON_JOB"
echo ""
echo "🔍 Verify with: crontab -l"
echo "📊 Check logs: tail -f logs/cron_update.log"
echo ""
echo "🧪 Test manually: ./cron_update_drugs.sh"
