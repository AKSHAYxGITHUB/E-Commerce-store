#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# backup.sh  –  Database + media backup to S3
# Schedule:  0 2 * * *  /opt/ecommerce-devsecops/scripts/backup.sh >> /var/log/ecommerce/backup.log 2>&1
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config (override via environment) ────────────────────────────────────────
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-ecommerce_db}"
DB_USER="${DB_USER:-ecomuser}"
DB_PASS="${DB_PASS:-ecompass}"
S3_BUCKET="${S3_BUCKET:-your-s3-bucket-name}"
AWS_REGION="${AWS_REGION:-ap-south-1}"
BACKUP_DIR="/tmp/ecommerce_backups"
RETENTION_DAYS=7
DATE=$(date +%Y%m%d_%H%M%S)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# ── Create local backup directory ────────────────────────────────────────────
mkdir -p "${BACKUP_DIR}"
log "Starting backup: ${DATE}"

# ── Database dump ─────────────────────────────────────────────────────────────
DB_FILE="${BACKUP_DIR}/db_backup_${DATE}.sql.gz"
log "Dumping database ${DB_NAME}…"
mysqldump \
    -h "${DB_HOST}" \
    -P "${DB_PORT}" \
    -u "${DB_USER}" \
    -p"${DB_PASS}" \
    --single-transaction \
    --routines \
    --triggers \
    "${DB_NAME}" | gzip > "${DB_FILE}"

log "DB dump size: $(du -sh "${DB_FILE}" | cut -f1)"

# ── Upload DB backup to S3 ────────────────────────────────────────────────────
log "Uploading DB backup to S3…"
aws s3 cp "${DB_FILE}" \
    "s3://${S3_BUCKET}/backups/db/$(basename "${DB_FILE}")" \
    --region "${AWS_REGION}" \
    --storage-class STANDARD_IA
log "DB backup uploaded: s3://${S3_BUCKET}/backups/db/$(basename "${DB_FILE}")"

# ── Clean up local DB dump ────────────────────────────────────────────────────
rm -f "${DB_FILE}"

# ── Remove old backups from S3 (older than RETENTION_DAYS) ───────────────────
log "Removing S3 backups older than ${RETENTION_DAYS} days…"
CUTOFF=$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%dT%H:%M:%SZ)
aws s3api list-objects-v2 \
    --bucket "${S3_BUCKET}" \
    --prefix "backups/db/" \
    --query "Contents[?LastModified<='${CUTOFF}'].Key" \
    --output text | tr '\t' '\n' | while read -r key; do
    [ -z "${key}" ] && continue
    aws s3 rm "s3://${S3_BUCKET}/${key}" --region "${AWS_REGION}"
    log "Deleted old backup: ${key}"
done

log "Backup completed successfully."
