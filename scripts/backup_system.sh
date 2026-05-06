#!/bin/bash
# Weekly system backup script
# Backs up root filesystem to a backup partition/directory

set -e

BACKUP_DIR="/backup"
BACKUP_NAME="system_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
BACKUP_LOG="/var/log/system_backup.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo "[$TIMESTAMP] Creating backup directory: $BACKUP_DIR"
    sudo mkdir -p "$BACKUP_DIR"
    sudo chmod 755 "$BACKUP_DIR"
fi

echo "[$TIMESTAMP] Starting weekly system backup..." | tee -a "$BACKUP_LOG"

# Exclude certain directories that don't need to be backed up
EXCLUDE_DIRS=(
    --exclude='/proc'
    --exclude='/sys'
    --exclude='/dev'
    --exclude='/run'
    --exclude='/tmp'
    --exclude='/mnt'
    --exclude='/media'
    --exclude='/lost+found'
    --exclude='/boot/firmware'
    --exclude='/var/cache'
    --exclude='/var/tmp'
    --exclude='/home/laser-dmx/.cache'
)

# Create backup (excluding system/cache dirs)
echo "[$TIMESTAMP] Backing up root filesystem to $BACKUP_DIR/$BACKUP_NAME" | tee -a "$BACKUP_LOG"
sudo tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    "${EXCLUDE_DIRS[@]}" \
    -C / \
    . 2>&1 | tee -a "$BACKUP_LOG"

BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
echo "[$TIMESTAMP] Backup completed. Size: $BACKUP_SIZE" | tee -a "$BACKUP_LOG"

# Keep only last 4 weekly backups (approx 1 month)
echo "[$TIMESTAMP] Cleaning up old backups (keeping last 4)..." | tee -a "$BACKUP_LOG"
sudo ls -t "$BACKUP_DIR"/system_backup_*.tar.gz 2>/dev/null | tail -n +5 | xargs -r sudo rm -v | tee -a "$BACKUP_LOG"

echo "[$TIMESTAMP] Weekly backup completed successfully!" | tee -a "$BACKUP_LOG"
