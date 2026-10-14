from pathlib import Path
import pandas as pd
from helpers import order_metrics

DATA_DIR = Path(__file__).parent / 'data'


def build_overview():
    """Load only the columns the Business Overview page needs and compute its numbers once."""
    cln_sales = pd.read_parquet(
        DATA_DIR / 'cln_sales.parquet',
        columns=['Invoice', 'Quantity', 'Revenue', 'Year', 'Month', 'MonthName', 'YearMonth'])
    sales = pd.read_parquet(DATA_DIR / 'sales.parquet', columns=['Invoice', 'YearMonth'])
    cncld = pd.read_parquet(DATA_DIR / 'cncld.parquet', columns=['Invoice', 'YearMonth'])

    # KPIs
    order_values = cln_sales.groupby('Invoice')['Revenue'].sum()
    kpis = {
        'total_revenue': cln_sales['Revenue'].sum(),
        'total_orders': cln_sales['Invoice'].nunique(),
        'total_units_sold': cln_sales['Quantity'].sum(),
        'avg_order_value': order_values.mean(),
        'med_order_value': order_values.median(),
    }

    # Revenue trends
    monthly_revenue = cln_sales.groupby('YearMonth')['Revenue'].sum().reset_index()
    yoy_data = (cln_sales.groupby(['Year', 'Month', 'MonthName'])['Revenue'].sum()
                .reset_index().sort_values('Month'))

    # Cancellation rate (completed orders come from `sales`, as in the notebook)
    cncld_by_month = cncld.groupby('YearMonth')['Invoice'].nunique().reset_index(name='Cancelled_Orders')
    sales_by_month = sales.groupby('YearMonth')['Invoice'].nunique().reset_index(name='Completed_Orders')
    cancellation_trend = pd.merge(sales_by_month, cncld_by_month, on='YearMonth', how='outer').fillna(0)
    cancellation_trend['All_Orders'] = cancellation_trend['Completed_Orders'] + cancellation_trend['Cancelled_Orders']
    cancellation_trend['Cancellation_Rate_%'] = cancellation_trend['Cancelled_Orders'] / cancellation_trend['All_Orders'] * 100
    cancellation_trend = cancellation_trend.sort_values('YearMonth')

    return {
        'kpis': kpis,
        'monthly_revenue': monthly_revenue,
        'yoy_data': yoy_data,
        'cancellation_trend': cancellation_trend,
    }


def build_products_markets():
    """Numbers for the Products & Markets page."""
    cln_sales = pd.read_parquet(
        DATA_DIR / 'cln_sales.parquet',
        columns=['StockCode', 'Description', 'Quantity', 'Revenue', 'Country'])

    # Top 10 products
    by_product = cln_sales.groupby(['StockCode', 'Description'])[['Revenue', 'Quantity']].sum().reset_index()
    top10_by_rev = by_product.sort_values('Revenue', ascending=False).head(10)
    top10_by_units = by_product.sort_values('Quantity', ascending=False).head(10)

    # Pareto: cumulative revenue share by product rank
    product_revenue = (by_product[['StockCode', 'Description', 'Revenue']]
                       .sort_values('Revenue', ascending=False).reset_index(drop=True))
    product_revenue['Rank'] = product_revenue.index + 1
    product_revenue['Revenue_%'] = product_revenue['Revenue'] / product_revenue['Revenue'].sum() * 100
    product_revenue['Cumulative_%'] = product_revenue['Revenue_%'].cumsum()
    n_products = len(product_revenue)
    n_products_80pct = int((product_revenue['Cumulative_%'] < 80).sum() + 1)

    # Revenue by country
    rev_by_country = (cln_sales.groupby('Country')['Revenue'].sum()
                      .sort_values(ascending=False).reset_index())
    intl_rev = rev_by_country[rev_by_country['Country'] != 'United Kingdom'].reset_index(drop=True)
    tot_uk_rev = rev_by_country.loc[rev_by_country['Country'] == 'United Kingdom', 'Revenue'].iloc[0]
    tot_intl_rev = intl_rev['Revenue'].sum()
    uk_pct = tot_uk_rev / (tot_uk_rev + tot_intl_rev) * 100

    return {
        'top10_by_rev': top10_by_rev,
        'top10_by_units': top10_by_units,
        'product_revenue': product_revenue,
        'n_products': n_products,
        'n_products_80pct': n_products_80pct,
        'pct_of_catalog': n_products_80pct / n_products * 100,
        'intl_rev': intl_rev,
        'tot_uk_rev': tot_uk_rev,
        'tot_intl_rev': tot_intl_rev,
        'uk_pct': uk_pct,
        'intl_pct': 100 - uk_pct,
    }
