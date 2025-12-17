"""
Statistical analysis module using pandas, numpy, and scipy.
Performs correlation and regression analysis on the collected data.
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency, pointbiserialr, spearmanr
from db import get_connection


def _format_p_value(p):
    """Formats p-value for display."""
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"


def _interpret_correlation(r):
    """Interprets correlation strength."""
    abs_r = abs(r)
    if abs_r < 0.1:
        strength = "negligible"
    elif abs_r < 0.3:
        strength = "weak"
    elif abs_r < 0.5:
        strength = "moderate"
    elif abs_r < 0.7:
        strength = "strong"
    else:
        strength = "very strong"

    direction = "positive" if r > 0 else "negative"
    return f"{strength} {direction}"


def analyze_meals():
    """
    Analyzes meals data:
    - Correlation: Area vs ingredient_count (Spearman)
    - Summary statistics by area
    """
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT m.id, m.name, m.area, m.ingredient_count, mc.name as category
        FROM meals m
        LEFT JOIN meal_categories mc ON m.category_id = mc.id
        WHERE m.sampled = 1 AND m.ingredient_count IS NOT NULL
    """, conn)
    conn.close()

    results = {
        'name': 'TheMealDB',
        'sample_size': len(df),
        'analyses': []
    }

    if len(df) < 5:
        results['error'] = 'Insufficient data for analysis'
        return results

    results['ingredient_stats'] = {
        'mean': df['ingredient_count'].mean(),
        'std': df['ingredient_count'].std(),
        'min': df['ingredient_count'].min(),
        'max': df['ingredient_count'].max()
    }

    if df['area'].nunique() > 1:
        area_encoded = pd.factorize(df['area'])[0]
        corr, p_value = spearmanr(area_encoded, df['ingredient_count'])

        results['analyses'].append({
            'name': 'Area vs Ingredient Count',
            'type': 'Spearman Correlation',
            'correlation': corr,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'interpretation': _interpret_correlation(corr)
        })

    area_stats = df.groupby('area')['ingredient_count'].agg(['mean', 'std', 'count'])
    area_stats = area_stats.sort_values('mean', ascending=False)
    results['by_area'] = area_stats.to_dict('index')

    if 'category' in df.columns:
        cat_stats = df.groupby('category')['ingredient_count'].agg(['mean', 'std', 'count'])
        cat_stats = cat_stats.sort_values('mean', ascending=False)
        results['by_category'] = cat_stats.to_dict('index')

    return results


def analyze_cocktails():
    """
    Analyzes cocktails data:
    - Point-biserial correlation: is_alcoholic vs ingredient_count
    - Summary statistics
    """
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id, name, category, glass, is_alcoholic, ingredient_count
        FROM cocktails
        WHERE sampled = 1 AND ingredient_count IS NOT NULL
    """, conn)
    conn.close()

    results = {
        'name': 'TheCocktailDB',
        'sample_size': len(df),
        'analyses': []
    }

    if len(df) < 5:
        results['error'] = 'Insufficient data for analysis'
        return results

    results['ingredient_stats'] = {
        'mean': df['ingredient_count'].mean(),
        'std': df['ingredient_count'].std(),
        'min': df['ingredient_count'].min(),
        'max': df['ingredient_count'].max()
    }

    if df['is_alcoholic'].nunique() == 2:
        corr, p_value = pointbiserialr(df['is_alcoholic'], df['ingredient_count'])

        results['analyses'].append({
            'name': 'Alcoholic Status vs Ingredient Count',
            'type': 'Point-Biserial Correlation',
            'correlation': corr,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'interpretation': _interpret_correlation(corr)
        })

    alc_stats = df.groupby('is_alcoholic')['ingredient_count'].agg(['mean', 'std', 'count'])
    alc_stats.index = ['Non-Alcoholic', 'Alcoholic']
    results['by_alcoholic'] = alc_stats.to_dict('index')

    if df['glass'].nunique() > 1:
        glass_stats = df.groupby('glass')['ingredient_count'].agg(['mean', 'count'])
        glass_stats = glass_stats.sort_values('mean', ascending=False)
        results['by_glass'] = glass_stats.head(10).to_dict('index')

    return results


def analyze_products():
    """
    Analyzes products data:
    - Spearman correlation: energy_kcal vs nutrition_grade_numeric
    - Linear regression: predict grade from calories
    """
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id, name, brand, nutrition_grade, nutrition_grade_numeric, energy_kcal
        FROM products
        WHERE sampled = 1
          AND nutrition_grade_numeric IS NOT NULL
          AND energy_kcal IS NOT NULL
    """, conn)
    conn.close()

    results = {
        'name': 'Open Food Facts',
        'sample_size': len(df),
        'analyses': []
    }

    if len(df) < 5:
        results['error'] = 'Insufficient data for analysis'
        return results

    results['calorie_stats'] = {
        'mean': df['energy_kcal'].mean(),
        'std': df['energy_kcal'].std(),
        'min': df['energy_kcal'].min(),
        'max': df['energy_kcal'].max()
    }

    corr, p_value = spearmanr(df['energy_kcal'], df['nutrition_grade_numeric'])

    results['analyses'].append({
        'name': 'Calories vs Nutrition Grade',
        'type': 'Spearman Correlation',
        'correlation': corr,
        'p_value': p_value,
        'significant': p_value < 0.05,
        'interpretation': _interpret_correlation(corr)
    })

    slope, intercept, r_value, p_reg, std_err = stats.linregress(
        df['energy_kcal'], df['nutrition_grade_numeric']
    )

    results['analyses'].append({
        'name': 'Linear Regression: Calories -> Grade',
        'type': 'Linear Regression',
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value ** 2,
        'p_value': p_reg,
        'std_error': std_err,
        'equation': f"grade = {slope:.6f} * kcal + {intercept:.2f}"
    })

    grade_stats = df.groupby('nutrition_grade')['energy_kcal'].agg(['mean', 'std', 'count'])
    grade_order = ['a', 'b', 'c', 'd', 'e']
    grade_stats = grade_stats.reindex([g for g in grade_order if g in grade_stats.index])
    results['by_grade'] = grade_stats.to_dict('index')

    return results


