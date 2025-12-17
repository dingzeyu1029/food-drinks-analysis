"""
Random sampling module with seed support for reproducible data selection.
"""

import random
import sqlite3
from config import DB_PATH, VALID_TABLES
from db import get_connection


def _create_sampling_config_table(conn):
    """Creates the sampling configuration table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sampling_config (
            id INTEGER PRIMARY KEY,
            random_seed INTEGER NOT NULL,
            target_sample_size INTEGER DEFAULT 500,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def _store_seed(conn, seed, sample_size=500):
    """Stores the random seed and sample size in the database."""
    _create_sampling_config_table(conn)
    conn.execute("DELETE FROM sampling_config")
    conn.execute(
        "INSERT INTO sampling_config (random_seed, target_sample_size) VALUES (?, ?)",
        (seed, sample_size)
    )
    conn.commit()


def _sample_from_table(conn, table_name, sample_size, seed):
    """
    Randomly samples items from a table using a reproducible seed.
    Marks selected items with sampled=1.

    Args:
        conn: Database connection.
        table_name: Name of the table to sample from (must be in VALID_TABLES).
        sample_size: Number of items to sample.
        seed: Random seed for reproducibility.

    Returns:
        Number of items sampled.

    Raises:
        ValueError: If table_name is not in the whitelist.
    """
    if table_name not in VALID_TABLES:
        raise ValueError(f"Invalid table name: {table_name}. Must be one of {VALID_TABLES}")

    random.seed(seed)

    cur = conn.execute(f"SELECT id FROM {table_name}")
    all_ids = [row[0] for row in cur.fetchall()]

    if len(all_ids) == 0:
        return 0

    if len(all_ids) <= sample_size:
        sampled_ids = all_ids
    else:
        sampled_ids = random.sample(all_ids, sample_size)

    conn.execute(f"UPDATE {table_name} SET sampled = 0")

    placeholders = ','.join('?' * len(sampled_ids))
    conn.execute(
        f"UPDATE {table_name} SET sampled = 1 WHERE id IN ({placeholders})",
        sampled_ids
    )
    conn.commit()

    return len(sampled_ids)


def sample_all_tables(seed, sample_size=500):
    """
    Samples from all data tables using the given seed.

    Args:
        seed: Random seed for reproducibility.
        sample_size: Number of items to sample per table.

    Returns:
        Dictionary with table names and sample counts.
    """
    conn = get_connection()
    _store_seed(conn, seed, sample_size)

    results = {}

    for table in VALID_TABLES:
        try:
            count = _sample_from_table(conn, table, sample_size, seed)
            results[table] = count
        except sqlite3.OperationalError:
            results[table] = 0

    conn.close()
    return results
