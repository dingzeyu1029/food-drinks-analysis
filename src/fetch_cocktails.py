"""
Fetch cocktails data from TheCocktailDB API.
Fetches ALL cocktails by iterating through letters a-z in one pass.
"""

import sqlite3
from config import DB_PATH, COCKTAILDB_API_BASE
from utils import fetch_with_retry, count_ingredients


def _get_connection():
    """Returns a database connection and ensures tables exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cocktails (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            glass TEXT,
            is_alcoholic INTEGER,
            instructions TEXT,
            ingredient_count INTEGER,
            sampled INTEGER DEFAULT 0
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


def _get_current_letter(conn):
    """Returns the current letter being processed."""
    cur = conn.execute("SELECT current_letter FROM fetch_progress WHERE api = 'cocktails'")
    row = cur.fetchone()
    return row[0] if row else 'a'


def _save_progress(conn, letter):
    """Saves the current progress letter."""
    conn.execute(
        "INSERT OR REPLACE INTO fetch_progress (api, current_letter) VALUES ('cocktails', ?)",
        (letter,)
    )
    conn.commit()


def fetch_cocktails():
    """
    Fetches ALL cocktails for the current letter, then moves to next letter.
    Returns (added_count, total_count).
    """
    conn = _get_connection()

    letter = _get_current_letter(conn)
    added = 0

    if letter > 'z':
        total = conn.execute("SELECT COUNT(*) FROM cocktails").fetchone()[0]
        conn.close()
        return 0, total

    resp = fetch_with_retry(f"{COCKTAILDB_API_BASE}/search.php?f={letter}")
    if resp is not None:
        data = resp.json()
        drinks = data.get("drinks") or []

        for drink in drinks:
            drink_id = int(drink["idDrink"])
            cur = conn.execute("SELECT 1 FROM cocktails WHERE id = ?", (drink_id,))
            if cur.fetchone():
                continue

            is_alcoholic = 1 if drink.get("strAlcoholic") == "Alcoholic" else 0
            instructions = drink.get("strInstructions") or ""
            ingredient_count = count_ingredients(drink, max_ingredients=15)

            conn.execute(
                "INSERT INTO cocktails (id, name, category, glass, is_alcoholic, instructions, ingredient_count) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (drink_id, drink["strDrink"], drink.get("strCategory"), drink.get("strGlass"), is_alcoholic, instructions[:500], ingredient_count)
            )
            added += 1

    next_letter = chr(ord(letter) + 1)
    _save_progress(conn, next_letter)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM cocktails").fetchone()[0]
    conn.close()
    return added, total


if __name__ == "__main__":
    fetch_cocktails()
