"""
Database module for research project
Handles all SQLite operations
"""
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import json
import os

# Base directory for data storage
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'research_memory.db')

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_database():
    """Initialize database with schema"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Research sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                date DATETIME NOT NULL,
                num_queries INTEGER,
                ai_mode TEXT,
                query_focus TEXT,
                min_quality_score INTEGER,
                max_sources INTEGER,
                completed BOOLEAN DEFAULT 0,
                cancelled BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Add cancelled column if it doesn't exist (for existing databases)
        cursor.execute("PRAGMA table_info(research_sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'cancelled' not in columns:
            cursor.execute("ALTER TABLE research_sessions ADD COLUMN cancelled BOOLEAN DEFAULT 0")
            print("✓ Added 'cancelled' column to research_sessions table")

        # Generated queries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                query_text TEXT NOT NULL,
                selected BOOLEAN DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES research_sessions(id)
            )
        """)

        # Sources found table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                query_source TEXT,
                ai_score INTEGER,
                score_reasoning TEXT,
                selected BOOLEAN DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES research_sessions(id)
            )
        """)

        # Create indexes for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_topic
            ON research_sessions(topic)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_date
            ON research_sessions(date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sources_url
            ON sources(url)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sources_selected
            ON sources(selected)
        """)

        print("✓ Database initialized successfully")

def save_session_start(topic, num_queries, ai_mode, query_focus, min_quality_score, max_sources):
    """Save a new research session (returns session_id)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO research_sessions
            (topic, date, num_queries, ai_mode, query_focus, min_quality_score, max_sources)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (topic, datetime.now(), num_queries, ai_mode, query_focus, min_quality_score, max_sources))

        return cursor.lastrowid

def save_queries(session_id, queries, selected_queries=None):
    """Save generated queries for a session"""
    if selected_queries is None:
        selected_queries = []

    with get_db() as conn:
        cursor = conn.cursor()
        for query in queries:
            cursor.execute("""
                INSERT INTO queries (session_id, query_text, selected)
                VALUES (?, ?, ?)
            """, (session_id, query, query in selected_queries))

def save_sources(session_id, sources, selected_urls=None):
    """Save found sources for a session"""
    if selected_urls is None:
        selected_urls = []

    with get_db() as conn:
        cursor = conn.cursor()
        for source in sources:
            cursor.execute("""
                INSERT INTO sources
                (session_id, url, title, query_source, ai_score, score_reasoning, selected)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                source.get('url'),
                source.get('title'),
                source.get('query'),
                source.get('relevance_score'),
                source.get('score_reasoning'),
                source.get('url') in selected_urls
            ))

def mark_session_complete(session_id):
    """Mark a session as completed"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE research_sessions
            SET completed = 1
            WHERE id = ?
        """, (session_id,))

def cancel_session(session_id):
    """Mark a session as cancelled (incomplete but saves preferences)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE research_sessions
            SET completed = 0, cancelled = 1
            WHERE id = ?
        """, (session_id,))

def get_recent_sessions(limit=10):
    """Get recent research sessions"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                s.id,
                s.topic,
                s.date,
                s.ai_mode,
                s.completed,
                s.cancelled,
                COUNT(DISTINCT q.id) as query_count,
                COUNT(DISTINCT src.id) as source_count,
                SUM(CASE WHEN src.selected = 1 THEN 1 ELSE 0 END) as selected_count
            FROM research_sessions s
            LEFT JOIN queries q ON s.id = q.session_id
            LEFT JOIN sources src ON s.id = src.session_id
            GROUP BY s.id
            ORDER BY s.date DESC
            LIMIT ?
        """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

def get_session_details(session_id):
    """Get full details of a research session"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get session info
        cursor.execute("""
            SELECT * FROM research_sessions WHERE id = ?
        """, (session_id,))
        session = dict(cursor.fetchone())

        # Get queries
        cursor.execute("""
            SELECT * FROM queries WHERE session_id = ?
        """, (session_id,))
        session['queries'] = [dict(row) for row in cursor.fetchall()]

        # Get sources
        cursor.execute("""
            SELECT * FROM sources WHERE session_id = ?
        """, (session_id,))
        session['sources'] = [dict(row) for row in cursor.fetchall()]

        return session

def get_favorite_sources(min_selections=2):
    """Get sources that have been selected multiple times"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                url,
                title,
                COUNT(*) as times_found,
                SUM(selected) as times_selected,
                AVG(ai_score) as avg_score
            FROM sources
            GROUP BY url
            HAVING times_selected >= ?
            ORDER BY times_selected DESC, avg_score DESC
            LIMIT 20
        """, (min_selections,))

        return [dict(row) for row in cursor.fetchall()]

def get_research_stats():
    """Get overall research statistics"""
    with get_db() as conn:
        cursor = conn.cursor()

        stats = {}

        # Total sessions
        cursor.execute("SELECT COUNT(*) as count FROM research_sessions")
        stats['total_sessions'] = cursor.fetchone()[0]

        # Completed sessions
        cursor.execute("SELECT COUNT(*) as count FROM research_sessions WHERE completed = 1")
        stats['completed_sessions'] = cursor.fetchone()[0]

        # Total sources found
        cursor.execute("SELECT COUNT(*) as count FROM sources")
        stats['total_sources'] = cursor.fetchone()[0]

        # Total sources selected
        cursor.execute("SELECT COUNT(*) as count FROM sources WHERE selected = 1")
        stats['selected_sources'] = cursor.fetchone()[0]

        # Most researched topics
        cursor.execute("""
            SELECT topic, COUNT(*) as count
            FROM research_sessions
            GROUP BY topic
            ORDER BY count DESC
            LIMIT 5
        """)
        stats['top_topics'] = [dict(row) for row in cursor.fetchall()]

        # AI mode usage
        cursor.execute("""
            SELECT ai_mode, COUNT(*) as count
            FROM research_sessions
            WHERE ai_mode IS NOT NULL
            GROUP BY ai_mode
            ORDER BY count DESC
        """)
        stats['ai_mode_usage'] = [dict(row) for row in cursor.fetchall()]

        return stats

def search_history(query):
    """Search through research history"""
    with get_db() as conn:
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT DISTINCT
                s.id,
                s.topic,
                s.date,
                s.ai_mode,
                COUNT(DISTINCT src.id) as source_count
            FROM research_sessions s
            LEFT JOIN queries q ON s.id = q.session_id
            LEFT JOIN sources src ON s.id = src.session_id
            WHERE s.topic LIKE ?
               OR q.query_text LIKE ?
               OR src.title LIKE ?
            GROUP BY s.id
            ORDER BY s.date DESC
            LIMIT 20
        """, (search_term, search_term, search_term))

        return [dict(row) for row in cursor.fetchall()]

# Initialize database on module import
init_database()
