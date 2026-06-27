#!/bin/bash
# ============================================
# MySQL 数据库导出脚本
# 用法: bash backup_db.sh
# 输出: mysql_data/muxue_YYYYMMDD_HHMMSS.sql
# ============================================

set -e

# 配置
DB_NAME="muxue"
DB_USER="muxueuser"
DB_PASS="q122764837"
DB_HOST="localhost"
DB_PORT="3306"

BACKUP_DIR="mysql_data"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/muxue_${TIMESTAMP}.sql"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 导出数据库
echo "正在导出数据库 ${DB_NAME} ..."
mysqldump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --user="${DB_USER}" \
    --password="${DB_PASS}" \
    --single-transaction \
    --routines \
    --triggers \
    --default-character-set=utf8mb4 \
    "${DB_NAME}" > "${BACKUP_FILE}"

# 压缩
gzip "${BACKUP_FILE}"
echo "导出完成: ${BACKUP_FILE}.gz"

# 只保留最近 10 份备份
echo "清理旧备份（保留最近 10 份）..."
ls -t "${BACKUP_DIR}"/muxue_*.sql.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
echo "清理完成"
