"""
Shared database utilities for the Food & Drinks Analysis project.
"""

import sqlite3
from config import DB_PATH


def get_connection():
    """Returns a database connection."""
    return sqlite3.connect(DB_PATH)
