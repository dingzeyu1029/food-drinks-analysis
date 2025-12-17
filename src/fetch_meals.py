"""
Fetch meals data from TheMealDB API.
Fetches ALL meals by iterating through letters a-z in one pass.
"""

import sqlite3
from config import DB_PATH, MEALDB_API_BASE
from utils import fetch_with_retry, count_ingredients


def _get_connection():
    """Returns a database connection and ensures tables exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meal_categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            description TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category_id INTEGER,
            area TEXT,
            instructions TEXT,
            ingredient_count INTEGER,
            sampled INTEGER DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES meal_categories(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fetch_progress (
            api TEXT PRIMARY KEY,
            current_letter TEXT
        )
    """)
    conn.commit()
    return conn


def _fetch_categories(conn):
    """Fetches and stores meal categories from the API."""
    resp = fetch_with_retry(f"{MEALDB_API_BASE}/categories.php")
    if resp is None:
        return
    data = resp.json()
    if not data.get("categories"):
        return
    for cat in data["categories"]:
        conn.execute(
            "INSERT OR IGNORE INTO meal_categories (id, name, description) VALUES (?, ?, ?)",
            (int(cat["idCategory"]), cat["strCategory"], cat["strCategoryDescription"][:200])
        )
    conn.commit()


def _get_category_id(conn, category_name):
    """Returns the category ID for a given category name."""
    cur = conn.execute("SELECT id FROM meal_categories WHERE name = ?", (category_name,))
    row = cur.fetchone()
    return row[0] if row else None


def _get_current_letter(conn):
    """Returns the current letter being processed."""
    cur = conn.execute("SELECT current_letter FROM fetch_progress WHERE api = 'meals'")
    row = cur.fetchone()
    return row[0] if row else 'a'


def _save_progress(conn, letter):
    """Saves the current progress letter."""
    conn.execute(
        "INSERT OR REPLACE INTO fetch_progress (api, current_letter) VALUES ('meals', ?)",
        (letter,)
    )
    conn.commit()


def fetch_meals():
    """
    Fetches ALL meals for the current letter, then moves to next letter.
    Returns (added_count, total_count).
    """
    conn = _get_connection()
    _fetch_categories(conn)

    letter = _get_current_letter(conn)
    added = 0

    if letter > 'z':
        total = conn.execute("SELECT COUNT(*) FROM meals").fetchone()[0]
        conn.close()
        return 0, total

    resp = fetch_with_retry(f"{MEALDB_API_BASE}/search.php?f={letter}")
    if resp is not None:
        data = resp.json()
        meals = data.get("meals") or []

        for meal in meals:
            meal_id = int(meal["idMeal"])
            cur = conn.execute("SELECT 1 FROM meals WHERE id = ?", (meal_id,))
            if cur.fetchone():
                continue

            category_id = _get_category_id(conn, meal["strCategory"])
            ingredient_count = count_ingredients(meal, max_ingredients=20)
            conn.execute(
                "INSERT INTO meals (id, name, category_id, area, instructions, ingredient_count) VALUES (?, ?, ?, ?, ?, ?)",
                (meal_id, meal["strMeal"], category_id, meal["strArea"], meal["strInstructions"][:500], ingredient_count)
            )
            added += 1

    next_letter = chr(ord(letter) + 1)
    _save_progress(conn, next_letter)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM meals").fetchone()[0]
    conn.close()
    return added, total


if __name__ == "__main__":
    fetch_meals()
