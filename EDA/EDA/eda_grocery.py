import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set visual styling for modern dark theme
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'figure.facecolor': '#111827',  # Slate-900
    'axes.facecolor': '#1f2937',    # Slate-800
    'text.color': '#f9fafb',        # Slate-50
    'axes.labelcolor': '#d1d5db',   # Slate-300
    'xtick.color': '#9ca3af',       # Slate-400
    'ytick.color': '#9ca3af',       # Slate-400
    'grid.color': '#374151',        # Slate-700
    'axes.edgecolor': '#4b5563',    # Slate-600
    'patch.edgecolor': '#374151'
})

# Define paths
eda_dir = r"d:\SEMESTER 6\Studio-Based Project\EDA"
output_dir = r"d:\SEMESTER 6\Studio-Based Project\assets"
os.makedirs(output_dir, exist_ok=True)

csv_file = os.path.join(eda_dir, "Grocery_and_Gourmet_Food_cleaned.csv")
color = "#10b981"  # Emerald
display_name = "Grocery & Gourmet Food"

print(f"\n==================================================")
print(f"      LOADING {display_name.upper()} DATASET...")
print(f"==================================================")

if not os.path.exists(csv_file):
    raise FileNotFoundError(f"Dataset not found at {csv_file}")

df = pd.read_csv(csv_file, low_memory=False)

# Preprocessing
df['average_rating'] = pd.to_numeric(df['average_rating'], errors='coerce')
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['rating_number'] = pd.to_numeric(df['rating_number'], errors='coerce')
df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
df['title_len'] = df['title'].astype(str).str.len()
df['desc_len'] = df['description'].astype(str).str.len()

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

df['subcategory'] = df['categories'].apply(parse_subcategory)

# Calculate stats for terminal output
total_rows = len(df)
mean_rating = df['average_rating'].mean()
std_rating = df['average_rating'].std()
median_price = df['price'].median()
price_populated_pct = (df['price'].notnull().sum() / len(df)) * 100
mean_completeness = (100 - df.isnull().sum().mean() / len(df) * 100)

print(f"📊 Dataset Size: {total_rows:,} products")
print(f"⭐ Average Rating: {mean_rating:.2f} Stars (Std Dev: {std_rating:.3f})")
if not np.isnan(median_price):
    print(f"💵 Median Price: ${median_price:.2f} (Price Populated: {price_populated_pct:.1f}%)")
else:
    print(f"💵 Median Price: N/A (Price Populated: 0%)")
print(f"🛡️ Overall Catalog Completeness: {mean_completeness:.1f}%")

print(f"\n--------------------------------------------------")
print(f"TOP BRANDS BY CATALOG VOLUME:")
top_stores = df['store'].value_counts().head(5)
for brand, count in top_stores.items():
    print(f"  • {brand}: {count:,} items")

print(f"\n--------------------------------------------------")
print(f"GENERATING HIGH-RESOLUTION PLOTS...")

# ----------------------------------------------------
# Graph 1: Rating Distribution (Histogram with KDE)
# ----------------------------------------------------
print("  [1/7] Creating Rating Distribution plot...")
fig1 = plt.figure(1, figsize=(10, 6))
sns.histplot(df['average_rating'].dropna(), bins=15, kde=True, color=color, edgecolor='#111827', linewidth=1.5)
plt.title(f"Average Rating Distribution - {display_name}", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("Average Rating (Stars)", fontsize=12)
plt.ylabel("Number of Products", fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "Grocery_and_Gourmet_Food_rating_dist.png"), dpi=150, facecolor='#111827')

