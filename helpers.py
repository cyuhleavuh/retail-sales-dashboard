def order_metrics(df):
    """One row per order: value (£), total units, and distinct products."""
    return df.groupby('Invoice').agg(
        order_value=('Revenue', 'sum'),
        units_per_order=('Quantity', 'sum'),
        products_per_order=('StockCode', 'nunique'),
    )