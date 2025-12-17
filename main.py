"""
Main orchestrator for the Food & Drinks Analysis project.
Fetches data from all 4 APIs, performs random sampling with a seed,
runs statistical analysis, and creates visualizations.
"""

import sys
import os
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import RANDOM_SEED, SAMPLE_SIZE, MIN_ITEMS, MAX_BATCHES
from fetch_meals import fetch_meals
from fetch_cocktails import fetch_cocktails
from fetch_products import fetch_products
from fetch_breweries import fetch_breweries
from sampling import sample_all_tables
from analysis import run_all_analyses, format_analysis_report
from visualizations import create_all_visualizations


def ensure_directories():
    """Creates data and output directories, cleaning them if they exist."""
    for folder in ["data", "output"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)


def fetch_all_data():
    """Fetches data from all APIs until each has MIN_ITEMS+ items."""
    meals_done = False
    cocktails_done = False
    products_done = False
    breweries_done = False

    for batch in range(1, MAX_BATCHES + 1):
        print(f"\n--- Batch {batch} ---")

        if not meals_done:
            try:
                added, total = fetch_meals()
                if total >= MIN_ITEMS or added == 0:
                    meals_done = True
                done = " [done]" if meals_done else ""
                print(f"{'Meals:':<10} {added:>3} added, {total:>4} total{done}")
            except Exception as e:
                print(f"{'Meals:':<10} [Error] {e}")

        if not cocktails_done:
            try:
                added, total = fetch_cocktails()
                if total >= MIN_ITEMS or added == 0:
                    cocktails_done = True
                done = " [done]" if cocktails_done else ""
                print(f"{'Cocktails:':<10} {added:>3} added, {total:>4} total{done}")
            except Exception as e:
                print(f"{'Cocktails:':<10} [Error] {e}")

        if not products_done:
            try:
                added, total = fetch_products()
                if total >= MIN_ITEMS or added == 0:
                    products_done = True
                done = " [done]" if products_done else ""
                print(f"{'Products:':<10} {added:>3} added, {total:>4} total{done}")
            except Exception as e:
                print(f"{'Products:':<10} [Error] {e}")

        if not breweries_done:
            try:
                added, total = fetch_breweries()
                if total >= MIN_ITEMS or added == 0:
                    breweries_done = True
                done = " [done]" if breweries_done else ""
                print(f"{'Breweries:':<10} {added:>3} added, {total:>4} total{done}")
            except Exception as e:
                print(f"{'Breweries:':<10} [Error] {e}")

        if meals_done and cocktails_done and products_done and breweries_done:
            print("\nAll data collection complete!\n")
            break


def perform_sampling():
    """Performs random sampling with the configured seed."""
    print(f"Performing random sampling (seed={RANDOM_SEED}, size={SAMPLE_SIZE})...")
    results = sample_all_tables(RANDOM_SEED, SAMPLE_SIZE)

    for table, count in results.items():
        print(f"  {table}: {count} items sampled")

    print()


def run_analysis():
    """Runs statistical analysis and saves results."""
    print("Running statistical analysis...")
    results = run_all_analyses()
    report = format_analysis_report(results, seed=RANDOM_SEED, sample_size=SAMPLE_SIZE)

    output_path = "output/calculations.txt"
    with open(output_path, "w") as f:
        f.write(report)

    print(f"  Analysis results saved to {output_path}")
    print()

    return results


def create_visualizations():
    """Creates all visualizations."""
    print("Creating visualizations...")
    created = create_all_visualizations()

    for filename in created:
        print(f"  Created: output/{filename}")

    print()


def main():
    """Main entry point."""
    print("=" * 70)
    print("FOOD & DRINKS ANALYSIS PROJECT")
    print(f"Random Seed: {RANDOM_SEED} | Target Sample Size: {SAMPLE_SIZE}")
    print("=" * 70)

    ensure_directories()

    print("\n" + "=" * 70)
    print("PHASE 1: FETCHING DATA FROM APIs")
    print("=" * 70)
    fetch_all_data()

    print("=" * 70)
    print("PHASE 2: RANDOM SAMPLING")
    print("=" * 70)
    perform_sampling()

    print("=" * 70)
    print("PHASE 3: STATISTICAL ANALYSIS")
    print("=" * 70)
    run_analysis()

    print("=" * 70)
    print("PHASE 4: CREATING VISUALIZATIONS")
    print("=" * 70)
    create_visualizations()

    print("=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print("\nOutput files:")
    print("  - output/calculations.txt (statistical analysis)")
    print("  - output/*.png (visualizations)")


if __name__ == "__main__":
    main()
