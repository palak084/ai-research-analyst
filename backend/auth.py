import sqlite3
import hashlib
import secrets
import json
import time
import os

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "research_analyst.db")
)


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            input_text TEXT NOT NULL,
            plan TEXT NOT NULL,
            analysis TEXT NOT NULL,
            insights TEXT NOT NULL,
            web_results TEXT DEFAULT '[]',
            created_at REAL NOT NULL,
            title TEXT DEFAULT '',
            FOREIGN KEY (username) REFERENCES users(username)
        );
    """)
    conn.commit()
    conn.close()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode()).hexdigest()


def create_user(username: str, password: str, full_name: str = "") -> dict | None:
    """Create a new user. Returns user dict or None if username exists."""
    conn = _get_conn()
    try:
        salt = secrets.token_hex(16)
        password_hash = _hash_password(password, salt)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, salt, full_name, time.time())
        )
        conn.commit()
        return {"username": username, "full_name": full_name}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> dict | None:
    """Verify credentials. Returns user dict or None."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    expected = _hash_password(password, row["salt"])
    if expected != row["password_hash"]:
        return None

    return {"username": row["username"], "full_name": row["full_name"]}


def create_access_token(username: str) -> str:
    """Create a simple token (username:random_hex)."""
    return f"{username}:{secrets.token_hex(32)}"


def get_current_user(token: str) -> str | None:
    """Extract username from token."""
    if not token or ":" not in token:
        return None
    return token.split(":")[0]


def save_analysis(
    username: str,
    input_text: str,
    plan: str,
    analysis: str,
    insights: str,
    web_results: list = None
) -> int:
    """Save an analysis to history. Returns analysis ID."""
    conn = _get_conn()
    # Generate a short title from the first ~60 chars of input
    title = input_text[:60].replace("\n", " ").strip()
    if len(input_text) > 60:
        title += "..."

    cursor = conn.execute(
        "INSERT INTO analyses (username, input_text, plan, analysis, insights, "
        "web_results, created_at, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            username, input_text, plan, analysis, insights,
            json.dumps(web_results or []), time.time(), title
        )
    )
    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    return analysis_id


def get_user_history(username: str) -> list:
    """Get all analyses for a user, newest first."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, title, created_at FROM analyses "
        "WHERE username = ? ORDER BY created_at DESC",
        (username,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_analysis_by_id(analysis_id: int) -> dict | None:
    """Get full analysis by ID."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    result["web_results"] = json.loads(result["web_results"])
    return result


def delete_analysis(analysis_id: int):
    """Delete an analysis by ID."""
    conn = _get_conn()
    conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    conn.close()
