# %%
import dash
import dash_bootstrap_components as dbc
#pip install dash-bootstrap-components
from dash import Input, Output, dcc, html
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import os

# %% [markdown]
# Read from DB or Generate Mock Data(temperary)

# %%
current_directory = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_directory, 'Airline_MA.db')
conn = sqlite3.connect(db_path) 

# %%
# read data for page 1
# Sankey Chart Data Processing -> Final use: data_sankey
query = """
SELECT 
    a.company_name,
    i.year, 
    i.revenue AS "Revenue", 
    i.sales_and_services_revenue AS "Sales & Services Revenue", 
    i.other_revenue AS "Other Revenue", 
    i.operating_expenses AS "Operating Expenses", 
    i.selling_and_marketing AS "Selling & Marketing", 
    i.depreciation_and_amortization AS "Depreciation & Amortization", 
    i.other_operating_expense AS "Other Operating Expense", 
    i.operating_income AS "Operating Income", 
    i.operating_loss AS "Operating Loss"
FROM 
    Airline a
JOIN 
    IncomeStatement i
ON 
    a.company_id = i.company_id;
"""
data_sankey = pd.read_sql_query(query, conn)

# Ensure numeric columns are properly converted
numeric_columns = [
    "Revenue", "Sales & Services Revenue", "Other Revenue", 
    "Operating Expenses", "Selling & Marketing", "Depreciation & Amortization", 
    "Other Operating Expense", "Operating Income", "Operating Loss"
]

# Convert these columns to numeric, handling errors (e.g., commas or non-numeric values)
data_sankey[numeric_columns] = data_sankey[numeric_columns].replace(',', '', regex=True)
data_sankey[numeric_columns] = data_sankey[numeric_columns].apply(pd.to_numeric, errors='coerce')

# Check for missing or NaN values after conversion
if data_sankey[numeric_columns].isnull().values.any():
    print("Warning: Some values in the numeric columns are NaN after conversion.")

# read data for page 1
# Line Chart Data Processing -> Final use: data_line
data_line = pd.read_sql_query("SELECT * FROM Multiple NATURAL JOIN Airline", conn)
data_line['date'] = pd.to_datetime(data_line['date'], format='%Y-%m-%d')
data_line['year'] = data_line['date'].dt.year

# %%
# read data for page 2
# Radar Chart Data Processing -> Final use: data_radar
query = """
SELECT a.company_name, k.ratio_year, 
       k.return_on_assets AS Profitability, 
       k.quick_ratio AS Liquidity, 
       k.total_debt_to_capital AS Credit, 
       k.total_debt_to_equity AS Leverage_Ratio, 
       k.return_on_invested_capit AS ROIC
FROM Airline a
JOIN KeyRatios k
ON a.company_id = k.company_id
"""
data_radar = pd.read_sql_query(query, conn)


# FootBall Field Data Processing -> Final use: data_football
key_financial = pd.read_sql_query("SELECT distinct company_name,fin_year, revenue, multiple_type, Q1 as 'lower', Q3 as 'upper' FROM key_financial join Multiple using(company_id) join Airline using (company_id)", conn)
# Calculate EV_Revenue_lower and EV_Revenue_upper
key_financial['EV_Revenue_lower'] = np.where(
    key_financial['multiple_type'] == 'revenue',
    key_financial['revenue'] * key_financial['lower'],
    np.nan
)

key_financial['EV_Revenue_upper'] = np.where(
    key_financial['multiple_type'] == 'revenue',
    key_financial['revenue'] * key_financial['upper'] - key_financial['EV_Revenue_lower'],
    np.nan
)


key_financial_reset = key_financial[['company_name', 'fin_year','multiple_type', 'EV_Revenue_lower', 'EV_Revenue_upper']]
key_financial_reset = key_financial_reset.dropna()
key_financial_reset

data_football = key_financial_reset.melt(id_vars = ['company_name', 'fin_year', 'multiple_type'],var_name = 'Range', value_name= 'Value')

# %% [markdown]
# Build App

