"""Cache manager for API responses and OCR results to improve performance."""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timedelta
import tempfile

DB_PATH = os.path.join(tempfile.gettempdir(), "cache.db")


def _init_cache_db():
    """Initialize cache database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT,
            created_at TEXT,
            expires_at TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_key ON cache(key)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)')
    conn.commit()
    conn.close()


def _get_hash(text):
    """Generate SHA256 hash of text for cache key."""
    return hashlib.sha256(text.encode()).hexdigest()


def get_cached(text, cache_type="extraction"):
    """Get cached result if it exists and hasn't expired."""
    _init_cache_db()
    key = f"{cache_type}:{_get_hash(text)}"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM cache WHERE key = ? AND expires_at > datetime('now')",
            (key,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
    except Exception as e:
        print(f"Cache read error: {e}")
    
    return None


def set_cache(text, value, cache_type="extraction", ttl_hours=24):
    """Store result in cache with TTL (Time To Live)."""
    _init_cache_db()
    key = f"{cache_type}:{_get_hash(text)}"
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        created_at = datetime.now().isoformat()
        expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        
        cursor.execute(
            "INSERT OR REPLACE INTO cache (key, value, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (key, json.dumps(value, ensure_ascii=False), created_at, expires_at)
        )
        conn.commit()
        conn.close()
        print(f"Cached for {cache_type}")
    except Exception as e:
        print(f"Cache write error: {e}")


def clear_expired_cache():
    """Remove expired cache entries."""
    _init_cache_db()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache WHERE expires_at <= datetime('now')")
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted > 0:
            print(f"Cleared {deleted} expired cache entries")
    except Exception as e:
        print(f"Cache cleanup error: {e}")


def cache_stats():
    """Get cache statistics."""
    _init_cache_db()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cache WHERE expires_at > datetime('now')")
        valid = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cache")
        total = cursor.fetchone()[0]
        conn.close()
        return {"valid": valid, "total": total}
    except Exception as e:
        print(f"Cache stats error: {e}")
        return {"valid": 0, "total": 0}
