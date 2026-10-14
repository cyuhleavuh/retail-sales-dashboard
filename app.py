from dash import Dash, html, callback, Input, Output
import dash_bootstrap_components as dbc

from data_prep import build_overview, build_products_markets, build_customers
from charts import top_products_fig
from layouts import overview_layout, products_layout, customers_layout

overview = build_overview()
products = build_products_markets()
customers = build_customers()

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title='Retail Sales Dashboard')

app.layout = dbc.Container([
    html.H2('Online Retail Sales Dashboard', className='mt-4'),
    html.P('Online Retail II, Dec 2009 to 9 Dec 2011 (Dec 2011 is partial). Currency £. '
           'Gross sales: cancelled orders are tracked separately.', className='text-muted'),
    dbc.Tabs([
        dbc.Tab(overview_layout(overview), label='Business Overview', tab_id='overview'),
        dbc.Tab(products_layout(products), label='Products & Markets', tab_id='products'),
        dbc.Tab(customers_layout(customers), label='Customers & Orders', tab_id='customers'),
    ], id='main-tabs', active_tab='overview'),
], fluid=True)


@callback(Output('top-products-graph', 'figure'), Input('top-products-metric', 'value'))
def update_top_products(metric):
    data = products['top10_by_rev'] if metric == 'Revenue' else products['top10_by_units']
    return top_products_fig(data, metric)


if __name__ == '__main__':
    app.run(debug=True)