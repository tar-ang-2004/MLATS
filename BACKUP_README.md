# Database Backup System

## Overview

The ATS Resume Checker includes a comprehensive backup system that supports both PostgreSQL and SQLite databases with automated scheduling, compression, and retention management.

## Features

- **Multi-Database Support**: PostgreSQL (pg_dump) and SQLite (file copy)
- **Compression**: Optional gzip compression to save storage space
- **Retention Management**: Automatic cleanup of old backups
- **Scheduled Backups**: Command-line script for cron jobs
- **REST API**: Full backup management through HTTP endpoints
- **Metadata Tracking**: JSON metadata file with backup information

## Configuration

### Environment Variables

```bash
# Backup directory (default: ./backups)
BACKUP_DIR=/path/to/backups

# Retention period in days (default: 30)
BACKUP_RETENTION_DAYS=30

# Enable compression (default: true)
BACKUP_COMPRESS=true
```

### Flask Configuration

The backup system is automatically configured when the Flask application starts. Configuration is loaded from `config.py`:

```python
BACKUP_DIR = os.environ.get('BACKUP_DIR', './backups')
BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
BACKUP_COMPRESS = os.environ.get('BACKUP_COMPRESS', 'true').lower() == 'true'
```

## Manual Backup Operations

### Creating a Backup

```bash
# Create backup via API
curl -X POST http://localhost:5000/api/backup/create \
  -H "Content-Type: application/json" \
  -d '{"backup_name": "manual_backup", "compress": true}'

# Create backup using Python script
python scheduled_backup.py --name manual_backup
```

### Listing Backups

```bash
# List all backups via API
curl http://localhost:5000/api/backup/list

# Response includes backup metadata and statistics
{
  "backups": [
    {
      "backup_name": "manual_backup",
      "file_path": "./backups/manual_backup.sql.gz",
      "file_size": 1048576,
      "compressed": true,
      "database_type": "postgresql",
      "timestamp": "2024-01-15T10:30:00Z",
      "duration": 5.2
    }
  ],
  "statistics": {
    "total_backups": 1,
    "total_size_mb": 1.0,
    "backup_directory": "./backups"
  }
}
```

### Restoring from Backup

```bash
# Restore database via API (CAUTION: This will overwrite current data)
curl -X POST http://localhost:5000/api/backup/restore/manual_backup
```

### Deleting Backups

```bash
# Delete specific backup
curl -X DELETE http://localhost:5000/api/backup/delete/manual_backup
```

## Scheduled Backups

### Command Line Script

The `scheduled_backup.py` script is designed for automated backups:

```bash
# Basic scheduled backup
python scheduled_backup.py

# Custom backup name
python scheduled_backup.py --name daily_backup_$(date +%Y%m%d)

# Uncompressed backup
python scheduled_backup.py --no-compress

# Quiet mode for cron jobs
python scheduled_backup.py --quiet
```

### Cron Job Setup

#### Daily Backups at 2 AM

```cron
0 2 * * * cd /path/to/ats-resume-checker && python scheduled_backup.py --quiet
```

#### Weekly Backups on Sunday at 3 AM

```cron
0 3 * * 0 cd /path/to/ats-resume-checker && python scheduled_backup.py --name weekly_backup --quiet
```

#### Multiple Backup Schedule

```cron
# Daily backups at 2 AM (kept for 7 days)
0 2 * * * cd /path/to/ats && BACKUP_RETENTION_DAYS=7 python scheduled_backup.py --name daily_$(date +\%Y\%m\%d) --quiet

# Weekly backups on Sunday at 3 AM (kept for 30 days)
0 3 * * 0 cd /path/to/ats && BACKUP_RETENTION_DAYS=30 python scheduled_backup.py --name weekly_$(date +\%Y\%m\%d) --quiet

# Monthly backups on 1st at 4 AM (kept for 365 days)
0 4 1 * * cd /path/to/ats && BACKUP_RETENTION_DAYS=365 python scheduled_backup.py --name monthly_$(date +\%Y\%m) --quiet
```

