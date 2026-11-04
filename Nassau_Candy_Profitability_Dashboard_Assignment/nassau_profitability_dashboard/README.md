# Nassau Candy Profitability Intelligence Dashboard

An interactive Streamlit dashboard for product profitability, division performance, margin-risk screening, Pareto concentration, and factory/product association analysis.

## Included files
- `app.py` — Streamlit application.
- `dataset.csv` — supplied assignment dataset.
- `requirements.txt` — Python dependencies.
- `ASSIGNMENT_REPORT.docx` — assignment-ready report (if included in the package).

## Run on Windows
1. Install Python 3.10 or later.
2. Extract the project ZIP.
3. Open Command Prompt in the project folder.
4. Create and activate a virtual environment (recommended):
   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   ```
5. Install packages:
   ```bat
   pip install -r requirements.txt
   ```
6. Start the app:
   ```bat
   streamlit run app.py
   ```
7. Streamlit opens the dashboard in your browser. The included `dataset.csv` loads by default. You can upload another CSV or Excel file from the sidebar.

## Modules
1. Executive Overview
2. Product Profitability
3. Division Performance
4. Cost & Margin Diagnostics
5. Profit Concentration
6. Factory Insights
7. Data Quality & Export

## Metric definitions
- Gross margin (%) = total gross profit / total sales × 100.
- Profit per unit = total gross profit / total units.
- Revenue contribution (%) = product sales / filtered sales × 100.
- Profit contribution (%) = product gross profit / filtered gross profit × 100.
- Margin risk = margin below the user-selected threshold or negative gross profit.
- Pareto analysis ranks products by revenue or gross profit and calculates cumulative contribution.

## Scope and data-quality caveats
The supplied file has 10,194 rows and 18 columns. In the supplied data, Order Dates run from January 2024 through December 2025, while Ship Dates run from June 2026 through June 2030. This creates unusually large order-to-ship intervals, so the application does not present shipping lead time as reliable operational performance. The dataset has no actual route, promised delivery date, transit status, or delay indicator.

Factory coordinates and product-to-factory relationships are provided as static assignment mappings. Factory totals are derived by aggregating mapped products; they do not prove that a particular order physically shipped from that factory. Products not matching the mapping are reported as unmapped.

The app validates required columns and numeric/date fields, flags suspect records, and excludes records with invalid core analysis values from the analysis while retaining raw rows for review. Gross Profit is checked against Sales minus Cost with a tolerance of $0.02.