# %%
# build dashboard layout
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# for deployment
server = app.server

external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=Open+Sans:ital,wght@0,300..800;1,300..800&family=PT+Serif+Caption:ital@0;1&display=swap',
     dbc.themes.SLATE
]

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "25vw",
    "padding": "2rem 2rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "25vw",
    "margin-right": "2rem",
    "padding": "2rem 2rem",
}

company_colors = {
    'Spirit': '#FFD966',
    'Sky West': '#E06666',
    'JetBlue': '#5B9BD5',
    'Hawaiian': '#9E91C9',
    'Frontier': '#A8D08D'
}

# Define specific link colors for each company
link_colors_by_company = {
    "Spirit": [
        "#EAC100", "#FFD306", "#FFDC35", "#FFE153", 
        "#FFE66F", "#FFED97", "#FFF0AC", "#FFF4C1"
    ],
    "Sky West": [
        "#8C4646", "#A65252", "#BF6A6A", "#D28484", 
        "#E1A3A3", "#EBC3C3", "#F5DCDC", "#FAEAEA"
    ],
    "JetBlue": [
        "#004B97", "#005AB5", "#0066CC", "#0072E3",
        "#0080FF", "#2894FF", "#46A3FF", "#66B3FF"
    ],
    "Hawaiian": [
        "#5151A2", "#5A5AAD", "#7373B9", "#8080C0",
        "#9999CC", "#A6A6D2", "#B8B8DC", "#C7C7E2"
    ],
    "Frontier": [
        "#4C8A4C", "#426D54", "#5A8559", "#639E63", 
        "#719A5E", "#7AB27A", "#91C791", "#A9DBA9"
    ]
}