### Systemd Timer (Alternative to Cron)

Create `/etc/systemd/system/ats-backup.service`:

```ini
[Unit]
Description=ATS Resume Checker Backup
After=network.target

[Service]
Type=oneshot
User=ats
WorkingDirectory=/path/to/ats-resume-checker
Environment=BACKUP_RETENTION_DAYS=30
ExecStart=/usr/bin/python3 scheduled_backup.py --quiet
```

Create `/etc/systemd/system/ats-backup.timer`:

```ini
[Unit]
Description=Run ATS backup daily
Requires=ats-backup.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:

```bash
sudo systemctl enable ats-backup.timer
sudo systemctl start ats-backup.timer
```

## Database-Specific Instructions

### PostgreSQL Backups

Prerequisites:
- `pg_dump` and `psql` utilities must be installed
- Database connection parameters are extracted from SQLAlchemy URL
- `PGPASSWORD` environment variable is set automatically

Backup format: SQL dump with `--clean --create` options for full restoration

### SQLite Backups

Prerequisites:
- File system access to the SQLite database file
- Write permissions to the backup directory

Backup format: Direct file copy (with optional gzip compression)

## Security Considerations

### Access Control

- Backup creation is rate-limited (3 requests per hour)
- Restore operations are heavily restricted (2 requests per hour)
- All backup operations are logged for audit purposes

### File Permissions

Ensure backup directory has appropriate permissions:

```bash
# Create backup directory with secure permissions
mkdir -p /var/backups/ats-resume-checker
chmod 750 /var/backups/ats-resume-checker
chown ats:ats /var/backups/ats-resume-checker
```

### Password Security

For PostgreSQL backups, passwords are handled securely:
- `PGPASSWORD` is set only during backup operations
- Database URLs with embedded passwords are sanitized in logs
- Connection strings in backup metadata exclude credentials

## Monitoring and Alerts

### Log Files

Backup operations are logged to:
- Application logs (when using Flask endpoints)
- `backup.log` file (when using scheduled script)

### Health Checks

Monitor backup health through the admin dashboard:

```bash
curl http://localhost:5000/api/backup/statistics
```

### Alert Integration

Set up alerts for backup failures:

```bash
# Check last backup status and send alert if failed
#!/bin/bash
LAST_BACKUP=$(curl -s http://localhost:5000/api/backup/list | jq -r '.backups[0].success')
if [ "$LAST_BACKUP" != "true" ]; then
    echo "Backup failed!" | mail -s "ATS Backup Alert" admin@example.com
fi
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure backup directory is writable
2. **pg_dump Not Found**: Install PostgreSQL client tools
3. **Connection Failed**: Verify database connection parameters
4. **Disk Space**: Monitor available disk space in backup directory

### Recovery Procedures

1. **Partial Backup Corruption**: Use previous backup or database replicas
2. **Full System Recovery**: Restore from most recent successful backup
3. **Point-in-Time Recovery**: For PostgreSQL, consider WAL archiving

### Log Analysis

```bash
# Check backup logs
tail -f backup.log

# Filter for errors
grep ERROR backup.log

# Check backup file integrity
gzip -t /path/to/backup.sql.gz
```

## API Reference

### Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/api/backup/create` | Create new backup | 3/hour |
| GET | `/api/backup/list` | List all backups | 20/min |
| POST | `/api/backup/restore/<name>` | Restore backup | 2/hour |
| DELETE | `/api/backup/delete/<name>` | Delete backup | 10/hour |
| GET | `/api/backup/statistics` | Backup statistics | 30/min |

### Response Formats

All endpoints return JSON with consistent structure:

```json
{
  "success": true,
  "backup_name": "example_backup",
  "file_path": "/backups/example_backup.sql.gz",
  "file_size": 1048576,
  "duration": 5.2,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

Error responses include:

```json
{
  "success": false,
  "error": "Backup creation failed: disk space insufficient",
  "backup_name": "example_backup",
  "timestamp": "2024-01-15T10:30:00Z"
}
```