# ----------------------------------------------------
# Graph 2: Price Distribution (Log Scale Histogram + Box Plot)
# ----------------------------------------------------
print("  [2/7] Creating Price Distribution plot...")
fig2, (ax_box, ax_hist) = plt.subplots(2, 1, sharex=True, gridspec_kw={"height_ratios": (.15, .85)}, figsize=(10, 6))
prices = df['price'].dropna()
if len(prices) > 0:
    sns.boxplot(x=prices, ax=ax_box, color=color, orient="h", width=0.5, fliersize=4)
    sns.histplot(x=prices, ax=ax_hist, color=color, bins=30, kde=False, edgecolor='#111827')
    ax_hist.set_xscale('log')
    ax_box.set(yticks=[])
    sns.despine(ax=ax_box, left=True, bottom=True)
    sns.despine(ax=ax_hist)
    ax_box.set_title(f"Price Distribution (Log Scale) - {display_name}", fontsize=14, fontweight='bold', pad=15)
    ax_hist.set_xlabel("Price ($) - Log Scale", fontsize=12)
    ax_hist.set_ylabel("Count", fontsize=12)
else:
    ax_hist.text(0.5, 0.5, "No Price Data Available", ha='center', va='center', fontsize=14, color='#9ca3af')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "Grocery_and_Gourmet_Food_price_dist.png"), dpi=150, facecolor='#111827')

# ----------------------------------------------------
# Graph 3: Review Volume vs. Average Rating (Hexbin/Density Scatter)
# ----------------------------------------------------
print("  [3/7] Creating Review Volume vs. Rating density plot...")
fig3 = plt.figure(3, figsize=(10, 6))
df_scatter = df[['rating_number', 'average_rating']].dropna().copy()
if len(df_scatter) > 0:
    df_scatter['log_rating_volume'] = np.log10(df_scatter['rating_number'] + 1)
    plt.hexbin(df_scatter['average_rating'], df_scatter['log_rating_volume'], gridsize=25, cmap=sns.dark_palette(color, as_cmap=True), mincnt=1)
    cb = plt.colorbar(label='Product Density')
    cb.ax.yaxis.label.set_color('#d1d5db')
    cb.ax.tick_params(colors='#9ca3af')
    plt.title(f"Review Volume vs. Average Rating - {display_name}", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Average Rating (Stars)", fontsize=12)
    plt.ylabel("Review Volume (Log10 scale)", fontsize=12)
else:
    plt.text(0.5, 0.5, "No Volume Data Available", ha='center', va='center', fontsize=14, color='#9ca3af')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "Grocery_and_Gourmet_Food_volume_vs_rating.png"), dpi=150, facecolor='#111827')

# ----------------------------------------------------
# Graph 4: Numeric & Meta Correlation Heatmap
# ----------------------------------------------------
print("  [4/7] Creating Numeric & Meta Correlation heatmap...")
fig4 = plt.figure(4, figsize=(10, 6))
corr_cols = ['average_rating', 'rating_number', 'price', 'timestamp', 'title_len', 'desc_len']
available_corr = [c for c in corr_cols if c in df.columns]
corr_matrix = df[available_corr].dropna().corr()
if not corr_matrix.empty:
    sns.heatmap(corr_matrix, annot=True, cmap=sns.diverging_palette(220, 20, as_cmap=True), 
                vmin=-1, vmax=1, center=0, square=True, linewidths=.5, cbar_kws={"shrink": .8},
                annot_kws={"size": 10, "weight": "bold"})
    plt.title(f"Numeric & Meta Correlation Matrix - {display_name}", fontsize=14, fontweight='bold', pad=15)
else:
    plt.text(0.5, 0.5, "No correlation matrix possible", ha='center', va='center', fontsize=14, color='#9ca3af')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "Grocery_and_Gourmet_Food_correlation_heatmap.png"), dpi=150, facecolor='#111827')

# ----------------------------------------------------
# Graph 5: Store Category Performance Heatmap (Pivot Heatmap)
# ----------------------------------------------------
print("  [5/7] Creating Brand Category Performance heatmap...")
fig5 = plt.figure(5, figsize=(10, 6))
top_stores = df['store'].value_counts().head(10).index
pivot_col = 'subcategory'
top_pivots = df[pivot_col].value_counts().head(6).index

