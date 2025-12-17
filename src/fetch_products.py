"""
Fetch food products data from Open Food Facts API.
Fetches 24 products per page.
"""

import sqlite3
from config import DB_PATH, OPENFOODFACTS_API_BASE
from utils import fetch_with_retry

PAGE_SIZE = 24
TIMEOUT = 90


def _get_connection():
    """Returns a database connection and ensures tables exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE,
            name TEXT,
            brand TEXT,
            categories TEXT,
            nutrition_grade TEXT,
            nutrition_grade_numeric INTEGER,
            energy_kcal REAL,
            sampled INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products_progress (
            id INTEGER PRIMARY KEY,
            current_page INTEGER
        )
    """)
    conn.commit()
    return conn


def _grade_to_numeric(grade):
    """Converts nutrition grade letter to numeric value (a=1, b=2, c=3, d=4, e=5)."""
    grade_map = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}
    return grade_map.get(grade.lower() if grade else '', None)


def _get_current_page(conn):
    """Returns the current page being processed."""
    cur = conn.execute("SELECT current_page FROM products_progress WHERE id = 1")
    row = cur.fetchone()
    return row[0] if row else 1


def _save_progress(conn, page):
    """Saves the current progress page."""
    conn.execute(
        "INSERT OR REPLACE INTO products_progress (id, current_page) VALUES (1, ?)",
        (page,)
    )
    conn.commit()


def fetch_products():
    """
    Fetches one page of products (24 items).
    Returns (added_count, total_count).
    """
    conn = _get_connection()
    page = _get_current_page(conn)
    added = 0

    url = f"{OPENFOODFACTS_API_BASE}/cgi/search.pl"
    params = {
        "search_terms": "food",
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": PAGE_SIZE,
        "page": page
    }

    resp = fetch_with_retry(url, params=params, timeout=TIMEOUT)
    if resp is not None:
        data = resp.json()
        products = data.get("products") or []

        for product in products:
            barcode = product.get("code")
            if not barcode:
                continue

            cur = conn.execute("SELECT 1 FROM products WHERE barcode = ?", (barcode,))
            if cur.fetchone():
                continue

            name = product.get("product_name") or "Unknown"
            if len(name) < 2:
                continue

            brand = product.get("brands") or ""
            categories = product.get("categories") or ""
            nutrition_grade = product.get("nutrition_grades") or ""
            nutrition_grade_num = _grade_to_numeric(nutrition_grade)
            energy = product.get("nutriments", {}).get("energy-kcal_100g")

            conn.execute(
                "INSERT INTO products (barcode, name, brand, categories, nutrition_grade, nutrition_grade_numeric, energy_kcal) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (barcode, name[:100], brand[:100], categories[:200], nutrition_grade, nutrition_grade_num, energy)
            )
            added += 1

    _save_progress(conn, page + 1)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    return added, total


if __name__ == "__main__":
    fetch_products()
