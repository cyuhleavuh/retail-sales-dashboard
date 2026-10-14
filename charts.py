import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = 'plotly_white'
MONTH_ORDER = list(calendar.month_name)[1:]


def monthly_revenue_fig(monthly_revenue):
    fig = px.line(monthly_revenue, x='YearMonth', y='Revenue',
                  title='Monthly Revenue Trend', template=TEMPLATE)
    fig.update_yaxes(title='Revenue (£)', tickformat=',.0f')
    fig.update_xaxes(title='Month, Year')
    return fig


def yoy_fig(yoy_data):
    data = (yoy_data.assign(Year=yoy_data['Year'].astype(str),
                            MonthName=pd.Categorical(yoy_data['MonthName'], categories=MONTH_ORDER, ordered=True))
            .sort_values(['Year', 'MonthName']))
    fig = px.line(data, x='MonthName', y='Revenue', color='Year', markers=True,
                  title='Revenue by Month: Year-over-Year Comparison',
                  category_orders={'MonthName': MONTH_ORDER}, template=TEMPLATE)
    fig.update_xaxes(title='Month')
    fig.update_yaxes(title='Revenue (£)', tickformat=',.0f')
    return fig


def cancellation_rate_fig(cancellation_trend):
    fig = px.line(cancellation_trend, x='YearMonth', y='Cancellation_Rate_%', markers=True,
                  title='Order Cancellation Rate over Time', template=TEMPLATE)
    fig.update_yaxes(title='Order Cancellation Rate (%)')
    fig.update_xaxes(title='Month, Year')
    return fig


def top_products_fig(data, metric):
    """data: a top-10 table; metric: 'Revenue' or 'Quantity'."""
    titles = {'Revenue': ('Top 10 Products by Revenue', 'Revenue (£)'),
              'Quantity': ('Top 10 Products by Units Sold', 'Units Sold')}
    title, axis_title = titles[metric]
    fig = px.bar(data, x=metric, y='Description', orientation='h', title=title, template=TEMPLATE)
    fig.update_yaxes(categoryorder='total ascending', title='Product Description')
    fig.update_xaxes(title=axis_title, tickformat=',.0f')
    return fig


def pareto_fig(product_revenue, n_products_80pct, top_n=50):
    plot_data = product_revenue.head(top_n)
    names = plot_data['Description'] if 'Description' in plot_data else [''] * len(plot_data)
    custom = list(zip(names, plot_data['Revenue_%']))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=plot_data['Rank'], y=plot_data['Revenue'],
        name='Revenue', marker_color='steelblue', customdata=custom,
        hovertemplate=('<b>Rank #%{x}</b><br>%{customdata[0]}<br>'
                       'Revenue: £%{y:,.0f}<br>'
                       'Share of total: %{customdata[1]:.2f}%<extra></extra>')))
    fig.add_trace(go.Scatter(
        x=plot_data['Rank'], y=plot_data['Cumulative_%'],
        name='Cumulative %', yaxis='y2',
        mode='lines+markers', line=dict(color='firebrick'),
        hovertemplate=('<b>Top %{x} products</b><br>'
                       'Cumulative share: %{y:.1f}% of revenue<extra></extra>')))
    fig.add_hline(y=80, line_dash='dash', line_color='gray', yref='y2')
    fig.update_layout(
        title=f'Pareto Analysis: Cumulative Revenue % by Product Rank (Top {top_n})',
        template=TEMPLATE,
        height=500,
        margin=dict(t=80, r=80, b=120),
        legend=dict(orientation='h', yanchor='top', y=-0.2, xanchor='center', x=0.5),
        yaxis=dict(title='Revenue (£)', tickformat=',.0f'),
        yaxis2=dict(title='Cumulative % of Revenue', overlaying='y', side='right',
                    range=[0, 100], tickvals=[0, 20, 40, 60, 80, 100], ticksuffix='%',
                    showgrid=False),
    )
    fig.update_xaxes(title='Product Rank', range=[0.5, top_n + 0.5])
    fig.add_annotation(
        x=top_n + 0.5, y=80, yref='y2', xanchor='right', yanchor='bottom', showarrow=False,
        text=f'80% of revenue is reached at product {n_products_80pct:,} (off this chart)')
    return fig


def intl_revenue_fig(intl_rev, top_n=15):
    fig = px.bar(intl_rev.head(top_n), x='Country', y='Revenue',
                 title=f'International Revenue by Country (Top {top_n}, excluding UK)',
                 template=TEMPLATE)
    fig.update_yaxes(title='Revenue (£)', tickformat=',.0f')
    fig.update_xaxes(title='Country', tickangle=-45)
    return fig


def cust_split_fig(split_df):
    fig = px.bar(split_df, x='Metric', y='Percent', color='Customer_Type', barmode='group',
                 title='Known vs. No Customer ID: Share of Revenue and Orders',
                 labels={'Customer_Type': 'Customer type'},
                 text=split_df['Percent'].round(1).astype(str) + '%', template=TEMPLATE)
    fig.update_yaxes(title='% of Total')
    return fig


def order_size_fig(orders, cap=800, bin_size=50):
    excluded_pct = (orders['units_per_order'] > cap).mean() * 100
    fig = px.histogram(
        orders, x='units_per_order', opacity=0.75, template=TEMPLATE,
        title=f'Distribution of Units per Order ({100 - excluded_pct:.0f}% of Orders, up to {cap} Units)')
    fig.update_traces(xbins=dict(size=bin_size))
    fig.update_xaxes(title='Units per Order', range=[0, cap], dtick=bin_size,
                     tickangle=-45, showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(title='Number of Orders')
    return fig


def order_buckets_fig(order_buckets):
    fig = px.bar(order_buckets, x='Orders', y='Customers', text='Customers',
                 title='Known Customers by Number of Orders', template=TEMPLATE)
    fig.update_xaxes(title='Orders Placed', type='category')
    fig.update_yaxes(title='Number of Customers')
    return fig


def top_customers_fig(top10):
    fig = px.bar(top10, x='Revenue', y='Customer', orientation='h',
                 title='Top 10 Known Customers by Revenue', template=TEMPLATE,
                 custom_data=['Country', 'Orders', 'AOV', 'Pct_of_Known_Rev'])
    fig.update_traces(hovertemplate=(
        '<b>%{y}</b> (%{customdata[0]})<br>'
        'Revenue: £%{x:,.0f}<br>'
        'Share of known-customer revenue: %{customdata[3]:.1f}%<br>'
        'Orders: %{customdata[1]:,}<br>'
        'Average order value: £%{customdata[2]:,.0f}'
        '<extra></extra>'))
    fig.update_yaxes(categoryorder='total ascending', title='Customer ID')
    fig.update_xaxes(title='Revenue (£)', tickformat=',.0f')
    return fig