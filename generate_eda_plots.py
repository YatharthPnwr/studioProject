"""
Generate EDA plots for all 4 Amazon dataset categories.
Saves PNGs to public/eda/ for Next.js to serve statically.
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(BASE_DIR, "amazon_datasets")
OUTPUT_DIR = os.path.join(BASE_DIR, "public", "eda")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dark theme rcParams matching the EDA scripts
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'figure.facecolor': '#111827',
    'axes.facecolor': '#1f2937',
    'text.color': '#f9fafb',
    'axes.labelcolor': '#d1d5db',
    'xtick.color': '#9ca3af',
    'ytick.color': '#9ca3af',
    'grid.color': '#374151',
    'axes.edgecolor': '#4b5563',
    'patch.edgecolor': '#374151',
})

CATEGORIES = [
    {
        "csv": "Electronics_cleaned.csv",
        "prefix": "Electronics",
        "display_name": "Electronics",
        "color": "#6366f1",
        "pivot_col": "main_category",
        "nrows": 200000,
    },
    {
        "csv": "Grocery_and_Gourmet_Food_cleaned.csv",
        "prefix": "Grocery_and_Gourmet_Food",
        "display_name": "Grocery & Gourmet Food",
        "color": "#10b981",
        "pivot_col": "subcategory",
        "nrows": None,
    },
    {
        "csv": "Health_Household_cleaned.csv",
        "prefix": "Health_Household",
        "display_name": "Health & Household",
        "color": "#14b8a6",
        "pivot_col": "subcategory",
        "nrows": None,
    },
    {
        "csv": "Health_and_Personal_Care_cleaned.csv",
        "prefix": "Health_and_Personal_Care",
        "display_name": "Health & Personal Care",
        "color": "#ec4899",
        "pivot_col": "subcategory",
        "nrows": None,
    },
]


def parse_subcategory(cat_str):
    if not isinstance(cat_str, str):
        return "Unknown"
    try:
        cleaned = cat_str.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
        parts = [p.strip() for p in cleaned.split(",") if p.strip()]
        if len(parts) > 1:
            return parts[1]
        elif len(parts) == 1:
            return parts[0]
        return "Unknown"
    except Exception:
        return "Unknown"


def save(fig, path):
    fig.savefig(path, dpi=150, facecolor='#111827', bbox_inches='tight')
    plt.close(fig)
    print(f"    Saved: {os.path.basename(path)}")


def generate_plots(cat):
    csv_path = os.path.join(DATASETS_DIR, cat["csv"])
    if not os.path.exists(csv_path):
        print(f"  [SKIP] {csv_path} not found")
        return

    prefix = cat["prefix"]
    display_name = cat["display_name"]
    color = cat["color"]
    pivot_col = cat["pivot_col"]

    print(f"\n{'='*52}")
    print(f"  {display_name}")
    print(f"{'='*52}")

    kwargs = {"low_memory": False, "escapechar": "\\"}
    if cat["nrows"]:
        kwargs["nrows"] = cat["nrows"]
    df = pd.read_csv(csv_path, **kwargs)

    # Preprocess
    df['average_rating'] = pd.to_numeric(df['average_rating'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['rating_number'] = pd.to_numeric(df['rating_number'], errors='coerce')
    df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
    df['title_len'] = df['title'].astype(str).str.len()
    df['desc_len'] = df['description'].astype(str).str.len()
    if pivot_col == "subcategory" and 'categories' in df.columns:
        df['subcategory'] = df['categories'].apply(parse_subcategory)

    # ── Graph 1: Rating Distribution ─────────────────────────
    print("  [1/7] Rating Distribution")
    fig = plt.figure(figsize=(10, 6))
    sns.histplot(df['average_rating'].dropna(), bins=15, kde=True, color=color,
                 edgecolor='#111827', linewidth=1.5)
    plt.title(f"Average Rating Distribution — {display_name}", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Average Rating (Stars)", fontsize=12)
    plt.ylabel("Number of Products", fontsize=12)
    plt.tight_layout()
    save(fig, os.path.join(OUTPUT_DIR, f"{prefix}_rating_dist.png"))

    # ── Graph 2: Price Distribution ───────────────────────────
    print("  [2/7] Price Distribution")
    fig, (ax_box, ax_hist) = plt.subplots(
        2, 1, sharex=True, gridspec_kw={"height_ratios": (.15, .85)}, figsize=(10, 6))
    prices = df['price'].dropna()
    if len(prices) > 0:
        sns.boxplot(x=prices, ax=ax_box, color=color, orient="h", width=0.5, fliersize=4)
        sns.histplot(x=prices, ax=ax_hist, color=color, bins=30, kde=False, edgecolor='#111827')
        ax_hist.set_xscale('log')
        ax_box.set(yticks=[])
        sns.despine(ax=ax_box, left=True, bottom=True)
        sns.despine(ax=ax_hist)
        ax_box.set_title(f"Price Distribution (Log Scale) — {display_name}", fontsize=14, fontweight='bold', pad=15)
        ax_hist.set_xlabel("Price ($) — Log Scale", fontsize=12)
        ax_hist.set_ylabel("Count", fontsize=12)
    else:
        ax_hist.text(0.5, 0.5, "No Price Data Available", ha='center', va='center',
                     fontsize=14, color='#9ca3af')
    plt.tight_layout()
    save(fig, os.path.join(OUTPUT_DIR, f"{prefix}_price_dist.png"))

    # ── Graph 3: Review Volume vs Rating ─────────────────────
    print("  [3/7] Review Volume vs Rating")
    fig = plt.figure(figsize=(10, 6))
    df_scatter = df[['rating_number', 'average_rating']].dropna().copy()
    if len(df_scatter) > 0:
        df_scatter['log_rating_volume'] = np.log10(df_scatter['rating_number'] + 1)
        plt.hexbin(df_scatter['average_rating'], df_scatter['log_rating_volume'],
                   gridsize=25, cmap=sns.dark_palette(color, as_cmap=True), mincnt=1)
        cb = plt.colorbar(label='Product Density')
        cb.ax.yaxis.label.set_color('#d1d5db')
        cb.ax.tick_params(colors='#9ca3af')
        plt.title(f"Review Volume vs. Average Rating — {display_name}", fontsize=14, fontweight='bold', pad=15)
        plt.xlabel("Average Rating (Stars)", fontsize=12)
        plt.ylabel("Review Volume (Log10 scale)", fontsize=12)
    else:
        plt.text(0.5, 0.5, "No Volume Data Available", ha='center', va='center',
                 fontsize=14, color='#9ca3af')
    plt.tight_layout()
    save(fig, os.path.join(OUTPUT_DIR, f"{prefix}_volume_vs_rating.png"))

    # ── Graph 4: Correlation Heatmap ─────────────────────────
    print("  [4/7] Correlation Heatmap")
    fig = plt.figure(figsize=(10, 6))
    corr_cols = ['average_rating', 'rating_number', 'price', 'timestamp', 'title_len', 'desc_len']
    available_corr = [c for c in corr_cols if c in df.columns]
    corr_matrix = df[available_corr].dropna().corr()
    if not corr_matrix.empty:
        sns.heatmap(corr_matrix, annot=True, cmap=sns.diverging_palette(220, 20, as_cmap=True),
                    vmin=-1, vmax=1, center=0, square=True, linewidths=.5,
                    cbar_kws={"shrink": .8}, annot_kws={"size": 10, "weight": "bold"})
        plt.title(f"Numeric & Meta Correlation Matrix — {display_name}", fontsize=14, fontweight='bold', pad=15)
    else:
        plt.text(0.5, 0.5, "No correlation matrix possible", ha='center', va='center',
                 fontsize=14, color='#9ca3af')
    plt.tight_layout()
    save(fig, os.path.join(OUTPUT_DIR, f"{prefix}_correlation_heatmap.png"))

    # ── Graph 5: Store vs Category Heatmap ───────────────────
    print("  [5/7] Store vs Category Heatmap")
    fig = plt.figure(figsize=(10, 6))
    top_stores_idx = df['store'].value_counts().head(10).index
    top_pivots = df[pivot_col].value_counts().head(6).index
    df_pivot = df[df['store'].isin(top_stores_idx) & df[pivot_col].isin(top_pivots)]
    if len(df_pivot) > 0:
        pivot_table = df_pivot.pivot_table(
            index='store', columns=pivot_col, values='average_rating', aggfunc='mean')
        sns.heatmap(pivot_table, annot=True, fmt=".2f",
                    cmap=sns.light_palette(color, as_cmap=True),
                    linewidths=.5, cbar_kws={"label": "Mean Rating"})
        pivot_label = "Category" if pivot_col == "main_category" else "Subcategory"
        plt.title(f"Store vs. {pivot_label} Rating Heatmap — {display_name}", fontsize=14, fontweight='bold', pad=15)
        plt.xlabel(pivot_label, fontsize=12)
        plt.ylabel("Store / Brand", fontsize=12)
        plt.xticks(rotation=15, ha='right')
    else:
        plt.text(0.5, 0.5, "No Pivot Data Available", ha='center', va='center',
                 fontsize=14, color='#9ca3af')
    plt.tight_layout()
    save(fig, os.path.join(OUTPUT_DIR, f"{prefix}_pivot_heatmap.png"))

    # ── Graph 6: Temporal Catalog Growth ─────────────────────
    print("  [6/7] Temporal Catalog Growth")
    fig = plt.figure(figsize=(10, 6))
    df_time = df[['timestamp', 'average_rating']].dropna().copy()
    if len(df_time) > 0:
        df_time['datetime'] = pd.to_datetime(df_time['timestamp'] / 1000, unit='s', errors='coerce')
        df_time['year'] = df_time['datetime'].dt.year
        yearly_agg = df_time.groupby('year').agg(
            count=('average_rating', 'count'),
            avg_rating=('average_rating', 'mean')
        ).reset_index()
        yearly_agg = yearly_agg[(yearly_agg['year'] >= 2005) & (yearly_agg['year'] <= 2024)]

        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        sns.lineplot(data=yearly_agg, x='year', y='count', ax=ax1, color=color,
                     marker='o', linewidth=2.5, label='Product Count')
        sns.lineplot(data=yearly_agg, x='year', y='avg_rating', ax=ax2, color='#f59e0b',
                     marker='s', linewidth=2, linestyle='--', label='Avg Rating')
        ax1.set_xlabel('Year', fontsize=12)
        ax1.set_ylabel('Number of Catalog Products', color=color, fontsize=12)
        ax2.set_ylabel('Average Rating (Stars)', color='#f59e0b', fontsize=12)
        ax1.tick_params(axis='y', labelcolor=color)
        ax2.tick_params(axis='y', labelcolor='#f59e0b')
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left',
                   facecolor='#1f2937', edgecolor='#374151')
        plt.title(f"Temporal Review & Catalog Growth — {display_name}", fontsize=14, fontweight='bold', pad=15)
        ax1.set_xticks(yearly_agg['year'].astype(int).unique())
        ax1.set_xticklabels(yearly_agg['year'].astype(int).unique(), rotation=45)
    else:
        plt.text(0.5, 0.5, "No Temporal Data Available", ha='center', va='center',
                 fontsize=14, color='#9ca3af')
    plt.tight_layout()
    save(fig, os.path.join(OUTPUT_DIR, f"{prefix}_temporal_line.png"))

    # ── Graph 7: Data Completeness ────────────────────────────
    print("  [7/7] Data Completeness")
    fig = plt.figure(figsize=(10, 6))
    missing_pct = (100 - df.isnull().sum() / len(df) * 100).round(2).sort_values(ascending=True)
    bar_colors = sns.light_palette(color, n_colors=len(missing_pct))
    missing_pct.plot(kind='barh', color=bar_colors, edgecolor='#111827', width=0.7)
    plt.title(f"Data Completeness (Percentage Populated) — {display_name}", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Percentage Populated (%)", fontsize=12)
    plt.ylabel("Data Feature Column", fontsize=12)
    plt.xlim(0, 105)
    for idx, val in enumerate(missing_pct):
        plt.text(val + 1, idx, f"{val}%", va='center', fontsize=9, fontweight='bold', color='#d1d5db')
    plt.tight_layout()
    save(fig, os.path.join(OUTPUT_DIR, f"{prefix}_completeness.png"))


if __name__ == "__main__":
    for cat in CATEGORIES:
        generate_plots(cat)
    print(f"\n✅ All plots saved to: {OUTPUT_DIR}")
