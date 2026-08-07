#!/usr/bin/env python3
"""
Generate and optionally run chatbot evaluation questions from sqlite.db.

The question set is designed for the current pre-RAG chatbot stage. It focuses
on structured database behavior: source routing, counts, dates, entities,
latest records, known notification summaries, charts, tables, and long
persona-style questions for management/business users.

Examples:
    python Backend/scripts/generate_chatbot_eval_questions.py
    python Backend/scripts/generate_chatbot_eval_questions.py --run
    python Backend/scripts/generate_chatbot_eval_questions.py --run --api-url http://127.0.0.1:8000/api/chat/message

Outputs are written to ./chatbot_eval_output by default:
    chatbot_eval_questions.csv
    chatbot_eval_questions.json
    chatbot_eval_answers.csv              only with --run
    chatbot_eval_report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "sqlite.db"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "chatbot_eval_output"
DEFAULT_API_URL = "http://127.0.0.1:8000/api/chat/message"
NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))

BASE_PER_SOURCE = 200
PERSONA_PER_SOURCE = 100
TOTAL_PER_SOURCE = BASE_PER_SOURCE + PERSONA_PER_SOURCE
TOTAL_QUESTIONS = TOTAL_PER_SOURCE * 3
STOPWORDS = {
    "about",
    "above",
    "after",
    "against",
    "also",
    "amendment",
    "amendments",
    "bank",
    "banking",
    "banks",
    "been",
    "being",
    "between",
    "company",
    "dated",
    "directions",
    "from",
    "have",
    "including",
    "india",
    "into",
    "issued",
    "letter",
    "limited",
    "notification",
    "please",
    "regarding",
    "report",
    "reserve",
    "shall",
    "should",
    "summary",
    "there",
    "under",
    "update",
    "updated",
    "with",
    "would",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=f"Create {TOTAL_QUESTIONS} SQLite-grounded chatbot questions and optionally run them against the API."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help=f"SQLite DB path. Default: {DEFAULT_DB}")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output folder. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Call the chatbot API for every generated question and save answers.",
    )
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help=f"Chat API URL. Default: {DEFAULT_API_URL}")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout per question in seconds.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional delay between API calls.")
    parser.add_argument("--limit", type=int, default=10, help="Chatbot request limit value.")
    parser.add_argument(
        "--allow-http-errors",
        action="store_true",
        help="Continue writing answers even when the API returns non-200 responses.",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip the initial hello request used to confirm the chatbot API URL is correct.",
    )
    return parser.parse_args()


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_all(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> Any:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return None
    return row[0]


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def keyword_from_text(text: str, fallback: str = "notification") -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9&-]{3,}", normalize_text(text))
    for word in words:
        cleaned = word.strip("-").lower()
        if cleaned and cleaned not in STOPWORDS:
            return word.strip("-")
    return fallback


def month_label(date_key: str) -> str:
    parsed = parse_date_value(date_key)
    if parsed:
        return parsed.strftime("%B %Y")

    date_key = normalize_text(date_key)
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_key[:10], fmt).strftime("%B %Y")
        except ValueError:
            pass
    if len(date_key) >= 7:
        return date_key[:7]
    return date_key


def parse_date_value(date_key: Any) -> date | None:
    text = normalize_text(date_key)
    if not text:
        return None

    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            pass
    return None


def month_key_for(date_key: Any) -> str:
    parsed = parse_date_value(date_key)
    if parsed:
        return parsed.strftime("%Y-%m")

    text = normalize_text(date_key)
    if len(text) >= 7:
        return text[:7]
    return text or "unknown"


def add_question(
    questions: list[dict[str, Any]],
    source: str,
    category: str,
    question: str,
    database: str,
    expected_answer: str,
    expected_keywords: list[str],
    evidence: str,
) -> None:
    questions.append(
        {
            "id": f"{source}-{len([q for q in questions if q['source'] == source]) + 1:03d}",
            "source": source,
            "database": database,
            "category": category,
            "question": normalize_text(question),
            "expected_answer": normalize_text(expected_answer),
            "expected_keywords": "|".join(str(k) for k in expected_keywords if k),
            "evidence": normalize_text(evidence),
        }
    )


def trim_source_questions(questions: list[dict[str, Any]], source: str) -> None:
    source_questions = [q for q in questions if q["source"] == source]
    if len(source_questions) < TOTAL_PER_SOURCE:
        raise RuntimeError(f"Could only generate {len(source_questions)} {source} questions")

    keep_ids = {q["id"] for q in source_questions[:TOTAL_PER_SOURCE]}
    questions[:] = [q for q in questions if q["source"] != source or q["id"] in keep_ids]


def make_candidate(
    source: str,
    category: str,
    question: str,
    database: str,
    expected_answer: str,
    expected_keywords: list[Any],
    evidence: str,
) -> dict[str, Any]:
    return {
        "source": source,
        "category": category,
        "question": question,
        "database": database,
        "expected_answer": expected_answer,
        "expected_keywords": expected_keywords,
        "evidence": evidence,
    }


def add_interleaved_candidates(
    questions: list[dict[str, Any]],
    source: str,
    buckets: list[list[dict[str, Any]]],
    target_count: int = BASE_PER_SOURCE,
) -> None:
    added = 0
    seen_questions: set[str] = set()

    while added < target_count and any(buckets):
        for bucket in buckets:
            if added >= target_count:
                break
            if not bucket:
                continue

            candidate = bucket.pop(0)
            normalized_question = normalize_text(candidate["question"]).lower()
            if normalized_question in seen_questions:
                source_id_match = re.search(r"\bid=([^ ]+)", candidate["evidence"])
                if source_id_match and source_id_match.group(1).lower() != "none":
                    candidate["question"] = f"{candidate['question']} Focus on source id {source_id_match.group(1)}."
                else:
                    duplicate_variants = [
                        "Return it as a concise bullet list.",
                        "Include a manager-friendly takeaway.",
                        "Include source evidence if available.",
                        "Separate the date, topic, and summary.",
                        "Explain why it matters for compliance monitoring.",
                    ]
                    candidate["question"] = f"{candidate['question']} {duplicate_variants[added % len(duplicate_variants)]}"
                normalized_question = normalize_text(candidate["question"]).lower()
                if normalized_question in seen_questions:
                    continue

            seen_questions.add(normalized_question)
            add_question(
                questions,
                source,
                candidate["category"],
                candidate["question"],
                candidate["database"],
                candidate["expected_answer"],
                candidate["expected_keywords"],
                candidate["evidence"],
            )
            added += 1

    if added < target_count:
        raise RuntimeError(f"Could only generate {added} varied {source} questions")


def rows_by_month(rows: list[sqlite3.Row], date_field: str) -> list[dict[str, Any]]:
    counter = Counter(month_key_for(row[date_field]) for row in rows if row[date_field])
    return [
        {"month_key": month_key, "count": counter[month_key]}
        for month_key in sorted(counter.keys(), reverse=True)
    ]


def generate_bse_questions(conn: sqlite3.Connection, questions: list[dict[str, Any]]) -> None:
    entity_counts = fetch_all(
        conn,
        """
        SELECT entity_name, COUNT(*) AS count
        FROM bse_daily_logs
        WHERE entity_name IS NOT NULL AND TRIM(entity_name) != ''
        GROUP BY entity_name
        ORDER BY count DESC, entity_name
        LIMIT 100
        """,
    )
    monthly_counts = fetch_all(
        conn,
        """
        SELECT SUBSTR(record_date, 1, 7) AS month_key, COUNT(*) AS count
        FROM bse_daily_logs
        WHERE record_date IS NOT NULL
        GROUP BY month_key
        ORDER BY month_key DESC
        LIMIT 36
        """,
    )
    nature_counts = fetch_all(
        conn,
        """
        SELECT nature, COUNT(*) AS count
        FROM bse_daily_logs
        WHERE nature IS NOT NULL AND TRIM(nature) != ''
        GROUP BY nature
        ORDER BY count DESC, nature
        LIMIT 80
        """,
    )
    sample_rows = fetch_all(
        conn,
        """
        SELECT id, sr_no, entity_name, nature, summary, record_date, link
        FROM bse_daily_logs
        WHERE entity_name IS NOT NULL
          AND TRIM(entity_name) != ''
          AND summary IS NOT NULL
          AND TRIM(summary) != ''
        ORDER BY record_date DESC, id ASC
        LIMIT 300
        """,
    )

    buckets: list[list[dict[str, Any]]] = [[] for _ in range(12)]

    for row in entity_counts[:50]:
        buckets[0].append(make_candidate(
            "BSE",
            "Entity Count",
            f"How many BSE notifications are there for {row['entity_name']}?",
            "bse",
            f"{row['entity_name']} has {row['count']} BSE notifications in sqlite.db.",
            ["BSE", row["entity_name"], row["count"]],
            f"bse_daily_logs entity_name={row['entity_name']} count={row['count']}",
        ))

    for row in entity_counts[:35]:
        buckets[1].append(make_candidate(
            "BSE",
            "Table Request",
            f"Create a table of the latest BSE notifications for {row['entity_name']} with date, subject, and summary.",
            "bse",
            f"The answer should provide a table/list for {row['entity_name']} BSE notifications.",
            ["BSE", row["entity_name"], "Date"],
            f"table request for bse_daily_logs entity_name={row['entity_name']} count={row['count']}",
        ))

    for first, second in zip(entity_counts[0::2], entity_counts[1::2]):
        buckets[2].append(make_candidate(
            "BSE",
            "Bar Chart Comparison",
            f"Create a bar chart comparing BSE notification counts for {first['entity_name']} and {second['entity_name']}.",
            "bse",
            f"{first['entity_name']}: {first['count']}; {second['entity_name']}: {second['count']}.",
            [first["entity_name"], first["count"], second["entity_name"], second["count"]],
            f"BSE chart comparison {first['entity_name']}={first['count']} {second['entity_name']}={second['count']}",
        ))

    for row in monthly_counts[:24]:
        label = month_label(row["month_key"] + "-01")
        buckets[3].append(make_candidate(
            "BSE",
            "Trend Chart",
            f"Show a month-wise trend chart for BSE notifications around {label}.",
            "bse",
            f"The answer should support a BSE monthly trend and include {label} count {row['count']}.",
            ["BSE", row["count"], label],
            f"bse_daily_logs month={row['month_key']} count={row['count']}",
        ))

    for row in entity_counts[:30]:
        buckets[4].append(make_candidate(
            "BSE",
            "Top N Ranking",
            f"Which companies are among the top BSE notification contributors, and where does {row['entity_name']} fit?",
            "bse",
            f"{row['entity_name']} has {row['count']} BSE notifications and is part of the ranked entity list.",
            ["BSE", row["entity_name"], row["count"]],
            f"top ranking evidence entity_name={row['entity_name']} count={row['count']}",
        ))

    for row in sample_rows[:35]:
        buckets[5].append(make_candidate(
            "BSE",
            "Latest Update",
            f"What is the latest available BSE update for {row['entity_name']}?",
            "bse",
            f"The answer should include a BSE update for {row['entity_name']} near {row['record_date']}.",
            ["BSE", row["entity_name"], row["record_date"]],
            f"id={row['id']} date={row['record_date']} nature={row['nature']} summary={row['summary']}",
        ))

    for row in sample_rows[:35]:
        keyword = keyword_from_text(row["summary"], row["nature"] or "notification")
        buckets[6].append(make_candidate(
            "BSE",
            "Topic Search",
            f"Find BSE notifications for {row['entity_name']} related to {keyword}.",
            "bse",
            f"The answer should mention {row['entity_name']} and topic {keyword}.",
            ["BSE", row["entity_name"], row["record_date"], keyword],
            f"id={row['id']} date={row['record_date']} nature={row['nature']} summary={row['summary']}",
        ))

    for row in sample_rows[35:70]:
        buckets[7].append(make_candidate(
            "BSE",
            "Executive Summary",
            f"Give an executive summary of recent BSE notifications for {row['entity_name']}.",
            "bse",
            f"The answer should summarize BSE notifications for {row['entity_name']}.",
            ["BSE", row["entity_name"]],
            f"id={row['id']} date={row['record_date']} nature={row['nature']} summary={row['summary']}",
        ))

    for row in nature_counts[:30]:
        buckets[8].append(make_candidate(
            "BSE",
            "Distribution",
            f"Show the distribution of BSE notifications by subject and include the category {row['nature']}.",
            "bse",
            f"The BSE subject/nature {row['nature']} appears {row['count']} times.",
            ["BSE", row["nature"], row["count"]],
            f"bse_daily_logs nature={row['nature']} count={row['count']}",
        ))

    for row in sample_rows[70:110]:
        nature = normalize_text(row["nature"]) or "notification"
        buckets[9].append(make_candidate(
            "BSE",
            "Filter Request",
            f"Filter BSE data for {row['entity_name']} where the subject contains {nature.split()[0]}.",
            "bse",
            f"The answer should include BSE records for {row['entity_name']} with nature/subject {nature}.",
            ["BSE", row["entity_name"], nature.split()[0]],
            f"id={row['id']} date={row['record_date']} nature={nature} summary={row['summary']}",
        ))

    for row in sample_rows[110:145]:
        buckets[10].append(make_candidate(
            "BSE",
            "Source Evidence",
            f"For {row['entity_name']}, provide the BSE notification summary and source link for the record dated {row['record_date']}.",
            "bse",
            f"The answer should include summary/link evidence for {row['entity_name']} on {row['record_date']}.",
            ["BSE", row["entity_name"], row["record_date"]],
            f"id={row['id']} date={row['record_date']} link={row['link']} summary={row['summary']}",
        ))

    for row in sample_rows[145:180]:
        buckets[11].append(make_candidate(
            "BSE",
            "Manager Brief",
            f"Prepare a short manager brief from the BSE record for {row['entity_name']} dated {row['record_date']}.",
            "bse",
            f"The answer should brief the BSE record for {row['entity_name']} dated {row['record_date']}.",
            ["BSE", row["entity_name"], row["record_date"]],
            f"id={row['id']} date={row['record_date']} nature={row['nature']} summary={row['summary']}",
        ))

    add_interleaved_candidates(questions, "BSE", buckets)

def generate_generic_source_questions(
    conn: sqlite3.Connection,
    questions: list[dict[str, Any]],
    source: str,
    database: str,
    table: str,
    date_column: str,
    link_column: str,
    created_column: str,
) -> None:
    rows = fetch_all(
        conn,
        f"""
        SELECT id, {date_column} AS date_key, {link_column} AS pdf_link, summary, {created_column} AS inserted_at
        FROM {table}
        WHERE summary IS NOT NULL
          AND TRIM(summary) != ''
        LIMIT 1000
        """,
    )
    rows = sorted(
        rows,
        key=lambda row: (parse_date_value(row["date_key"]) or date.min, row["id"] or 0),
        reverse=True,
    )
    monthly_counts = rows_by_month(rows, "date_key")[:24]
    total_count = scalar(conn, f"SELECT COUNT(*) FROM {table}") or 0

    buckets: list[list[dict[str, Any]]] = [[] for _ in range(12)]

    buckets[0].append(make_candidate(
        source,
        "Total Count",
        f"How many {source} records are available in the updated database?",
        database,
        f"There are {total_count} {source} records in sqlite.db.",
        [source, total_count],
        f"{table} total_count={total_count}",
    ))

    for row in monthly_counts:
        label = month_label(row["month_key"] + "-01")
        buckets[1].append(make_candidate(
            source,
            "Trend Chart",
            f"Create a month-wise trend chart for {source} notifications and include {label}.",
            database,
            f"There are {row['count']} {source} notifications in {row['month_key']}.",
            [source, row["count"], label],
            f"{table} month={row['month_key']} count={row['count']}",
        ))

    for row in rows[:35]:
        keyword = keyword_from_text(row["summary"])
        buckets[2].append(make_candidate(
            source,
            "Table Request",
            f"Create a table of {source} notifications dated around {row['date_key']} with date, topic, and summary.",
            database,
            f"The answer should include {source} records around {row['date_key']} in a table/list format.",
            [source, row["date_key"], keyword],
            f"id={row['id']} date={row['date_key']} summary={row['summary']}",
        ))

    for row in rows[:35]:
        keyword = keyword_from_text(row["summary"])
        buckets[3].append(make_candidate(
            source,
            "Topic Search",
            f"Show {source} updates related to {keyword}, including any item dated {row['date_key']}.",
            database,
            f"The answer should include {source} content related to {keyword}.",
            [source, keyword],
            f"id={row['id']} date={row['date_key']} summary={row['summary']}",
        ))

    for row in rows[35:70]:
        buckets[4].append(make_candidate(
            source,
            "Latest Update",
            f"What are the latest {source} updates around {row['date_key']}?",
            database,
            f"The answer should include {source} records around {row['date_key']}.",
            [source, row["date_key"]],
            f"id={row['id']} date={row['date_key']} summary={row['summary']}",
        ))

    for row in rows[70:105]:
        keyword = keyword_from_text(row["summary"])
        buckets[5].append(make_candidate(
            source,
            "Executive Summary",
            f"Give an executive summary of the {source} item dated {row['date_key']} about {keyword}.",
            database,
            f"The answer should include the {source} record dated {row['date_key']} and mention {keyword}.",
            [source, row["date_key"], keyword],
            f"id={row['id']} date={row['date_key']} link={row['pdf_link']} summary={row['summary']}",
        ))

    for first, second in zip(monthly_counts[0::2], monthly_counts[1::2]):
        first_label = month_label(first["month_key"] + "-01")
        second_label = month_label(second["month_key"] + "-01")
        buckets[6].append(make_candidate(
            source,
            "Month Comparison",
            f"Compare {source} notification volume between {first_label} and {second_label}.",
            database,
            f"{first_label}: {first['count']}; {second_label}: {second['count']}.",
            [source, first_label, first["count"], second_label, second["count"]],
            f"{table} comparison {first['month_key']}={first['count']} {second['month_key']}={second['count']}",
        ))

    for row in rows[105:140]:
        keyword = keyword_from_text(row["summary"])
        buckets[7].append(make_candidate(
            source,
            "Manager Brief",
            f"Prepare a short manager brief for the {source} item dated {row['date_key']} mentioning {keyword}.",
            database,
            f"The answer should brief the {source} record dated {row['date_key']} and mention {keyword}.",
            [source, row["date_key"], keyword],
            f"id={row['id']} date={row['date_key']} summary={row['summary']}",
        ))

    for row in rows[140:175]:
        keyword = keyword_from_text(row["summary"])
        buckets[8].append(make_candidate(
            source,
            "Risk/Compliance Lens",
            f"From a compliance monitoring view, explain the {source} item about {keyword} dated {row['date_key']}.",
            database,
            f"The answer should connect the {source} record dated {row['date_key']} with topic {keyword}.",
            [source, row["date_key"], keyword],
            f"id={row['id']} date={row['date_key']} summary={row['summary']}",
        ))

    for row in rows[175:210]:
        keyword = keyword_from_text(row["summary"])
        buckets[9].append(make_candidate(
            source,
            "Source Evidence",
            f"Provide the source link and short summary for the {source} item dated {row['date_key']} about {keyword}.",
            database,
            f"The answer should include source evidence for the {source} item dated {row['date_key']}.",
            [source, row["date_key"], keyword],
            f"id={row['id']} date={row['date_key']} link={row['pdf_link']} summary={row['summary']}",
        ))

    for row in rows[210:245]:
        keyword = keyword_from_text(row["summary"])
        buckets[10].append(make_candidate(
            source,
            "Question Answering",
            f"Does the {source} database contain any update about {keyword}, and what does it say?",
            database,
            f"The answer should mention {source} data related to {keyword}.",
            [source, keyword],
            f"id={row['id']} date={row['date_key']} summary={row['summary']}",
        ))

    for row in rows[:35]:
        keyword = keyword_from_text(row["summary"])
        buckets[11].append(make_candidate(
            source,
            "Chart by Topic",
            f"Can you show a chart or grouped view of {source} notifications related to {keyword} around {row['date_key']}?",
            database,
            f"The answer should group or chart {source} records related to {keyword}.",
            [source, keyword],
            f"id={row['id']} date={row['date_key']} summary={row['summary']}",
        ))

    add_interleaved_candidates(questions, source, buckets)


def persona_templates() -> list[tuple[str, str]]:
    return [
        (
            "CEO",
            "As the CEO, I need a board-ready explanation of the latest {source} matter dated {date_key} about {topic}. Please summarize the regulatory issue, why it matters strategically, what management should watch, and what one follow-up question I should ask the compliance team.",
        ),
        (
            "CFO",
            "As the CFO, review the {source} notification dated {date_key} related to {topic}. Explain whether there may be financial reporting, provisioning, capital, liquidity, investor communication, or audit committee implications, and give me a concise action checklist.",
        ),
        (
            "CTO",
            "As the CTO, look at the {source} update dated {date_key} about {topic}. Tell me whether this could require any system, data, reporting, workflow, dashboard, archival, automation, or access-control changes, and list the technology questions I should validate.",
        ),
        (
            "Business User",
            "I am a business user, not a technical user. Explain the {source} record dated {date_key} about {topic} in simple language, include the practical business impact, and tell me what information I should share with my manager.",
        ),
        (
            "Compliance Officer",
            "As a compliance officer, analyze the {source} notification dated {date_key} on {topic}. Identify the compliance obligation, likely owner, evidence to retain, timeline questions, and any risk if the organization misses the requirement.",
        ),
        (
            "Risk Manager",
            "As a risk manager, assess the {source} item dated {date_key} concerning {topic}. Classify the risk theme, explain potential operational/regulatory impact, and suggest controls or monitoring indicators we should track.",
        ),
        (
            "Legal Head",
            "As the legal head, review the {source} update dated {date_key} about {topic}. Explain the legal/regulatory interpretation in plain English, what documents or approvals may be needed, and what should be escalated.",
        ),
        (
            "Board Member",
            "As an independent board member, give me a governance-focused briefing on the {source} notification dated {date_key} about {topic}. Highlight why the board should care, key questions for management, and whether this needs committee-level review.",
        ),
        (
            "Investor Relations",
            "As an investor relations user, summarize the {source} record dated {date_key} about {topic}. Tell me whether it could affect disclosures, analyst questions, stakeholder messaging, or market perception, and draft three talking points.",
        ),
        (
            "Operations Head",
            "As the operations head, interpret the {source} update dated {date_key} related to {topic}. Explain what day-to-day process, ownership, tracking, or coordination changes may be required and give a practical next-step plan.",
        ),
    ]


def source_rows_for_persona(conn: sqlite3.Connection, source: str) -> list[sqlite3.Row]:
    if source == "BSE":
        rows = fetch_all(
            conn,
            """
            SELECT id, entity_name, record_date AS date_key, link AS pdf_link, nature, summary
            FROM bse_daily_logs
            WHERE summary IS NOT NULL
              AND TRIM(summary) != ''
              AND entity_name IS NOT NULL
              AND TRIM(entity_name) != ''
            ORDER BY record_date DESC, id ASC
            LIMIT 180
            """,
        )
    elif source == "SEBI":
        rows = fetch_all(
            conn,
            """
            SELECT id, NULL AS entity_name, date_key, pdf_link, NULL AS nature, summary
            FROM sebi_excel_summaries
            WHERE summary IS NOT NULL
              AND TRIM(summary) != ''
            LIMIT 220
            """,
        )
    else:
        rows = fetch_all(
            conn,
            """
            SELECT id, NULL AS entity_name, run_date AS date_key, pdf_link, NULL AS nature, summary
            FROM rbi_master_summaries
            WHERE summary IS NOT NULL
              AND TRIM(summary) != ''
            LIMIT 260
            """,
        )

    return sorted(
        rows,
        key=lambda row: (parse_date_value(row["date_key"]) or date.min, row["id"] or 0),
        reverse=True,
    )


def generate_persona_questions(conn: sqlite3.Connection, questions: list[dict[str, Any]], source: str) -> None:
    database = source.lower()
    rows = source_rows_for_persona(conn, source)
    if not rows:
        raise RuntimeError(f"No rows available for {source} persona questions")

    templates = persona_templates()
    added = 0
    row_index = 0

    while added < PERSONA_PER_SOURCE:
        persona, template = templates[added % len(templates)]
        row = rows[row_index % len(rows)]
        row_index += 1

        topic = keyword_from_text(row["summary"], row["nature"] or source)
        entity_text = f" for {row['entity_name']}" if row["entity_name"] else ""
        question = template.format(source=source, date_key=row["date_key"], topic=topic)
        if entity_text:
            question = question.replace(f"latest {source} matter", f"latest {source} matter{entity_text}")
            question = question.replace(f"the {source} notification", f"the {source} notification{entity_text}")
            question = question.replace(f"the {source} record", f"the {source} record{entity_text}")

        add_question(
            questions,
            source,
            f"Persona - {persona}",
            question,
            database,
            f"The answer should address the {persona} perspective for the {source} record dated {row['date_key']} about {topic}.",
            [source, row["date_key"], topic, persona],
            f"id={row['id']} date={row['date_key']} entity={row['entity_name']} nature={row['nature']} link={row['pdf_link']} summary={row['summary']}",
        )
        added += 1


def generate_questions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    generate_bse_questions(conn, questions)
    generate_generic_source_questions(
        conn,
        questions,
        source="SEBI",
        database="sebi",
        table="sebi_excel_summaries",
        date_column="date_key",
        link_column="pdf_link",
        created_column="inserted_at",
    )
    generate_generic_source_questions(
        conn,
        questions,
        source="RBI",
        database="rbi",
        table="rbi_master_summaries",
        date_column="run_date",
        link_column="pdf_link",
        created_column="created_at",
    )
    for source in ["BSE", "SEBI", "RBI"]:
        generate_persona_questions(conn, questions, source)

    if len(questions) != TOTAL_QUESTIONS:
        raise RuntimeError(f"Expected {TOTAL_QUESTIONS} questions, generated {len(questions)}")

    return questions


def write_questions(output_dir: Path, questions: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "source",
        "database",
        "category",
        "question",
        "expected_answer",
        "expected_keywords",
        "evidence",
    ]

    with (output_dir / "chatbot_eval_questions.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(questions)

    with (output_dir / "chatbot_eval_questions.json").open("w", encoding="utf-8") as file:
        json.dump(questions, file, indent=2, ensure_ascii=False)


def call_chatbot(api_url: str, question: dict[str, Any], timeout: int, limit: int) -> dict[str, Any]:
    payload = {
        "message": question["question"],
        "session_id": f"eval-{question['id']}",
        "database": question["database"],
        "limit": limit,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.perf_counter()
    try:
        with NO_PROXY_OPENER.open(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            data = json.loads(response_body)
            return {
                "http_status": response.status,
                "elapsed_ms": elapsed_ms,
                "answer": normalize_text(data.get("response")),
                "response_type": data.get("response_type"),
                "database_detected": data.get("database_detected"),
                "error": "",
            }
    except urllib.error.HTTPError as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "http_status": error.code,
            "elapsed_ms": elapsed_ms,
            "answer": "",
            "response_type": "",
            "database_detected": "",
            "error": error.read().decode("utf-8", errors="replace"),
        }
    except Exception as error:
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        return {
            "http_status": "",
            "elapsed_ms": elapsed_ms,
            "answer": "",
            "response_type": "",
            "database_detected": "",
            "error": str(error),
        }


def preflight_chatbot(api_url: str, timeout: int) -> None:
    print(f"Preflight check: POST {api_url}")
    result = call_chatbot(
        api_url,
        {
            "id": "PREFLIGHT",
            "question": "hello",
            "database": "all",
            "expected_keywords": "",
        },
        timeout=timeout,
        limit=1,
    )

    status = str(result.get("http_status") or "")
    answer = result.get("answer") or ""
    error = result.get("error") or ""

    if status != "200" or not answer:
        parsed = urllib.parse.urlparse(api_url)
        docs_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/api/docs", "", "", ""))
        openapi_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/openapi.json", "", "", ""))
        detail = error[:500] if error else "No response body returned by server."
        raise RuntimeError(
            "Chatbot API preflight failed. The eval questions were not sent.\n"
            f"API URL: {api_url}\n"
            f"HTTP status: {status or 'no HTTP response'}\n"
            f"Detail: {detail}\n\n"
            "Also verify that this is the AEGIS FastAPI app, not another service:\n"
            f"  curl.exe {docs_url}\n"
            f"  curl.exe {openapi_url}\n\n"
            "From the same terminal/VM, verify the endpoint first:\n"
            f"  curl.exe -X POST {api_url} -H \"Content-Type: application/json\" -d \"{{\\\"message\\\":\\\"hello\\\",\\\"database\\\":\\\"all\\\"}}\"\n\n"
            "If your backend is not on port 8000, rerun with:\n"
            "  python generate_chatbot_eval_questions.py --run --api-url http://127.0.0.1:YOUR_PORT/api/chat/message"
        )

    print(f"Preflight OK: HTTP {status}, response preview: {answer[:120]}")


def score_answer(question: dict[str, Any], api_result: dict[str, Any]) -> tuple[str, str]:
    http_status = str(api_result.get("http_status") or "")
    answer = api_result.get("answer") or ""
    error = api_result.get("error") or ""

    if http_status and http_status != "200":
        detail = f"API returned HTTP {http_status}"
        if error:
            detail = f"{detail}: {error[:200]}"
        return "ERROR", detail

    if error:
        return "ERROR", "API call failed"

    if not answer:
        return "ERROR", "API returned an empty answer"

    answer_lower = answer.lower()
    keywords = [keyword.strip() for keyword in question["expected_keywords"].split("|") if keyword.strip()]
    if not keywords:
        return "CHECK", "No expected keywords configured"

    matched = 0
    for keyword in keywords:
        keyword_text = str(keyword).lower()
        if keyword_text and keyword_text in answer_lower:
            matched += 1

    ratio = matched / len(keywords)
    if ratio >= 0.5:
        return "PASS", f"Matched {matched}/{len(keywords)} expected evidence terms"
    if matched > 0:
        return "CHECK", f"Matched only {matched}/{len(keywords)} expected evidence terms"
    return "CHECK", "No expected evidence terms found; needs manual review"


def run_questions(
    output_dir: Path,
    questions: list[dict[str, Any]],
    api_url: str,
    timeout: int,
    limit: int,
    sleep_seconds: float,
    allow_http_errors: bool,
) -> list[dict[str, Any]]:
    answers: list[dict[str, Any]] = []
    for index, question in enumerate(questions, start=1):
        print(f"[{index}/{len(questions)}] {question['id']} {question['question']}")
        api_result = call_chatbot(api_url, question, timeout=timeout, limit=limit)
        status, notes = score_answer(question, api_result)

        if index == 1 and status == "ERROR" and not allow_http_errors:
            raise RuntimeError(
                "The first chatbot API call failed, so the run was stopped before writing a misleading answers file.\n"
                f"API URL: {api_url}\n"
                f"HTTP status: {api_result.get('http_status')}\n"
                f"Error/detail: {notes}\n"
                "Start the FastAPI backend, confirm the URL/port, then rerun. "
                "Use --allow-http-errors only if you intentionally want to capture failures."
            )

        answers.append({**question, **api_result, "status": status, "review_notes": notes})
        if sleep_seconds:
            time.sleep(sleep_seconds)

    fieldnames = list(answers[0].keys()) if answers else []
    with (output_dir / "chatbot_eval_answers.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(answers)

    return answers


def write_report(
    output_dir: Path,
    db_path: Path,
    questions: list[dict[str, Any]],
    answers: list[dict[str, Any]] | None,
) -> None:
    source_counts = Counter(q["source"] for q in questions)
    category_counts = Counter(q["category"] for q in questions)

    lines = [
        "# AEGIS Chatbot Database Evaluation Report",
        "",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"SQLite database used: `{db_path}`",
        "",
        "## Executive Summary",
        "",
        "This test pack validates whether the current chatbot can answer database-grounded regulatory questions before RAG/vector search is introduced.",
        "The questions are generated directly from the latest SQLite export and cover BSE, SEBI, and RBI data equally.",
        "",
        "## Question Coverage",
        "",
        f"Total questions generated: **{len(questions)}**",
        "",
    ]

    for source in ["BSE", "SEBI", "RBI"]:
        lines.append(f"- {source}: {source_counts[source]} questions")

    lines.extend(["", "## Test Categories", ""])
    for category, count in sorted(category_counts.items()):
        lines.append(f"- {category}: {count}")

    if answers is not None:
        status_counts = Counter(answer["status"] for answer in answers)
        total = len(answers)
        pass_count = status_counts.get("PASS", 0)
        check_count = status_counts.get("CHECK", 0)
        error_count = status_counts.get("ERROR", 0)
        pass_rate = round((pass_count / total) * 100, 2) if total else 0
        avg_ms = round(sum(int(a["elapsed_ms"] or 0) for a in answers) / total, 2) if total else 0

        lines.extend(
            [
                "",
                "## Chatbot Run Results",
                "",
                f"Questions sent to chatbot: **{total}**",
                f"Automatic pass: **{pass_count}**",
                f"Needs manual check: **{check_count}**",
                f"API errors: **{error_count}**",
                f"Indicative pass rate: **{pass_rate}%**",
                f"Average response time: **{avg_ms} ms**",
                "",
                "Note: PASS/CHECK is keyword-based, not an LLM judge. CHECK does not always mean wrong; it means a human should review the answer.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Chatbot Run Results",
                "",
                "The questions were generated but not sent to the chatbot. Run the script with `--run` after starting the backend API.",
            ]
        )

    lines.extend(
        [
            "",
            "## Output Files",
            "",
            f"- `chatbot_eval_questions.csv`: all {len(questions)} questions with expected evidence",
            "- `chatbot_eval_questions.json`: machine-readable question set",
            "- `chatbot_eval_answers.csv`: chatbot answers and automatic review status, created only when `--run` is used",
            "- `chatbot_eval_report.md`: this manager-friendly report",
            "",
            "## Manager Notes",
            "",
            "This evaluation is suitable for pre-RAG validation because it tests direct database retrieval and routing behavior.",
            "After vector database access is available, add semantic/paraphrase-heavy questions and compare RAG answers against this baseline.",
        ]
    )

    (output_dir / "chatbot_eval_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    db_path = Path(args.db).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    if not db_path.is_absolute():
        db_path = (Path.cwd() / db_path).resolve()
    if not output_dir.is_absolute():
        output_dir = (Path.cwd() / output_dir).resolve()

    with connect(db_path) as conn:
        questions = generate_questions(conn)

    write_questions(output_dir, questions)

    answers = None
    if args.run:
        if not args.skip_preflight:
            preflight_chatbot(args.api_url, args.timeout)

        answers = run_questions(
            output_dir,
            questions,
            api_url=args.api_url,
            timeout=args.timeout,
            limit=args.limit,
            sleep_seconds=args.sleep,
            allow_http_errors=args.allow_http_errors,
        )

    write_report(output_dir, db_path, questions, answers)

    print(f"Generated {len(questions)} questions in {output_dir}")
    if args.run:
        print(f"Saved chatbot answers to {output_dir / 'chatbot_eval_answers.csv'}")
    print(f"Saved report to {output_dir / 'chatbot_eval_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