def build_customers():
    """Numbers for the Customers & Orders page."""
    cols = ['Invoice', 'Quantity', 'Revenue', 'StockCode', 'Customer ID', 'Country']
    known = pd.read_parquet(DATA_DIR / 'custID_sales.parquet', columns=cols)
    noid = pd.read_parquet(DATA_DIR / 'no_custID_sales.parquet', columns=cols)

    known_orders = order_metrics(known)
    noid_orders = order_metrics(noid)
    all_orders = pd.concat([known_orders, noid_orders]).reset_index(drop=True)

    # Known vs. No Customer ID: share of revenue and orders
    known_rev, noid_rev = known['Revenue'].sum(), noid['Revenue'].sum()
    total_revenue = known_rev + noid_rev
    total_orders = len(all_orders)
    split_df = pd.DataFrame({
        'Metric': ['Revenue', 'Revenue', 'Orders', 'Orders'],
        'Customer_Type': ['Known', 'No Customer ID', 'Known', 'No Customer ID'],
        'Percent': [known_rev / total_revenue * 100, noid_rev / total_revenue * 100,
                    len(known_orders) / total_orders * 100, len(noid_orders) / total_orders * 100],
    })

    # Comparison table (medians lead, means alongside)
    labels = {'order_value': ('Order Value', '£{:,.0f}'),
              'units_per_order': ('Units per Order', '{:,.0f}'),
              'products_per_order': ('Distinct Products per Order', '{:,.1f}')}
    comparison = pd.DataFrame([{
        'Metric': label,
        'No ID (median)': fmt.format(noid_orders[col].median()),
        'Known (median)': fmt.format(known_orders[col].median()),
        'No ID (mean)': fmt.format(noid_orders[col].mean()),
        'Known (mean)': fmt.format(known_orders[col].mean()),
    } for col, (label, fmt) in labels.items()])

    # Top customers and concentration
    customer_rev = (known.groupby('Customer ID')
                    .agg(Revenue=('Revenue', 'sum'), Orders=('Invoice', 'nunique'),
                         Country=('Country', 'first'))
                    .sort_values('Revenue', ascending=False).reset_index())
    customer_rev['AOV'] = customer_rev['Revenue'] / customer_rev['Orders']
    customer_rev['Pct_of_Known_Rev'] = customer_rev['Revenue'] / known_rev * 100
    customer_rev['Cumulative_%'] = customer_rev['Pct_of_Known_Rev'].cumsum()
    n_customers = len(customer_rev)
    n_top_1pct = max(1, int(n_customers * 0.01))
    n_to_80 = int((customer_rev['Cumulative_%'] < 80).sum() + 1)
    top10 = customer_rev.head(10).copy()
    top10['Customer'] = 'ID ' + top10['Customer ID'].astype(str)

    # Repeat purchases
    orders_per_cust = known.groupby('Customer ID')['Invoice'].nunique()
    order_buckets = orders_per_cust.clip(upper=10).value_counts().sort_index().reset_index()
    order_buckets.columns = ['Orders', 'Customers']
    order_buckets['Orders'] = order_buckets['Orders'].astype(str).replace({'10': '10+'})

    return {
        'split_df': split_df,
        'comparison': comparison,
        'orders': all_orders,
        'top10': top10,
        'order_buckets': order_buckets,
        'n_customers': n_customers,
        'noid_rev_pct': noid_rev / total_revenue * 100,
        'repeat_rate': (orders_per_cust > 1).mean() * 100,
        'n_repeat': int((orders_per_cust > 1).sum()),
        'median_orders': orders_per_cust.median(),
        'mean_orders': orders_per_cust.mean(),
        'top10_known_pct': top10['Pct_of_Known_Rev'].sum(),
        'top10_total_pct': top10['Revenue'].sum() / total_revenue * 100,
        'top1pct_share': customer_rev.head(n_top_1pct)['Pct_of_Known_Rev'].sum(),
        'n_top_1pct': n_top_1pct,
        'n_to_80': n_to_80,
        'n_to_80_pct': n_to_80 / n_customers * 100,
    }    