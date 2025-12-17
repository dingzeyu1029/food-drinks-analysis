# Food & Drinks Analysis

Statistical analysis of food and beverage data from public APIs.

## Overview

This project collects data from four public APIs, performs random sampling for reproducibility, runs statistical analyses, and generates visualizations.

### Data Sources

- **TheMealDB** - Meal recipes with ingredients and categories
- **TheCocktailDB** - Cocktail recipes with ingredients and glass types
- **Open Food Facts** - Food products with nutrition grades and calorie data
- **Open Brewery DB** - US brewery information with locations and types

## Requirements

- Python 3.9+
- uv (package manager)

## Installation

```bash
uv sync
```

## Usage

Run the full pipeline:

```bash
uv run python main.py
```

This will:

1. Fetch data from all four APIs (minimum 500 items each)
2. Perform random sampling with seed 42 for reproducibility
3. Run statistical analyses (correlations, chi-square tests, linear regression)
4. Generate visualizations

## Output

Results are saved to the `output/` directory:

- `calculations.txt` - Statistical analysis results
- `*.png` - Visualization charts

## Project Structure

```
.
├── main.py                 # Main orchestrator
├── pyproject.toml          # Project dependencies
└── src/
    ├── config.py           # Shared configuration constants
    ├── db.py               # Database connection utilities
    ├── utils.py            # Shared utilities (API fetching, helpers)
    ├── fetch_meals.py      # TheMealDB data fetcher
    ├── fetch_cocktails.py  # TheCocktailDB data fetcher
    ├── fetch_products.py   # Open Food Facts data fetcher
    ├── fetch_breweries.py  # Open Brewery DB data fetcher
    ├── sampling.py         # Random sampling with seed support
    ├── analysis.py         # Statistical analysis module
    └── visualizations.py   # Chart generation module
```

## Configuration

Edit `src/config.py` to modify:

- `RANDOM_SEED` - Seed for reproducible sampling (default: 42)
- `SAMPLE_SIZE` - Number of items to sample per API (default: 500)
- `MIN_ITEMS` - Minimum items to fetch before stopping (default: 500)
- `MAX_BATCHES` - Maximum fetch iterations (default: 30)

## Statistical Methods

- **Spearman Correlation** - Area vs ingredient count (meals), calories vs nutrition grade (products)
- **Point-Biserial Correlation** - Alcoholic status vs ingredient count (cocktails)
- **Chi-Square Test** - Brewery type vs website presence
- **Linear Regression** - Predicting nutrition grade from calorie content
