# Online Retail Sales Dashboard

An interactive Dash dashboard that analyses two years of UK online gift-retailer transactions (Online Retail II, Dec 2009 to 9 Dec 2011, £): revenue trends, product and market performance, and customer behaviour.

![Business Overview](images/overview.png)

## Key findings
- **Revenue:** £19.36M from 39,513 orders. The typical order is £301 (median), against a mean of £490. November is the peak month in both years (£1.45M in 2011, £1.43M in 2010); Dec 2011 is partial because the data ends on 9 Dec.
- **Cancellations:** 12-17% of monthly orders are cancelled; the average fell from 15.0% in 2010 to 13.9% in 2011.
- **Products:** 1,053 products (21.5% of the 4,895-product catalogue) account for 80% of revenue. No single product exceeds 1.7%.
- **Markets:** the UK accounts for 85.3% of revenue. Ireland and the Netherlands lead international sales.
- **Customers:** 72.3% of the 5,852 known customers placed more than one order, and the top 1% generate 31.3% of known-customer revenue.
- **Missing customer IDs:** these orders are 7.4% of orders but 13.3% of revenue. The typical one is smaller (median £184 vs. £303), but the average is higher because of a few very large invoices.

## Data cleaning
The cleaning notebook documents each decision, taking 1,067,371 raw rows down to 1,026,189:
- removed 34,335 duplicate rows
- removed 2,215 non-sale rows
- removed 4,627 rows with no description or a non-product code
- removed 5 line items from 3 orders identified as entry errors (£284,623, about 1.4% of revenue)
- standardised country names
- used a gross-sales convention, with cancelled invoices tracked separately

## Project structure
| File | Purpose |
|---|---|
| `RetailData_Cleaning.ipynb` | Cleans the raw Excel file and saves parquet files to `data/` |
| `RetailData_Analysis.ipynb` | Exploratory analysis with findings |
| `data_prep.py`, `helpers.py` | Loads the parquet files and computes the dashboard numbers |
| `charts.py`, `layouts.py` | Plotly figures and page layouts |
| `app.py` | Dash app |

## Run it locally
1. Download `online_retail_II.xlsx` from [Kaggle](https://www.kaggle.com/datasets/ozlemilgun/online-retail-dataset) and put it in `data/`.
2. Create and activate a virtual environment, then install the requirements:
```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
```
3. Run `RetailData_Cleaning.ipynb` top to bottom. It creates the parquet files the dashboard reads.
4. Start the dashboard and open the address it prints (usually http://127.0.0.1:8050):
```
   python app.py
```

## Tools
Python, pandas, Plotly, Dash, Dash Bootstrap Components.