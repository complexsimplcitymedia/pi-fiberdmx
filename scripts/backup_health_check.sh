#!/bin/bash
# Backup health check - runs daily to verify backups are happening
# Alerts if no backup has been created in the last 8 days

BACKUP_DIR="/backup"
BACKUP_LOG="/var/log/system_backup.log"
ALERT_LOG="/var/log/backup_alert.log"
MAX_DAYS_WITHOUT_BACKUP=8
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Running backup health check..." >> "$ALERT_LOG"

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "[$TIMESTAMP] WARNING: Backup directory does not exist: $BACKUP_DIR" >> "$ALERT_LOG"
    exit 1
fi

# Find the most recent backup
LAST_BACKUP=$(ls -t "$BACKUP_DIR"/system_backup_*.tar.gz 2>/dev/null | head -1)

if [ -z "$LAST_BACKUP" ]; then
    echo "[$TIMESTAMP] ALERT: No backup files found in $BACKUP_DIR" >> "$ALERT_LOG"
    # Create alert message
    cat > /tmp/backup_alert.txt << 'ALERT_MSG'
⚠️ BACKUP ALERT ⚠️

The Fiber Laser DMX system has NO BACKUPS.

ACTION REQUIRED:
1. Connect device to power
2. Ensure network connectivity
3. First backup will run on Sunday at 2 AM (or manually trigger via SSH)
4. Check /var/log/system_backup.log for status

Device: Fiber Laser DMX (Raspberry Pi 5)
Alert Time: $(date)
ALERT_MSG
    exit 1
fi

# Get the modification time of the last backup
LAST_BACKUP_TIME=$(stat -c %Y "$LAST_BACKUP")
CURRENT_TIME=$(date +%s)
SECONDS_SINCE_BACKUP=$((CURRENT_TIME - LAST_BACKUP_TIME))
DAYS_SINCE_BACKUP=$((SECONDS_SINCE_BACKUP / 86400))

echo "[$TIMESTAMP] Last backup: $(basename $LAST_BACKUP) ($DAYS_SINCE_BACKUP days ago)" >> "$ALERT_LOG"

# Check if backup is overdue
if [ $DAYS_SINCE_BACKUP -gt $MAX_DAYS_WITHOUT_BACKUP ]; then
    echo "[$TIMESTAMP] ALERT: No backup for $DAYS_SINCE_BACKUP days (threshold: $MAX_DAYS_WITHOUT_BACKUP)" >> "$ALERT_LOG"
    
    # Create alert message
    cat > /tmp/backup_alert.txt << ALERT_MSG
⚠️ BACKUP OVERDUE ⚠️

The Fiber Laser DMX system backup is OVERDUE!

Last Backup: $(basename $LAST_BACKUP)
Days Since Backup: $DAYS_SINCE_BACKUP days
Recommended: Weekly (7 days)

ACTION REQUIRED:
1. Connect device to power to allow next scheduled backup
2. Scheduled backups run Sunday at 2 AM UTC
3. Check /var/log/system_backup.log for status
4. Manually trigger backup via SSH if urgent

Device: Fiber Laser DMX (Raspberry Pi 5)
Alert Time: $(date)
ALERT_MSG

    # Display alert on console if available
    echo "======================================" >&2
    echo "⚠️  BACKUP OVERDUE ALERT" >&2
    echo "======================================" >&2
    echo "Last backup: $DAYS_SINCE_BACKUP days ago" >&2
    echo "Action: Connect to power for next backup" >&2
    echo "======================================" >&2
    
    exit 1
else
    echo "[$TIMESTAMP] OK: Backup current ($DAYS_SINCE_BACKUP days since last backup)" >> "$ALERT_LOG"
    exit 0
fi