sidebar = html.Div(
    [
        html.H2("Airline Financial Performance", className="display-4", style={'font-size': '2rem', 'font-family': "PT Serif Caption, serif",
  'font-weight': '400', 'font-style': 'normal'}),
        html.Hr(),
        html.P(
            "This dashboard visualize the financial performance of potential M&A targets for Alaska Airline. Individual financial performance are shown, and comparison of performance between targeted airlines and Alaska Airline can be further understood.", className="lead", style={'font-size': '14px', 'font-family': "Newsreader, serif",
  'letter-spacing': '1px', 'line-height': '16px'}
        ),
        dbc.Nav(
            [
                dbc.NavLink("Overview", href="/", active="exact"),
                dbc.NavLink("Company Comparison", href="/page-1", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

# %%
# Callback for page layout
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return html.Div([
            html.H2('Overview Yearly Performance', style={'font-family': 'Newsreader, serif', 'font-size': '24px', 'font-weight': '700'}),
            html.Div(
                [
                dbc.Label("Airline:"),
                dbc.RadioItems(
                    id="company-filter",
                    options=[{'label': company, 'value': company} for company in data_sankey['company_name'].unique()],
                    value="Spirit", # Default selected company
                    inline=True
                    )
                ], style={'display': 'flex', 'justifyContent': 'flex-start', 'gap': '15px', 'marginBottom': '10px'}
            ),
            html.Div(
                dcc.Slider(
                    id='year-filter',
                    min=data_sankey['year'].min(),
                    max=data_sankey['year'].max(),
                    step=1,
                    value=data_sankey['year'].max(), # Default selected year
                    included=False,
                    marks={year: str(year) for year in range(data_sankey['year'].min(), data_sankey['year'].max() + 1)}
                ),
                # style={'marginBottom': '40px'}
            ),
            dcc.Graph(id="sankey-diagram"),
            html.Div(
                [
                dbc.Label("Type:"),
                dbc.RadioItems(
                    id="multiple-filter",
                    options=[{'label': type, 'value': type} for type in data_line['multiple_type'].unique()],
                    value=data_line['multiple_type'].unique()[0],
                    inline=True
                )
                ],
                style={'display': 'flex', 'justifyContent': 'flex-start', 'gap': '15px'}
            ),
            dcc.Graph(id='line-graph'),
            ])
    elif pathname == "/page-1":
        return html.Div([
            html.H2("Comparison between Airlines", style={'font-family': 'Newsreader, serif', 'font-size': '24px', 'font-weight': '700'}),

            # Shared Company Checklist
            html.Div(
                [
                dbc.Label("Airline:"),
                dbc.Checklist(
                    id="company-checklist",
                    options=[{'label': f'  {company}', 'value': company} for company in data_radar['company_name'].unique()],
                    value=data_radar['company_name'].unique().tolist(),
                    inline=True
                    )
                ],
                style={'display': 'flex', 'justifyContent': 'flex-start', 'gap': '15px', 'marginBottom': '10px'}               
            ),

            # Shared Year Slider
            html.Div(
                dcc.Slider(
                    id='year-slider',
                    min=data_football['fin_year'].min(),
                    max=data_football['fin_year'].max(),
                    step=1,
                    value=data_football['fin_year'].max(),
                    included=False,
                    marks={int(year): str(year) for year in data_football['fin_year'].unique()}
                ),
                # style={'marginBottom': '40px'}
            ),

            # Radar Chart
            html.Div(
                dcc.Graph(id='radar-chart'), 
                # style={'marginBottom': '40px'}
                ),

            # Bar Chart
            html.Div(
                dcc.Graph(id='bar-chart')
                ),
        ])
    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )

# %%
# Callback for Sankey Diagram
@app.callback(
    Output('sankey-diagram', 'figure'),
    [Input('company-filter', 'value'),
     Input('year-filter', 'value')]
)
def update_sankey(selected_company, selected_year):
    # Ensure single company is selected
    if isinstance(selected_company, list):
        selected_company = selected_company[0]
    
    # Filter the data for the selected company and year
    filtered_data = data_sankey[
        (data_sankey['company_name'] == selected_company) & 
        (data_sankey['year'] == selected_year)
    ]

    # Get the individual values
    sales_services_revenue = filtered_data['Sales & Services Revenue'].values[0]
    other_revenue = filtered_data['Other Revenue'].values[0]
    operating_income = filtered_data['Operating Income'].values[0]
    operating_loss = filtered_data['Operating Loss'].values[0]
    revenue = filtered_data['Revenue'].values[0]
    operating_expenses = filtered_data['Operating Expenses'].values[0]
    selling_marketing = filtered_data['Selling & Marketing'].values[0]
    depreciation_amortization = filtered_data['Depreciation & Amortization'].values[0]
    other_operating_expense = filtered_data['Other Operating Expense'].values[0]

    # Select link colors for the selected company
    link_colors = link_colors_by_company[selected_company]
    
    # Generate the Sankey diagram data
    nodes = [
        "Sales & Services Revenue",
        "Other Revenue",
        "Revenue",
        "Operating Income",
        "Operating Expenses",
        "Operating Loss",
        "Selling & Marketing",
        "Depreciation & Amortization",
        "Other Operating Expense"
    ]
    
    if operating_loss == 0 and operating_income > 0:
        # Revenue splits into Operating Expenses and Operating Income
        links = dict(
            source=[0, 1, 2, 2, 5, 4, 4, 4],
            target=[2, 2, 3, 4, 4, 6, 7, 8],
            value=[
                sales_services_revenue,  # Sales & Services Revenue to Revenue
                other_revenue,           # Other Revenue to Revenue
                operating_income,        # Operating Income to Operating Income
                operating_expenses,      # Revenue to Operating Expenses
                operating_loss,          # Operating Loss stays as is
                selling_marketing,       # Selling & Marketing
                depreciation_amortization,  # Depreciation & Amortization
                other_operating_expense   # Other Operating Expense
            ],
            color=link_colors
        )
    else:
        links = dict(
            source=[0, 1, 2, 5, 4, 4, 4],
            target=[2, 2, 4, 4, 6, 7, 8],
            value=[
                sales_services_revenue,  # Sales & Services Revenue to Revenue
                other_revenue,           # Other Revenue to Revenue
                revenue,                 # Revenue to Operating Expenses
                operating_loss,          # Operating Loss to Operating Expenses
                selling_marketing,       # Selling & Marketing from Operating Expenses
                depreciation_amortization,  # Depreciation & Amortization from Operating Expenses
                other_operating_expense   # Other Operating Expense from Operating Expenses
            ],
            color=link_colors
        )

    # Create the Sankey diagram
    sankey_chart = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="#E0E0E0", width=0),
            label=nodes,
            color="#f5f5f5"
        ),
        link=dict(
            source=links["source"],
            target=links["target"],
            value=links["value"],
            color=links["color"]  # Adjusted opacity for the links
        )
    )])
    
    sankey_chart.update_layout(
        title_text=f"Sankey Diagram for {selected_company} {selected_year} Financial Data"
    )
    return sankey_chart

