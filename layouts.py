from dash import html, dcc
import dash_bootstrap_components as dbc

from charts import (monthly_revenue_fig, yoy_fig, cancellation_rate_fig,
                    top_products_fig, pareto_fig, intl_revenue_fig,
                    cust_split_fig, order_size_fig, order_buckets_fig, top_customers_fig)


def kpi_card(title, value, subtext=None):
    body = [html.P(title, className='text-muted mb-1'), html.H3(value, className='mb-0')]
    if subtext:
        body.append(html.Small(subtext, className='text-muted'))
    return dbc.Card(dbc.CardBody(body), className='shadow-sm h-100')


def chart_block(figure, caption):
    """A chart with its key finding underneath."""
    return html.Div([
        dcc.Graph(figure=figure),
        html.P(caption, className='text-muted small'),
    ])


def overview_layout(overview):
    k = overview['kpis']
    return html.Div([
        dbc.Row([
            dbc.Col(kpi_card('Total Revenue', f"£{k['total_revenue'] / 1e6:.2f}M"), md=3),
            dbc.Col(kpi_card('Total Orders', f"{k['total_orders']:,}"), md=3),
            dbc.Col(kpi_card('Units Sold', f"{k['total_units_sold'] / 1e6:.1f}M"), md=3),
            dbc.Col(kpi_card('Median Order Value', f"£{k['med_order_value']:,.0f}",
                             f"Mean £{k['avg_order_value']:,.0f}"), md=3),
        ], className='g-3 my-3'),

        dbc.Row(dbc.Col(chart_block(
            monthly_revenue_fig(overview['monthly_revenue']),
            'Revenue builds from September into a November peak (£1.45M in Nov 2011, £1.43M in Nov 2010). '
            'Dec 2011 is partial (data ends 9 Dec), so its low point is not a real drop.'))),

        dbc.Row([
            dbc.Col(chart_block(
                yoy_fig(overview['yoy_data']),
                'Jan-Nov 2011 is 1.7% above 2010: behind in Jan-Apr, ahead in May and Jul-Sep, '
                'roughly flat in Oct-Nov.'), md=6),
            dbc.Col(chart_block(
                cancellation_rate_fig(overview['cancellation_trend']),
                '12-17% of monthly orders are cancelled; the average fell from 15.0% in 2010 '
                'to 13.9% in 2011.'), md=6),
        ], className='g-3 mt-2'),
    ])


def products_layout(p):
    top_products_block = html.Div([
        dcc.Graph(id='top-products-graph',
                  figure=top_products_fig(p['top10_by_rev'], 'Revenue')),
        dbc.RadioItems(
            id='top-products-metric',
            options=[{'label': 'By revenue', 'value': 'Revenue'},
                     {'label': 'By units sold', 'value': 'Quantity'}],
            value='Revenue', inline=True, className='d-flex justify-content-center mb-2'),
        html.P('Four products rank in the top 10 for both revenue and units: jumbo bag red retrospot, '
               'white hanging heart T-light holder, small popcorn holder and assorted colour bird ornament. '
               'Revenue leaders are mostly giftware and seasonal decor; unit leaders are lower-priced items.',
               className='text-muted small'),
    ])

    return html.Div([
        dbc.Row([
            dbc.Col(kpi_card('UK Revenue', f"£{p['tot_uk_rev'] / 1e6:.2f}M",
                             f"{p['uk_pct']:.1f}% of total"), md=3),
            dbc.Col(kpi_card('International Revenue', f"£{p['tot_intl_rev'] / 1e6:.2f}M",
                             f"{p['intl_pct']:.1f}% of total"), md=3),
        ], className='g-3 my-3'),

        dbc.Row([
            dbc.Col(top_products_block, md=6),
            dbc.Col(chart_block(
                pareto_fig(p['product_revenue'], p['n_products_80pct']),
                f"It takes {p['n_products_80pct']:,} products ({p['pct_of_catalog']:.1f}% of the "
                f"{p['n_products']:,}-product catalog) to reach 80% of revenue. No single product "
                f"exceeds 1.7% of revenue, and the top 10 together account for 7.6%."), md=6),
        ], className='g-3'),

        dbc.Row(dbc.Col(chart_block(
            intl_revenue_fig(p['intl_rev']),
            "Ireland (£623K) and the Netherlands (£550K) lead international sales, together ~41% of the total; "
            "Germany and France bring the top four to ~66%. Countries outside the top 15 account for 7.1% "
            f"of international revenue. UK revenue (£{p['tot_uk_rev'] / 1e6:.2f}M, {p['uk_pct']:.1f}% of total) "
            "is shown separately above and excluded here for scale.")), className='mt-3'),
    ])

def simple_table(df):
    header = html.Thead(html.Tr([html.Th(c) for c in df.columns]))
    body = html.Tbody([html.Tr([html.Td(v) for v in row]) for row in df.values])
    return dbc.Table([header, body], striped=True, hover=True, size='sm')


def customers_layout(c):
    return html.Div([
        dbc.Row([
            dbc.Col(kpi_card('Known Customers', f"{c['n_customers']:,}"), md=3),
            dbc.Col(kpi_card('Repeat Customers', f"{c['repeat_rate']:.1f}%",
                             f"{c['n_repeat']:,} placed 2+ orders"), md=3),
            dbc.Col(kpi_card('Top 1% of Customers', f"{c['top1pct_share']:.1f}%",
                             f"of known-customer revenue ({c['n_top_1pct']} customers)"), md=3),
            dbc.Col(kpi_card('No Customer ID', f"{c['noid_rev_pct']:.1f}%", 'of total revenue'), md=3),
        ], className='g-3 my-3'),

        dbc.Row([
            dbc.Col(chart_block(
                cust_split_fig(c['split_df']),
                'Orders with no Customer ID are 7.4% of orders but 13.3% of revenue. The source does not '
                'say why the ID is missing, so the group may mix guest checkouts, other sales channels and '
                'batch invoices.'), md=5),
            dbc.Col(html.Div([
                html.H6('Typical order: No Customer ID vs. known customers', className='mt-3'),
                simple_table(c['comparison']),
                html.P('The typical no-ID order is smaller (median £184 vs. £303), but the average is higher '
                       '(£881 vs. £459) because of a small number of very large bulk invoices. Medians '
                       'describe the typical order.', className='text-muted small'),
            ]), md=7),
        ], className='g-3'),

        dbc.Row([
            dbc.Col(chart_block(
                order_size_fig(c['orders']),
                'The typical order is about 148 units (median); the mean is 279, pulled up by a long tail of '
                'bulk orders. The chart is capped at 800 units and leaves out the largest 4.9% of orders '
                '(up to 87,167 units).'), md=6),
            dbc.Col(chart_block(
                order_buckets_fig(c['order_buckets']),
                f"{c['repeat_rate']:.1f}% of known customers placed more than one order (median "
                f"{c['median_orders']:.0f}, mean {c['mean_orders']:.1f}). Customers who first ordered late in "
                "2011 had little time to reorder, so the true repeat rate is likely slightly higher."), md=6),
        ], className='g-3 mt-2'),

        dbc.Row(dbc.Col(chart_block(
            top_customers_fig(c['top10']),
            f"The top 10 customers account for {c['top10_known_pct']:.1f}% of known-customer revenue "
            f"({c['top10_total_pct']:.1f}% of total revenue), the top 1% for {c['top1pct_share']:.1f}%. "
            f"It takes {c['n_to_80']:,} customers ({c['n_to_80_pct']:.1f}% of the base) to reach 80%. "
            "Most of the top ten are repeat bulk buyers, so retaining them is important.")), className='mt-3'),
    ])    