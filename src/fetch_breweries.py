"""
Fetch brewery data from Open Brewery DB API.
Fetches 200 breweries per page for faster collection.
"""

import sqlite3
from config import DB_PATH, BREWERYDB_API_BASE
from utils import fetch_with_retry

PAGE_SIZE = 200


def _get_connection():
    """Returns a database connection and ensures tables exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS brewery_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS breweries (
            id TEXT PRIMARY KEY,
            name TEXT,
            type_id INTEGER,
            city TEXT,
            state TEXT,
            country TEXT,
            postal_code TEXT,
            latitude REAL,
            longitude REAL,
            phone TEXT,
            website_url TEXT,
            has_website INTEGER DEFAULT 0,
            sampled INTEGER DEFAULT 0,
            FOREIGN KEY (type_id) REFERENCES brewery_types(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS brewery_progress (
            id INTEGER PRIMARY KEY,
            current_page INTEGER
        )
    """)
    conn.commit()
    return conn


def _get_or_create_type(conn, type_name):
    """Returns the type ID for a given type name, creating it if necessary."""
    if not type_name:
        type_name = "unknown"
    cur = conn.execute("SELECT id FROM brewery_types WHERE name = ?", (type_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO brewery_types (name) VALUES (?)", (type_name,))
    conn.commit()
    return cur.lastrowid


def _get_current_page(conn):
    """Returns the current page being processed."""
    cur = conn.execute("SELECT current_page FROM brewery_progress WHERE id = 1")
    row = cur.fetchone()
    return row[0] if row else 1


def _save_progress(conn, page):
    """Saves the current progress page."""
    conn.execute(
        "INSERT OR REPLACE INTO brewery_progress (id, current_page) VALUES (1, ?)",
        (page,)
    )
    conn.commit()


def fetch_breweries():
    """
    Fetches one page of breweries (200 items).
    Returns (added_count, total_count).
    """
    conn = _get_connection()
    page = _get_current_page(conn)
    added = 0

    url = f"{BREWERYDB_API_BASE}/breweries"
    params = {
        "per_page": PAGE_SIZE,
        "page": page
    }

    resp = fetch_with_retry(url, params=params)
    if resp is not None:
        breweries = resp.json()

        if not breweries:
            total = conn.execute("SELECT COUNT(*) FROM breweries").fetchone()[0]
            conn.close()
            return 0, total

        for brewery in breweries:
            brewery_id = brewery.get("id")
            if not brewery_id:
                continue

            cur = conn.execute("SELECT 1 FROM breweries WHERE id = ?", (brewery_id,))
            if cur.fetchone():
                continue

            type_id = _get_or_create_type(conn, brewery.get("brewery_type"))
            website_url = brewery.get("website_url")
            has_website = 1 if website_url and website_url.strip() else 0

            conn.execute(
                """INSERT INTO breweries
                   (id, name, type_id, city, state, country, postal_code,
                    latitude, longitude, phone, website_url, has_website)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    brewery_id,
                    brewery.get("name", "Unknown"),
                    type_id,
                    brewery.get("city"),
                    brewery.get("state"),
                    brewery.get("country"),
                    brewery.get("postal_code"),
                    brewery.get("latitude"),
                    brewery.get("longitude"),
                    brewery.get("phone"),
                    website_url,
                    has_website
                )
            )
            added += 1

    _save_progress(conn, page + 1)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM breweries").fetchone()[0]
    conn.close()
    return added, total


if __name__ == "__main__":
    fetch_breweries()
