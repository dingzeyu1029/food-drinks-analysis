"""
Enhanced visualization module using matplotlib and seaborn.
Creates statistical plots including regression lines and box plots.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from config import OUTPUT_DIR
from db import get_connection


def _setup_style():
    """Sets up consistent plot styling."""
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['font.size'] = 10


def plot_meals_by_area(output_path=None):
    """Creates a box plot of ingredient count by cuisine area."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT area, ingredient_count
        FROM meals
        WHERE sampled = 1 AND ingredient_count IS NOT NULL AND area IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 5:
        return

    top_areas = df['area'].value_counts().head(10).index
    df_filtered = df[df['area'].isin(top_areas)]

    area_order = df_filtered.groupby('area')['ingredient_count'].median().sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=df_filtered, x='area', y='ingredient_count', order=area_order, ax=ax)

    ax.set_xlabel('Cuisine Area')
    ax.set_ylabel('Number of Ingredients')
    ax.set_title('Ingredient Complexity by Cuisine (Top 10 Areas)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def plot_meals_by_category(output_path=None):
    """Creates a bar chart of average ingredients by category."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT mc.name as category, m.ingredient_count
        FROM meals m
        LEFT JOIN meal_categories mc ON m.category_id = mc.id
        WHERE m.sampled = 1 AND m.ingredient_count IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 5:
        return

    cat_stats = df.groupby('category')['ingredient_count'].agg(['mean', 'std', 'count'])
    cat_stats = cat_stats.sort_values('mean', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(cat_stats.index, cat_stats['mean'], xerr=cat_stats['std'], capsize=3)
    ax.set_xlabel('Average Number of Ingredients')
    ax.set_ylabel('Category')
    ax.set_title('Average Ingredient Count by Meal Category')

    for i, (idx, row) in enumerate(cat_stats.iterrows()):
        ax.annotate(f'n={int(row["count"])}', xy=(row['mean'] + row['std'] + 0.5, i),
                   va='center', fontsize=8, color='gray')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def plot_cocktails_by_alcoholic(output_path=None):
    """Creates a box plot comparing ingredient counts by alcoholic status."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT is_alcoholic, ingredient_count
        FROM cocktails
        WHERE sampled = 1 AND ingredient_count IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 5:
        return

    df['status'] = df['is_alcoholic'].map({0: 'Non-Alcoholic', 1: 'Alcoholic'})

    status_order = ['Alcoholic', 'Non-Alcoholic']

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.boxplot(data=df, x='status', y='ingredient_count', order=status_order, ax=ax)
    sns.stripplot(data=df, x='status', y='ingredient_count', order=status_order, ax=ax, color='black', alpha=0.3, size=4)

    ax.set_xlabel('Alcoholic Status')
    ax.set_ylabel('Number of Ingredients')
    ax.set_title('Ingredient Complexity: Alcoholic vs Non-Alcoholic Cocktails')

    means = df.groupby('status')['ingredient_count'].mean()
    for i, status in enumerate(status_order):
        if status in means.index:
            ax.annotate(f'mean={means[status]:.1f}', xy=(i, means[status]),
                       xytext=(i + 0.2, means[status]), fontsize=10)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def plot_cocktails_by_glass(output_path=None):
    """Creates a bar chart of average ingredients by glass type."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT glass, ingredient_count
        FROM cocktails
        WHERE sampled = 1 AND ingredient_count IS NOT NULL AND glass IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 5:
        return

    df['glass'] = df['glass'].str.title()

    top_glasses = df['glass'].value_counts().head(10).index
    df_filtered = df[df['glass'].isin(top_glasses)]

    glass_stats = df_filtered.groupby('glass')['ingredient_count'].agg(['mean', 'count'])
    glass_stats = glass_stats.sort_values('mean', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(glass_stats.index, glass_stats['mean'])
    ax.set_xlabel('Average Number of Ingredients')
    ax.set_ylabel('Glass Type')
    ax.set_title('Average Ingredient Count by Glass Type (Top 10)')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def plot_products_regression(output_path=None):
    """Creates a scatter plot with regression line: calories vs nutrition grade."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT nutrition_grade, nutrition_grade_numeric, energy_kcal
        FROM products
        WHERE sampled = 1
          AND nutrition_grade_numeric IS NOT NULL
          AND energy_kcal IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 5:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    jitter = np.random.normal(0, 0.1, len(df))
    ax.scatter(df['nutrition_grade_numeric'] + jitter, df['energy_kcal'],
              alpha=0.5, edgecolors='none', s=50)

    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df['nutrition_grade_numeric'], df['energy_kcal']
    )
    x_line = np.array([1, 5])
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', linewidth=2,
            label=f'y = {slope:.1f}x + {intercept:.1f}\nR² = {r_value**2:.3f}, p = {p_value:.4f}')

    ax.set_xlabel('Nutrition Grade (1=A, 5=E)')
    ax.set_ylabel('Energy (kcal/100g)')
    ax.set_title('Calories vs Nutrition Grade - Linear Regression')
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels(['A', 'B', 'C', 'D', 'E'])
    ax.legend(loc='upper left')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def plot_products_boxplot(output_path=None):
    """Creates a box plot of calories by nutrition grade."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT nutrition_grade, energy_kcal
        FROM products
        WHERE sampled = 1
          AND nutrition_grade IN ('a', 'b', 'c', 'd', 'e')
          AND energy_kcal IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 5:
        return

    grade_order = ['a', 'b', 'c', 'd', 'e']

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=df, x='nutrition_grade', y='energy_kcal',
               order=grade_order, ax=ax)

    ax.set_xlabel('Nutrition Grade')
    ax.set_ylabel('Energy (kcal/100g)')
    ax.set_title('Calorie Distribution by Nutrition Grade')
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xticklabels(['A', 'B', 'C', 'D', 'E'])

    counts = df.groupby('nutrition_grade').size()
    for i, grade in enumerate(grade_order):
        if grade in counts.index:
            ax.annotate(f'n={counts[grade]}', xy=(i, ax.get_ylim()[1]),
                       ha='center', va='bottom', fontsize=9, color='gray')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def plot_breweries_website(output_path=None):
    """Creates a stacked bar chart of website presence by brewery type."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT bt.name as brewery_type, b.has_website
        FROM breweries b
        LEFT JOIN brewery_types bt ON b.type_id = bt.id
        WHERE b.sampled = 1 AND bt.name IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 5:
        return

    cross = pd.crosstab(df['brewery_type'], df['has_website'], normalize='index') * 100
    cross.columns = ['No Website', 'Has Website']
    cross = cross.sort_values('Has Website', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 8))
    cross.plot(kind='barh', stacked=True, ax=ax, color=['#ff7f7f', '#7fbf7f'])

    ax.set_xlabel('Percentage')
    ax.set_ylabel('Brewery Type')
    ax.set_title('Website Presence by Brewery Type')
    ax.legend(title='', loc='lower right')

    for i, (idx, row) in enumerate(cross.iterrows()):
        ax.annotate(f'{row["Has Website"]:.0f}%',
                   xy=(row["Has Website"] / 2, i),
                   ha='center', va='center', fontsize=9, color='white', fontweight='bold')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def plot_breweries_geographic(output_path=None):
    """Creates a scatter plot of brewery locations colored by type."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT bt.name as brewery_type, b.latitude, b.longitude
        FROM breweries b
        LEFT JOIN brewery_types bt ON b.type_id = bt.id
        WHERE b.sampled = 1
          AND b.latitude IS NOT NULL
          AND b.longitude IS NOT NULL
    """, conn)
    conn.close()

    df = df[
        (df['latitude'] >= -90) & (df['latitude'] <= 90) &
        (df['longitude'] >= -180) & (df['longitude'] <= 180)
    ]

    if len(df) < 5:
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    types = df['brewery_type'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(types)))

    for i, btype in enumerate(types):
        mask = df['brewery_type'] == btype
        ax.scatter(df.loc[mask, 'longitude'], df.loc[mask, 'latitude'],
                  c=[colors[i]], label=btype, alpha=0.6, s=50)

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Geographic Distribution of Breweries by Type')
    ax.legend(title='Brewery Type', loc='lower left', fontsize=8)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def plot_breweries_by_state(output_path=None):
    """Creates a bar chart of top states by brewery count."""
    _setup_style()

    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT state
        FROM breweries
        WHERE sampled = 1 AND state IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 5:
        return

    state_counts = df['state'].value_counts().head(15)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(range(len(state_counts)), state_counts.values)
    ax.set_xticks(range(len(state_counts)))
    ax.set_xticklabels(state_counts.index, rotation=45, ha='right')
    ax.set_xlabel('State')
    ax.set_ylabel('Number of Breweries')
    ax.set_title('Top 15 States by Number of Breweries')

    for i, v in enumerate(state_counts.values):
        ax.annotate(str(v), xy=(i, v), ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.close()


def create_all_visualizations():
    """Creates all visualizations and saves them to the output directory."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    visualizations = [
        ('meals_by_area.png', plot_meals_by_area),
        ('meals_by_category.png', plot_meals_by_category),
        ('cocktails_by_alcoholic.png', plot_cocktails_by_alcoholic),
        ('cocktails_by_glass.png', plot_cocktails_by_glass),
        ('products_regression.png', plot_products_regression),
        ('products_boxplot.png', plot_products_boxplot),
        ('breweries_website.png', plot_breweries_website),
        ('breweries_geographic.png', plot_breweries_geographic),
        ('breweries_by_state.png', plot_breweries_by_state),
    ]

    created = []
    for filename, plot_func in visualizations:
        try:
            output_path = f"{OUTPUT_DIR}/{filename}"
            plot_func(output_path)
            created.append(filename)
        except Exception as e:
            print(f"Error creating {filename}: {e}")

    return created
