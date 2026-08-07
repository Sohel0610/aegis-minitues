"""
MS Teams Integration — Route Module
REST API endpoints for Teams meeting management, transcript retrieval,
MOM generation, and AI transcript analysis.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import logging
import asyncio
import concurrent.futures
import uuid
from datetime import datetime

from utils.pgsql_service import get_pg_connection, get_pg_cursor
from utils.auth_dep import require_session

logger = logging.getLogger(__name__)

# Thread pool for blocking DB / LLM operations
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)

router = APIRouter(tags=["MS Teams"])

# ─────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────

class CreateMeetingRequest(BaseModel):
    meeting_url: str
    title: Optional[str] = None
    company_id: Optional[int] = None
    scheduled_at: Optional[str] = None


class MeetingResponse(BaseModel):
    id: str
    meeting_url: str
    title: Optional[str] = None
    call_id: Optional[str] = None
    status: str
    company_id: Optional[int] = None
    scheduled_at: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    created_at: str


class MeetingListResponse(BaseModel):
    data: List[MeetingResponse]
    count: int


class TranscriptResponse(BaseModel):
    id: Optional[str] = None
    meeting_id: str
    raw_vtt: Optional[str] = None
    structured_json: Optional[Any] = None
    full_text: Optional[str] = None
    participants: Optional[List[str]] = None
    participant_count: int = 0
    duration_minutes: int = 0
    created_at: Optional[str] = None


class MOMResponse(BaseModel):
    id: Optional[str] = None
    meeting_id: str
    mom_json: Optional[Any] = None
    mom_html: Optional[str] = None
    version: int = 1
    generated_at: Optional[str] = None


class InsightResponse(BaseModel):
    id: Optional[str] = None
    meeting_id: str
    insight_type: str
    insight_json: Optional[Any] = None
    generated_at: Optional[str] = None


class InsightsListResponse(BaseModel):
    data: List[InsightResponse]
    count: int


class UploadTranscriptRequest(BaseModel):
    vtt_content: str


# ─────────────────────────────────────────────
# Dynamic Database Selector (SSO_ENABLED toggle)
# ─────────────────────────────────────────────

import sqlite3

def is_sso_enabled() -> bool:
    return os.getenv('SSO_ENABLED', 'false').lower() == 'true'

def _get_teams_db():
    return os.getenv('POSTGRES_DATABASE_TEAMS', 'postgres')

def get_teams_db_conn():
    """
    Returns (conn, is_sqlite).
    If SSO_ENABLED=true -> PostgreSQL connection.
    If SSO_ENABLED=false -> SQLite connection to ./data/local.db.
    """
    if is_sso_enabled():
        target_db = _get_teams_db()
        conn = get_pg_connection(target_db)
        if conn:
            return conn, False
        logger.warning(f"PostgreSQL connection failed ({target_db}), falling back to SQLite local.db")

    # SQLite mode for UAT / Local guest usage
    db_dir = os.path.join(os.getcwd(), 'data')
    os.makedirs(db_dir, exist_ok=True)
    sqlite_path = os.path.join(db_dir, 'local.db')
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    return conn, True


def db_fetch_all(query: str, params: tuple = ()):
    conn, is_sqlite = get_teams_db_conn()
    if not conn:
        raise RuntimeError("Database connection unavailable")
    try:
        if is_sqlite:
            cursor = conn.cursor()
            q = query.replace("%s", "?")
            cursor.execute(q, params)
            return [dict(r) for r in cursor.fetchall()]
        else:
            cursor = get_pg_cursor(conn)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()


def db_fetch_one(query: str, params: tuple = ()):
    conn, is_sqlite = get_teams_db_conn()
    if not conn:
        raise RuntimeError("Database connection unavailable")
    try:
        if is_sqlite:
            cursor = conn.cursor()
            q = query.replace("%s", "?")
            cursor.execute(q, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        else:
            cursor = get_pg_cursor(conn)
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def db_execute(query: str, params: tuple = ()):
    conn, is_sqlite = get_teams_db_conn()
    if not conn:
        raise RuntimeError("Database connection unavailable")
    try:
        if is_sqlite:
            cursor = conn.cursor()
            q = query.replace("%s", "?")
            cursor.execute(q, params)
            conn.commit()
            return cursor.rowcount
        else:
            cursor = get_pg_cursor(conn)
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()


def init_teams_pg():
    """Initialize MS Teams tables in PostgreSQL or SQLite based on SSO_ENABLED."""
    conn, is_sqlite = get_teams_db_conn()
    if not conn:
        logger.warning("Could not obtain database connection for Teams init.")
        return

    try:
        if is_sqlite:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams_meetings (
                    id TEXT PRIMARY KEY,
                    meeting_url TEXT NOT NULL,
                    title TEXT,
                    call_id TEXT,
                    status TEXT DEFAULT 'pending',
                    company_id INTEGER,
                    scheduled_at TEXT,
                    started_at TEXT,
                    ended_at TEXT,
                    created_by TEXT DEFAULT 'guest@adani.local',
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_transcripts (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT,
                    raw_vtt TEXT,
                    structured_json TEXT,
                    full_text TEXT,
                    participants TEXT,
                    participant_count INTEGER DEFAULT 0,
                    duration_minutes INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(meeting_id) REFERENCES teams_meetings(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_moms (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT,
                    transcript_id TEXT,
                    mom_json TEXT,
                    mom_html TEXT,
                    version INTEGER DEFAULT 1,
                    generated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(meeting_id) REFERENCES teams_meetings(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_insights (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT,
                    transcript_id TEXT,
                    insight_type TEXT,
                    insight_json TEXT,
                    generated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(meeting_id) REFERENCES teams_meetings(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_status ON teams_meetings(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_created ON teams_meetings(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_meeting ON meeting_transcripts(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_moms_meeting ON meeting_moms(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_meeting ON meeting_insights(meeting_id)")
            conn.commit()
            logger.info("MS Teams tables initialized in SQLite (./data/local.db)")
        else:
            cursor = get_pg_cursor(conn)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teams_meetings (
                    id TEXT PRIMARY KEY,
                    meeting_url TEXT NOT NULL,
                    title TEXT,
                    call_id TEXT,
                    status TEXT DEFAULT 'pending',
                    company_id INTEGER,
                    scheduled_at TIMESTAMP,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    created_by TEXT DEFAULT 'guest@adani.local',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_transcripts (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT REFERENCES teams_meetings(id) ON DELETE CASCADE,
                    raw_vtt TEXT,
                    structured_json JSONB,
                    full_text TEXT,
                    participants JSONB,
                    participant_count INTEGER DEFAULT 0,
                    duration_minutes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_moms (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT REFERENCES teams_meetings(id) ON DELETE CASCADE,
                    transcript_id TEXT,
                    mom_json JSONB,
                    mom_html TEXT,
                    version INTEGER DEFAULT 1,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meeting_insights (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT REFERENCES teams_meetings(id) ON DELETE CASCADE,
                    transcript_id TEXT,
                    insight_type TEXT,
                    insight_json JSONB,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_status ON teams_meetings(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_created ON teams_meetings(created_at DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transcripts_meeting ON meeting_transcripts(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_moms_meeting ON meeting_moms(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_meeting ON meeting_insights(meeting_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_type ON meeting_insights(insight_type)")
            conn.commit()
            logger.info(f"MS Teams tables initialized in PostgreSQL ({_get_teams_db()})")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to initialize Teams tables: {e}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# API Endpoints — Meetings CRUD
# ─────────────────────────────────────────────

@router.post("/teams/meetings", response_model=MeetingResponse)
async def create_meeting(request: CreateMeetingRequest):
    """Create a new meeting record by pasting a Teams meeting link."""
    try:
        meeting_id = str(uuid.uuid4())

        def insert():
            conn, is_sqlite = get_teams_db_conn()
            if not conn:
                raise RuntimeError("Teams database connection unavailable")
            try:
                if is_sqlite:
                    cursor = conn.cursor()
                    created_by = "guest@adani.local"
                    now_str = datetime.now().isoformat()
                    cursor.execute(
                        """INSERT INTO teams_meetings (id, meeting_url, title, status, company_id, scheduled_at, created_by, created_at)
                           VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)""",
                        (meeting_id, request.meeting_url, request.title,
                         request.company_id, request.scheduled_at, created_by, now_str)
                    )
                    conn.commit()
                    return {
                        "id": meeting_id,
                        "meeting_url": request.meeting_url,
                        "title": request.title,
                        "call_id": None,
                        "status": "pending",
                        "company_id": request.company_id,
                        "scheduled_at": request.scheduled_at,
                        "started_at": None,
                        "ended_at": None,
                        "created_at": now_str,
                    }
                else:
                    cursor = get_pg_cursor(conn)
                    cursor.execute(
                        """INSERT INTO teams_meetings (id, meeting_url, title, status, company_id, scheduled_at)
                           VALUES (%s, %s, %s, 'pending', %s, %s)
                           RETURNING id, meeting_url, title, call_id, status, company_id,
                                     scheduled_at, started_at, ended_at, created_at""",
                        (meeting_id, request.meeting_url, request.title,
                         request.company_id, request.scheduled_at)
                    )
                    row = cursor.fetchone()
                    conn.commit()
                    return dict(row)
            finally:
                conn.close()

        row = await asyncio.get_running_loop().run_in_executor(thread_pool, insert)
        return MeetingResponse(
            id=row['id'],
            meeting_url=row['meeting_url'],
            title=row['title'],
            call_id=row['call_id'],
            status=row['status'],
            company_id=row['company_id'],
            scheduled_at=str(row['scheduled_at']) if row['scheduled_at'] else None,
            started_at=str(row['started_at']) if row['started_at'] else None,
            ended_at=str(row['ended_at']) if row['ended_at'] else None,
            created_at=str(row['created_at']),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/meetings", response_model=MeetingListResponse)
async def list_meetings():
    """List all meetings ordered by creation date."""
    try:
        def fetch():
            return db_fetch_all(
                """SELECT id, meeting_url, title, call_id, status, company_id,
                          scheduled_at, started_at, ended_at, created_at
                   FROM teams_meetings ORDER BY created_at DESC"""
            )

        rows = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        data = [
            MeetingResponse(
                id=r['id'],
                meeting_url=r['meeting_url'],
                title=r['title'],
                call_id=r['call_id'],
                status=r['status'],
                company_id=r['company_id'],
                scheduled_at=str(r['scheduled_at']) if r['scheduled_at'] else None,
                started_at=str(r['started_at']) if r['started_at'] else None,
                ended_at=str(r['ended_at']) if r['ended_at'] else None,
                created_at=str(r['created_at']),
            )
            for r in rows
        ]
        return MeetingListResponse(data=data, count=len(data))
    except Exception as e:
        logger.error(f"Error listing meetings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/meetings/{meeting_id}")
async def get_meeting(meeting_id: str):
    """Get a single meeting with its transcript, MOM, and insights summary."""
    try:
        def fetch():
            meeting = db_fetch_one("SELECT * FROM teams_meetings WHERE id = %s", (meeting_id,))
            if not meeting:
                return None

            transcript = db_fetch_one(
                "SELECT id, participant_count, duration_minutes, created_at FROM meeting_transcripts WHERE meeting_id = %s ORDER BY created_at DESC LIMIT 1",
                (meeting_id,)
            )
            mom = db_fetch_one(
                "SELECT id, version, generated_at FROM meeting_moms WHERE meeting_id = %s ORDER BY generated_at DESC LIMIT 1",
                (meeting_id,)
            )
            insights = db_fetch_all(
                "SELECT id FROM meeting_insights WHERE meeting_id = %s", (meeting_id,)
            )

            return {
                "meeting": meeting,
                "has_transcript": transcript is not None,
                "transcript_summary": transcript,
                "has_mom": mom is not None,
                "mom_summary": mom,
                "insight_count": len(insights),
            }

        result = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        if not result:
            raise HTTPException(status_code=404, detail="Meeting not found")

        for key, val in result.get("meeting", {}).items():
            if isinstance(val, datetime):
                result["meeting"][key] = val.isoformat()
        if result.get("transcript_summary"):
            for k, v in result["transcript_summary"].items():
                if isinstance(v, datetime):
                    result["transcript_summary"][k] = v.isoformat()
        if result.get("mom_summary"):
            for k, v in result["mom_summary"].items():
                if isinstance(v, datetime):
                    result["mom_summary"][k] = v.isoformat()

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teams/meetings/{meeting_id}")
async def delete_meeting(meeting_id: str):
    """Delete a meeting and all associated data (cascades)."""
    try:
        def delete():
            count = db_execute("DELETE FROM teams_meetings WHERE id = %s", (meeting_id,))
            return count > 0

        deleted = await asyncio.get_running_loop().run_in_executor(thread_pool, delete)
        return {"success": deleted, "deleted_id": meeting_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# API Endpoints — Bot Join / Leave
# ─────────────────────────────────────────────

@router.post("/teams/meetings/{meeting_id}/join")
async def join_meeting(meeting_id: str):
    """Bot joins the meeting via Graph API."""
    try:
        def get_url():
            return db_fetch_one("SELECT meeting_url, status FROM teams_meetings WHERE id = %s", (meeting_id,))

        meeting = await asyncio.get_running_loop().run_in_executor(thread_pool, get_url)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        from services.teams_bot_service import TeamsBotService
        bot = TeamsBotService()
        result = await bot.join_meeting(meeting['meeting_url'], meeting_id)

        if result.get("success"):
            def update_status():
                now_str = datetime.now().isoformat()
                db_execute(
                    """UPDATE teams_meetings SET status = 'active', call_id = %s, started_at = %s
                       WHERE id = %s""",
                    (result.get("call_id", ""), now_str, meeting_id)
                )
            await asyncio.get_running_loop().run_in_executor(thread_pool, update_status)

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining meeting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/meetings/{meeting_id}/leave")
async def leave_meeting(meeting_id: str):
    """Bot leaves the meeting."""
    try:
        def get_call_id():
            row = db_fetch_one("SELECT call_id FROM teams_meetings WHERE id = %s", (meeting_id,))
            return row['call_id'] if row else None

        call_id = await asyncio.get_running_loop().run_in_executor(thread_pool, get_call_id)
        if not call_id:
            raise HTTPException(status_code=404, detail="No active call found for this meeting")

        from services.teams_bot_service import TeamsBotService
        bot = TeamsBotService()
        result = await bot.leave_meeting(call_id)

        if result.get("success"):
            def update_status():
                now_str = datetime.now().isoformat()
                db_execute(
                    "UPDATE teams_meetings SET status = 'completed', ended_at = %s WHERE id = %s",
                    (now_str, meeting_id)
                )
            await asyncio.get_running_loop().run_in_executor(thread_pool, update_status)

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# API Endpoints — Transcript
# ─────────────────────────────────────────────

@router.post("/teams/meetings/{meeting_id}/fetch-transcript")
async def fetch_transcript(meeting_id: str):
    """Fetch transcript from Graph API for a completed meeting."""
    try:
        def get_meeting():
            return db_fetch_one("SELECT meeting_url FROM teams_meetings WHERE id = %s", (meeting_id,))

        meeting = await asyncio.get_running_loop().run_in_executor(thread_pool, get_meeting)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        from services.teams_transcript_service import TeamsTranscriptService
        svc = TeamsTranscriptService()
        result = await svc.fetch_transcript(meeting['meeting_url'])

        if result.get("success"):
            def store():
                tid = str(uuid.uuid4())
                now_str = datetime.now().isoformat()
                db_execute(
                    """INSERT INTO meeting_transcripts (id, meeting_id, raw_vtt, structured_json, full_text, participants, participant_count, duration_minutes, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (tid, meeting_id, result['raw_vtt'],
                     json.dumps(result['structured_json']),
                     result.get('full_text', ''),
                     json.dumps(result.get('participants', [])),
                     result.get('participant_count', 0),
                     result.get('duration_minutes', 0),
                     now_str)
                )
                db_execute(
                    "UPDATE teams_meetings SET status = 'transcript_ready' WHERE id = %s AND status != 'completed'",
                    (meeting_id,)
                )
                return {"id": tid, "created_at": now_str}

            stored = await asyncio.get_running_loop().run_in_executor(thread_pool, store)
            result['transcript_db_id'] = stored['id'] if stored else None

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/meetings/{meeting_id}/upload-transcript")
async def upload_transcript(meeting_id: str, request: UploadTranscriptRequest):
    """Upload a VTT transcript manually (for testing without Graph API)."""
    try:
        from services.teams_transcript_service import TeamsTranscriptService
        svc = TeamsTranscriptService()
        result = svc.parse_uploaded_vtt(request.vtt_content)

        if result.get("success"):
            def store():
                tid = str(uuid.uuid4())
                now_str = datetime.now().isoformat()
                db_execute(
                    """INSERT INTO meeting_transcripts (id, meeting_id, raw_vtt, structured_json, full_text, participants, participant_count, duration_minutes, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (tid, meeting_id, result['raw_vtt'],
                     json.dumps(result['structured_json']),
                     result.get('full_text', ''),
                     json.dumps(result.get('participants', [])),
                     result.get('participant_count', 0),
                     result.get('duration_minutes', 0),
                     now_str)
                )
                db_execute(
                    "UPDATE teams_meetings SET status = 'transcript_ready' WHERE id = %s",
                    (meeting_id,)
                )
                return {"id": tid, "created_at": now_str}

            stored = await asyncio.get_running_loop().run_in_executor(thread_pool, store)
            result['transcript_db_id'] = stored['id'] if stored else None

        return result
    except Exception as e:
        logger.error(f"Error uploading transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/meetings/{meeting_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(meeting_id: str):
    """Get the stored transcript for a meeting."""
    try:
        def fetch():
            return db_fetch_one(
                """SELECT id, meeting_id, raw_vtt, structured_json, full_text, participants,
                          participant_count, duration_minutes, created_at
                   FROM meeting_transcripts WHERE meeting_id = %s
                   ORDER BY created_at DESC LIMIT 1""",
                (meeting_id,)
            )

        row = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        if not row:
            raise HTTPException(status_code=404, detail="No transcript found for this meeting")

        structured = row['structured_json']
        if isinstance(structured, str):
            try: structured = json.loads(structured)
            except Exception: pass

        participants = row['participants']
        if isinstance(participants, str):
            try: participants = json.loads(participants)
            except Exception: participants = []

        return TranscriptResponse(
            id=row['id'],
            meeting_id=row['meeting_id'],
            raw_vtt=row['raw_vtt'],
            structured_json=structured,
            full_text=row['full_text'],
            participants=participants,
            participant_count=row['participant_count'],
            duration_minutes=row['duration_minutes'],
            created_at=str(row['created_at']),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# API Endpoints — MOM Generation
# ─────────────────────────────────────────────

@router.post("/teams/meetings/{meeting_id}/generate-mom")
async def generate_mom(meeting_id: str):
    """Generate AI MOM from the stored transcript."""
    try:
        def get_transcript_data():
            transcript = db_fetch_one(
                "SELECT id, full_text, participants FROM meeting_transcripts WHERE meeting_id = %s ORDER BY created_at DESC LIMIT 1",
                (meeting_id,)
            )
            meeting = db_fetch_one(
                "SELECT title, scheduled_at FROM teams_meetings WHERE id = %s",
                (meeting_id,)
            )
            return transcript, meeting

        transcript, meeting = await asyncio.get_running_loop().run_in_executor(thread_pool, get_transcript_data)
        if not transcript:
            raise HTTPException(status_code=404, detail="No transcript found. Fetch or upload a transcript first.")

        from services.mom_generator_service import MOMGeneratorService
        svc = MOMGeneratorService()

        participants = transcript['participants']
        if isinstance(participants, str):
            try: participants = json.loads(participants)
            except Exception: participants = []

        def run_generation():
            return svc.generate_mom(
                transcript_text=transcript['full_text'],
                meeting_title=meeting['title'] if meeting else None,
                meeting_date=str(meeting['scheduled_at']) if meeting and meeting['scheduled_at'] else None,
                participants=participants,
            )

        result = await asyncio.get_running_loop().run_in_executor(thread_pool, run_generation)

        if result.get("success"):
            mom_data = result.get("mom", {})
            mom_html = svc.generate_mom_html(mom_data)

            def store_mom():
                mom_id = str(uuid.uuid4())
                now_str = datetime.now().isoformat()
                db_execute(
                    """INSERT INTO meeting_moms (id, meeting_id, transcript_id, mom_json, mom_html, version, generated_at)
                       VALUES (%s, %s, %s, %s, %s, 1, %s)""",
                    (mom_id, meeting_id, transcript['id'],
                     json.dumps(mom_data), mom_html, now_str)
                )
                db_execute(
                    "UPDATE teams_meetings SET status = 'mom_ready' WHERE id = %s",
                    (meeting_id,)
                )
                return {"id": mom_id, "generated_at": now_str}

            stored = await asyncio.get_running_loop().run_in_executor(thread_pool, store_mom)
            result['mom_db_id'] = stored['id'] if stored else None
            result['mom_html'] = mom_html

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating MOM: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/meetings/{meeting_id}/mom", response_model=MOMResponse)
async def get_mom(meeting_id: str):
    """Get the generated MOM for a meeting."""
    try:
        def fetch():
            return db_fetch_one(
                """SELECT id, meeting_id, mom_json, mom_html, version, generated_at
                   FROM meeting_moms WHERE meeting_id = %s
                   ORDER BY generated_at DESC LIMIT 1""",
                (meeting_id,)
            )

        row = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        if not row:
            raise HTTPException(status_code=404, detail="No MOM found. Generate one first.")

        mom_json = row['mom_json']
        if isinstance(mom_json, str):
            try: mom_json = json.loads(mom_json)
            except Exception: pass

        return MOMResponse(
            id=row['id'],
            meeting_id=row['meeting_id'],
            mom_json=mom_json,
            mom_html=row['mom_html'],
            version=row['version'],
            generated_at=str(row['generated_at']),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# API Endpoints — AI Analysis
# ─────────────────────────────────────────────

@router.post("/teams/meetings/{meeting_id}/analyze")
async def analyze_transcript(meeting_id: str):
    """Run AI analysis on the meeting transcript."""
    try:
        def get_data():
            return db_fetch_one(
                "SELECT id, full_text, structured_json FROM meeting_transcripts WHERE meeting_id = %s ORDER BY created_at DESC LIMIT 1",
                (meeting_id,)
            )

        transcript = await asyncio.get_running_loop().run_in_executor(thread_pool, get_data)
        if not transcript:
            raise HTTPException(status_code=404, detail="No transcript found. Fetch or upload one first.")

        from services.transcript_analysis_service import TranscriptAnalysisService
        svc = TranscriptAnalysisService()

        segments = transcript['structured_json']
        if isinstance(segments, str):
            try: segments = json.loads(segments)
            except Exception: segments = []

        def run_analysis():
            return svc.run_all_analyses(
                transcript_text=transcript['full_text'],
                structured_segments=segments,
            )

        result = await asyncio.get_running_loop().run_in_executor(thread_pool, run_analysis)

        if result.get("success"):
            def store_insights():
                db_execute("DELETE FROM meeting_insights WHERE meeting_id = %s", (meeting_id,))
                now_str = datetime.now().isoformat()

                for insight_type, insight_data in result.get("insights", {}).items():
                    insight_id = str(uuid.uuid4())
                    db_execute(
                        """INSERT INTO meeting_insights (id, meeting_id, transcript_id, insight_type, insight_json, generated_at)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (insight_id, meeting_id, transcript['id'],
                         insight_type, json.dumps(insight_data), now_str)
                    )

                db_execute(
                    "UPDATE teams_meetings SET status = 'analyzed' WHERE id = %s",
                    (meeting_id,)
                )

            await asyncio.get_running_loop().run_in_executor(thread_pool, store_insights)

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/meetings/{meeting_id}/insights", response_model=InsightsListResponse)
async def get_insights(meeting_id: str):
    """Get all AI insights for a meeting."""
    try:
        def fetch():
            return db_fetch_all(
                """SELECT id, meeting_id, insight_type, insight_json, generated_at
                   FROM meeting_insights WHERE meeting_id = %s
                   ORDER BY generated_at""",
                (meeting_id,)
            )

        rows = await asyncio.get_running_loop().run_in_executor(thread_pool, fetch)
        data = []
        for r in rows:
            ij = r['insight_json']
            if isinstance(ij, str):
                try: ij = json.loads(ij)
                except Exception: pass
            data.append(
                InsightResponse(
                    id=r['id'],
                    meeting_id=r['meeting_id'],
                    insight_type=r['insight_type'],
                    insight_json=ij,
                    generated_at=str(r['generated_at']),
                )
            )
        return InsightsListResponse(data=data, count=len(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