df_pivot = df[df['store'].isin(top_stores) & df[pivot_col].isin(top_pivots)]
if len(df_pivot) > 0:
    pivot_table = df_pivot.pivot_table(index='store', columns=pivot_col, values='average_rating', aggfunc='mean')
    sns.heatmap(pivot_table, annot=True, fmt=".2f", cmap=sns.light_palette(color, as_cmap=True),
                linewidths=.5, cbar_kws={"label": "Mean Rating"})
    plt.title(f"Store vs. Subcategory Rating Heatmap - {display_name}", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Subcategory", fontsize=12)
    plt.ylabel("Store / Brand", fontsize=12)
    plt.xticks(rotation=15, ha='right')
else:
    plt.text(0.5, 0.5, "No Pivot Data Available", ha='center', va='center', fontsize=14, color='#9ca3af')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "Grocery_and_Gourmet_Food_pivot_heatmap.png"), dpi=150, facecolor='#111827')

# ----------------------------------------------------
# Graph 6: Temporal Review Activity (Line Chart)
# ----------------------------------------------------
print("  [6/7] Creating Temporal Review & Catalog Growth plot...")
fig6 = plt.figure(6, figsize=(10, 6))
df_time = df[['timestamp', 'average_rating']].dropna().copy()
if len(df_time) > 0:
    df_time['datetime'] = pd.to_datetime(df_time['timestamp'] / 1000, unit='s', errors='coerce')
    df_time['year'] = df_time['datetime'].dt.year
    yearly = df_time.groupby('year').agg(
        count=('average_rating', 'count'),
        avg_rating=('average_rating', 'mean')
    ).reset_index()
    yearly = yearly[(yearly['year'] >= 2005) & (yearly['year'] <= 2024)]
    
    ax1 = fig6.add_subplot(111)
    ax2 = ax1.twinx()
    
    sns.lineplot(data=yearly, x='year', y='count', ax=ax1, color=color, marker='o', linewidth=2.5, label='Product Count')
    sns.lineplot(data=yearly, x='year', y='avg_rating', ax=ax2, color='#f59e0b', marker='s', linewidth=2, linestyle='--', label='Avg Rating')
    
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Number of Catalog Products', color=color, fontsize=12)
    ax2.set_ylabel('Average Rating (Stars)', color='#f59e0b', fontsize=12)
    
    ax1.tick_params(axis='y', labelcolor=color)
    ax2.tick_params(axis='y', labelcolor='#f59e0b')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', facecolor='#1f2937', edgecolor='#374151')
    plt.title(f"Temporal Review & Catalog Growth - {display_name}", fontsize=14, fontweight='bold', pad=15)
    ax1.set_xticks(yearly['year'].astype(int).unique())
    ax1.set_xticklabels(yearly['year'].astype(int).unique(), rotation=45)
else:
    plt.text(0.5, 0.5, "No Temporal Data Available", ha='center', va='center', fontsize=14, color='#9ca3af')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "Grocery_and_Gourmet_Food_temporal_line.png"), dpi=150, facecolor='#111827')

# ----------------------------------------------------
# Graph 7: Data Completeness Matrix (Horizontal Bar Chart)
# ----------------------------------------------------
print("  [7/7] Creating Data Completeness matrix...")
fig7 = plt.figure(7, figsize=(10, 6))
missing_pct = (100 - df.isnull().sum() / len(df) * 100).round(2).sort_values(ascending=True)
colors = sns.light_palette(color, n_colors=len(missing_pct))
missing_pct.plot(kind='barh', color=colors, edgecolor='#111827', width=0.7)
plt.title(f"Data Completeness (Percentage Populated) - {display_name}", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("Percentage Populated (%)", fontsize=12)
plt.ylabel("Data Feature Column", fontsize=12)
plt.xlim(0, 105)
for idx, val in enumerate(missing_pct):
    plt.text(val + 1, idx, f"{val}%", va='center', fontsize=9, fontweight='bold', color='#d1d5db')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "Grocery_and_Gourmet_Food_completeness.png"), dpi=150, facecolor='#111827')

print(f"\n==================================================")
print(f"🎉 SUCCESS: All 7 visual plots saved to:")
print(f"   {output_dir}")
print(f"==================================================")
print("Opening interactive plotting windows. Please review...")
plt.show()  # Display all 7 plots together!
