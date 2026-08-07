# Health Route Module
# This module provides health check endpoints for monitoring the API status
from fastapi import APIRouter
from datetime import datetime
import logging
import os
from utils.pgsql_service import get_pg_connection, get_pg_cursor

logger = logging.getLogger(__name__)

# Create a router instance for health endpoints
router = APIRouter()

# Health check endpoint that returns the status of the API
@router.get("/health")
async def health_check():
    """Liveness check, retained for load balancers."""
    return {
        "status": "healthy",
        "service": "Financial Data API",
        "timestamp": datetime.now().isoformat()
    }


def _database_status(label: str, database: str, table: str, date_column: str):
    """Run a bounded, read-only probe without ever returning credentials."""
    if not database:
        return {"status": "not_configured", "table": table}
    try:
        conn = get_pg_connection(database)
        if not conn:
            return {"status": "unavailable", "table": table}
        try:
            cursor = get_pg_cursor(conn)
            try:
                cursor.execute(f"SELECT COUNT(*) AS row_count, MAX({date_column}) AS latest_record FROM {table}")
                row = cursor.fetchone()
                return {
                    "status": "connected",
                    "table": table,
                    "row_count": int(row["row_count"]),
                    "latest_record": row["latest_record"].isoformat() if row["latest_record"] else None,
                }
            finally:
                cursor.close()
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("%s database health check failed: %s", label, exc)
        return {"status": "unavailable", "table": table, "detail": "Connection or table probe failed"}


@router.get("/health/regulatory-databases")
async def regulatory_database_health():
    """Report BSE, SEBI and RBI PostgreSQL reachability and data freshness.

    This endpoint is intentionally read-only and does not disclose hosts, users,
    connection strings, or database error details.
    """
    databases = {
        "bse": _database_status("BSE", os.getenv("POSTGRES_DATABASE_BSE"), "daily_logs", "record_date"),
        "sebi": _database_status("SEBI", os.getenv("POSTGRES_DATABASE_SEBI"), "aegis_sebi_data", "inserted_at"),
        "rbi": _database_status("RBI", os.getenv("POSTGRES_DATABASE_RBI"), "master_summaries", "run_date"),
    }
    healthy = all(value["status"] == "connected" for value in databases.values())
    return {
        "status": "healthy" if healthy else "degraded",
        "databases": databases,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }
