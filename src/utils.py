"""
Shared utilities for the Food & Drinks Analysis project.
"""

import time
import requests


def fetch_with_retry(url, params=None, max_retries=3, timeout=30):
    """
    Fetches URL with automatic retry on failure.

    Returns the response object on success, or None if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except (requests.RequestException, requests.Timeout) as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                print(
                    f"[Retry {attempt + 1}/{max_retries}] Request failed: {e}. Waiting {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                print(f"[Error] All {max_retries} attempts failed for {url}: {e}")
                return None
    return None


def count_ingredients(item, max_ingredients=20):
    """
    Counts non-empty ingredients in a meal or cocktail.

    Args:
        item: Dictionary containing strIngredient1, strIngredient2, etc.
        max_ingredients: Maximum ingredient index to check (20 for meals, 15 for cocktails).

    Returns:
        Number of non-empty ingredients.
    """
    count = 0
    for i in range(1, max_ingredients + 1):
        ingredient = item.get(f"strIngredient{i}")
        if ingredient and ingredient.strip():
            count += 1
    return count