# Callback for Line Chart
@app.callback(
    Output('line-graph', 'figure'),
    [Input('company-filter', 'value'),
     Input('year-filter', 'value'),
     Input('multiple-filter', 'value')]
)
def update_graphs(selected_company, selected_year, selected_type):
    filtered_df = data_line[
        (data_line['company_name']==selected_company) &
        (data_line['year'] == selected_year) & 
        (data_line['multiple_type'] == selected_type)
    ]

    if filtered_df.empty:
        empty_figure = px.line()
        message_annotation = {
            'x': 0.5, 'y': 0.5, 'xref': 'paper', 'yref': 'paper', 
            'text': 'No data available for the selected filters.',
            'font':dict(
                        size=15,
                        family="Newsreader, serif",
                        color="#CC0000"
                    ), 'showarrow': False}

        # Update the figure layout and show
        empty_figure.update_layout({'annotations': [message_annotation]})
        empty_figure.update_layout(
            plot_bgcolor='white',
            height=400,
            paper_bgcolor="white",
            xaxis_showticklabels=False,
            yaxis_showticklabels=False
        )
        return empty_figure

    line_graph = px.line(
        data_frame=filtered_df,
        x='date', 
        y='multiple_value',
        color='company_name',
        color_discrete_map=company_colors
        )
    
    line_graph.add_hline(
        y=filtered_df[filtered_df['year']==selected_year].iloc[0]['average'],  
        line_dash="solid",
        line_color="black",
        annotation_text=f"Average({round(filtered_df[filtered_df['year']==selected_year].iloc[0]['average'],2)})",
        annotation_position="top right"
    )

    line_graph.add_hline(
        y=filtered_df[filtered_df['year']==selected_year].iloc[0]['Q1'],  
        line_dash="dash",
        line_color="grey",
        annotation_text=f"-1 std({round(filtered_df[filtered_df['year']==selected_year].iloc[0]['Q1'],2)})",
        annotation_position="top right"
    )

    line_graph.add_hline(
        y=filtered_df[filtered_df['year']==selected_year].iloc[0]['Q3'],  
        line_dash="dash",
        line_color="grey",
        annotation_text=f"+1 std({round(filtered_df[filtered_df['year']==selected_year].iloc[0]['Q3'],2)})",
        annotation_position="top right"
    )
    
    line_graph.update_layout(
        title_text=f"Multiple Trend of {selected_year}",
        yaxis_title=f'{selected_type} multiple',
        plot_bgcolor='#f5f5f5',
        height=400
    )

    return line_graph

