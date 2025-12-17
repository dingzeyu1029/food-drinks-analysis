"""
Shared configuration constants for the Food & Drinks Analysis project.
"""

DB_PATH = "data/food_drinks.db"
OUTPUT_DIR = "output"

# API endpoints
MEALDB_API_BASE = "https://www.themealdb.com/api/json/v1/1"
COCKTAILDB_API_BASE = "https://www.thecocktaildb.com/api/json/v1/1"
BREWERYDB_API_BASE = "https://api.openbrewerydb.org/v1"
OPENFOODFACTS_API_BASE = "https://world.openfoodfacts.org"

# Sampling configuration
RANDOM_SEED = 42
SAMPLE_SIZE = 500

# Fetch configuration
MIN_ITEMS = 500
MAX_BATCHES = 30

# Valid table names for sampling (whitelist for SQL safety)
VALID_TABLES = frozenset(['meals', 'cocktails', 'products', 'breweries'])