def analyze_breweries():
    """
    Analyzes breweries data:
    - Chi-square test: brewery_type vs has_website
    - Geographic analysis: latitude distribution by type
    """
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT b.id, b.name, bt.name as brewery_type, b.state, b.latitude,
               b.longitude, b.has_website
        FROM breweries b
        LEFT JOIN brewery_types bt ON b.type_id = bt.id
        WHERE b.sampled = 1
    """, conn)
    conn.close()

    results = {
        'name': 'Open Brewery DB',
        'sample_size': len(df),
        'analyses': []
    }

    if len(df) < 5:
        results['error'] = 'Insufficient data for analysis'
        return results

    if df['brewery_type'].nunique() > 1 and df['has_website'].nunique() == 2:
        contingency = pd.crosstab(df['brewery_type'], df['has_website'])
        chi2, p_value, dof, expected = chi2_contingency(contingency)

        results['analyses'].append({
            'name': 'Brewery Type vs Website Presence',
            'type': 'Chi-Square Test',
            'chi2_statistic': chi2,
            'p_value': p_value,
            'degrees_of_freedom': dof,
            'significant': p_value < 0.05,
            'interpretation': 'Type and website presence are associated' if p_value < 0.05 else 'No significant association'
        })

    type_website = df.groupby('brewery_type').agg({
        'has_website': ['sum', 'count']
    })
    type_website.columns = ['with_website', 'total']
    type_website['percentage'] = (type_website['with_website'] / type_website['total'] * 100).round(1)
    type_website = type_website.sort_values('percentage', ascending=False)
    results['website_by_type'] = type_website.to_dict('index')

    df_geo = df[df['latitude'].notna()]
    if len(df_geo) > 5:
        results['latitude_stats'] = {
            'mean': df_geo['latitude'].mean(),
            'std': df_geo['latitude'].std(),
            'min': df_geo['latitude'].min(),
            'max': df_geo['latitude'].max()
        }

        lat_by_type = df_geo.groupby('brewery_type')['latitude'].agg(['mean', 'std', 'count'])
        lat_by_type = lat_by_type.sort_values('mean', ascending=False)
        results['latitude_by_type'] = lat_by_type.to_dict('index')

    state_counts = df['state'].value_counts().head(15)
    results['by_state'] = state_counts.to_dict()

    return results


def run_all_analyses():
    """Runs all analyses and returns combined results."""
    return {
        'meals': analyze_meals(),
        'cocktails': analyze_cocktails(),
        'products': analyze_products(),
        'breweries': analyze_breweries()
    }


def format_analysis_report(results, seed=None, sample_size=None):
    """Formats analysis results into a readable report."""
    lines = []
    lines.append("=" * 70)
    lines.append("STATISTICAL ANALYSIS RESULTS")
    if seed is not None:
        lines.append(f"Random Seed: {seed} | Target Sample Size: {sample_size} per API")
    lines.append("=" * 70)
    lines.append("")

    for key, data in results.items():
        lines.append(f"{data['name'].upper()}")
        lines.append("-" * 50)
        lines.append(f"Sample size: {data['sample_size']} items")
        lines.append("")

        if 'error' in data:
            lines.append(f"Error: {data['error']}")
            lines.append("")
            continue

        if 'ingredient_stats' in data:
            stats_data = data['ingredient_stats']
            lines.append(f"Ingredient Count: mean={stats_data['mean']:.1f}, "
                        f"std={stats_data['std']:.1f}, "
                        f"range=[{stats_data['min']}-{stats_data['max']}]")

        if 'calorie_stats' in data:
            stats_data = data['calorie_stats']
            lines.append(f"Calories (kcal/100g): mean={stats_data['mean']:.1f}, "
                        f"std={stats_data['std']:.1f}, "
                        f"range=[{stats_data['min']:.0f}-{stats_data['max']:.0f}]")

        lines.append("")

        for analysis in data.get('analyses', []):
            lines.append(f"  {analysis['name']} ({analysis['type']})")

            if 'correlation' in analysis:
                sig = "*" if analysis['significant'] else ""
                lines.append(f"    r = {analysis['correlation']:.3f}, "
                           f"p = {_format_p_value(analysis['p_value'])}{sig}")
                lines.append(f"    Interpretation: {analysis['interpretation']}")

            if 'chi2_statistic' in analysis:
                sig = "*" if analysis['significant'] else ""
                lines.append(f"    chi2 = {analysis['chi2_statistic']:.2f}, "
                           f"df = {analysis['degrees_of_freedom']}, "
                           f"p = {_format_p_value(analysis['p_value'])}{sig}")
                lines.append(f"    Interpretation: {analysis['interpretation']}")

            if 'r_squared' in analysis:
                lines.append(f"    R-squared = {analysis['r_squared']:.3f}")
                lines.append(f"    Equation: {analysis['equation']}")

            lines.append("")

        lines.append("")

    lines.append("* indicates significance at p < 0.05")
    lines.append("")

    return "\n".join(lines)