# Callback for Radar Chart
@app.callback(
    Output('radar-chart', 'figure'),
    [Input('company-checklist', 'value'),
     Input('year-slider', 'value')]
)
def update_radar_chart(selected_companies, selected_year):
    if len(selected_companies) < 2:
        figure = go.Figure()
        figure.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[
                dict(
                    text="Reminder: Please select at least two companies to display a meaningful comparison on the radar chart.",
                    x=0.5,  # Position at the center horizontally
                    y=0.5,  # Position at the center vertically
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(
                        size=15,
                        family="Newsreader, serif",
                        color="#CC0000"
                    )
                )
            ]
        )
        return figure

    filtered_data = data_radar[
        (data_radar['ratio_year'] == selected_year) & 
        (data_radar['company_name'].isin(selected_companies))
    ]
    
    if filtered_data.empty:
        figure = go.Figure()
        figure.update_layout(
            title=f"No data available for year {selected_year}",
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return figure

    metrics = ["Profitability", "Liquidity", "Credit", "Leverage_Ratio", "ROIC"]
    for metric in metrics:
        filtered_data[metric] = pd.to_numeric(filtered_data[metric], errors='coerce')
    
    radar = []
    for company in selected_companies:
        company_data = filtered_data[filtered_data['company_name'] == company]
        if not company_data.empty:
            values = company_data[metrics].iloc[0].tolist()
            values.append(values[0])  # Close the loop
            radar.append(go.Scatterpolar(
                r=values,
                theta=metrics + [metrics[0]],  # Close the loop
                fill='toself',
                name=company,
                line=dict(color=company_colors.get(company, '#000000'))
            ))

    radar_chart = go.Figure(data=radar)
    radar_chart.update_layout(
        polar=dict(
            bgcolor='#f5f5f5',
            radialaxis=dict(visible=True),
        ),
        title=f"Financial Ratios for Year {selected_year}",
        legend=dict(
            xanchor="left",
            yanchor="middle",
            x=1.1,  # Consistent position for the legend
            y=0.5,  # Center the legend vertically
            orientation='v',  # Vertical layout
            traceorder='normal',  # Keep items ordered
        )
    )
    return radar_chart

# Callback for Bar Chart
@app.callback(
    Output('bar-chart', 'figure'),
    [Input('company-checklist', 'value'),
     Input('year-slider', 'value')]
)
def update_bar_chart(selected_companies, year):
    if len(selected_companies) < 2:
        figure = go.Figure()
        figure.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[
                dict(
                    text="Reminder: Please select at least two companies to display a meaningful comparison on the football field chart.",
                    x=0.5,  # Position at the center horizontally
                    y=0.5,  # Position at the center vertically
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(
                        size=15,
                        family="Newsreader, serif",
                        color="#CC0000"
                    )
                )
            ]
        )
        return figure    

    # Filter data
    filtered_data = data_football[data_football['company_name'].isin(selected_companies)]
    filtered_data = filtered_data[filtered_data['fin_year'] == year]
    
    # Adjust Range for better legend and visualization
    filtered_data['Range_Display'] = filtered_data.apply(
        lambda row: row['company_name'] if row['Range'] == 'EV_Revenue_upper' else 'Transparent',
        axis=1
    )
    
    # Define a color map
    color_discrete_map = {
        company: company_colors.get(company, "#000000")  # Default to black for companies
        for company in selected_companies
    }
    color_discrete_map['Transparent'] = 'rgba(0, 0, 0, 0)'  # Transparent color for lower range

    # Create the bar chart
    football_chart = px.bar(
        filtered_data, 
        x='Value', 
        y='company_name', 
        color='Range_Display',
        title="Enterprise Value Range",
        color_discrete_map=color_discrete_map
    )

    # Remove the bar frame by adjusting the `marker` properties
    football_chart.update_traces(
        marker=dict(line=dict(width=0))  # Set border width to 0
    )

    # Customize layout and legend
    football_chart.update_layout(
        xaxis_title='Business Valuation ($ in millions)',
        yaxis_title='Company',
        xaxis=dict(range=[0, 8000]),  # Set x-axis range
        showlegend=True,  # Enable legend
        legend=dict(
            title="Company",
            traceorder="normal",
            itemsizing="constant",
            bgcolor="rgba(255, 255, 255, 0)",  # No background
        ),
        height=400,
        plot_bgcolor='#f5f5f5'
    )

    # Exclude 'Transparent' from the legend
    football_chart.for_each_trace(
        lambda trace: trace.update(showlegend=False) if trace.name == 'Transparent' else None
    )
    
    return football_chart


if __name__ == "__main__":
    app.run(debug=True)


