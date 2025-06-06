from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_dashboard_layout():
    df_vendas = pd.DataFrame({
        'Mês': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
        'Vendas': [15000, 18000, 22000, 19000, 25000, 28000],
        'Produtos': [120, 150, 180, 160, 200, 220]
    })
    
    fig_vendas = px.bar(df_vendas, x='Mês', y='Vendas', title='Vendas Mensais')
    fig_produtos = px.line(df_vendas, x='Mês', y='Produtos', title='Produtos Vendidos')
    
    return dbc.Container([
        dbc.NavbarSimple(
            brand="Dashboard V3 - Tiny ERP",
            brand_href="#",
            color="primary",
            dark=True,
            children=[
                dbc.NavItem(dbc.Button("Test API", id="test-api-button", color="info", size="sm", className="me-2")),
                dbc.NavItem(dbc.Button("ULTRA DEBUG", id="ultra-debug-button", color="warning", size="sm", className="me-2")),
                dbc.NavItem(dbc.Button("Conectar ao Tiny", id="tiny-connect-button", color="success", size="sm", className="me-2")),
                dbc.NavItem(dbc.Button("Sair", id="logout-button", color="danger", size="sm"))
            ]
        ),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Total de Vendas", className="card-title"),
                        html.H2("R$ 127.000", className="text-primary")
                    ])
                ], className="mb-4")
            ], width=12, md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Produtos Vendidos", className="card-title"),
                        html.H2("1.030", className="text-success")
                    ])
                ], className="mb-4")
            ], width=12, md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Clientes Ativos", className="card-title"),
                        html.H2("245", className="text-info")
                    ])
                ], className="mb-4")
            ], width=12, md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Ticket Médio", className="card-title"),
                        html.H2("R$ 520", className="text-warning")
                    ])
                ], className="mb-4")
            ], width=12, md=3),
        ], className="mt-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=fig_vendas)
                    ])
                ])
            ], width=12, md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(figure=fig_produtos)
                    ])
                ])
            ], width=12, md=6),
        ], className="mt-4"),
        
        # Area for Tiny connection status and product info
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Status Conexão Tiny", className="card-title"),
                        html.Div(id="tiny-status", children="Não conectado"),
                        html.Hr(),
                        html.Div(id="product-info", children="")
                    ])
                ], className="mt-4")
            ], width=12, md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Debug Console", className="card-title"),
                        html.Div(id="debug-output", style={'whiteSpace': 'pre-line', 'fontSize': '12px', 'fontFamily': 'monospace'}),
                        html.Hr(),
                        dcc.Interval(id='debug-interval', interval=2000),  # Update every 2 seconds
                        html.Div(id="debug-live", style={'whiteSpace': 'pre-line', 'fontSize': '10px', 'fontFamily': 'monospace', 'color': 'green'})
                    ])
                ], className="mt-4")
            ], width=12, md=6)
        ]),
        
        # Modal for API test results
        dbc.Modal([
            dbc.ModalHeader("API Test Results"),
            dbc.ModalBody([
                html.Pre(id="api-test-results", style={'whiteSpace': 'pre-wrap', 'fontSize': '12px'})
            ]),
            dbc.ModalFooter([
                dbc.Button("Download Debug", id="download-debug-button", color="primary", className="me-2", n_clicks=0),
                dbc.Button("Close", id="close-test-modal", className="ms-auto", n_clicks=0)
            ]),
        ], id="test-modal", size="lg", is_open=False),
        
        # Store for API test and debug download
        dcc.Store(id='api-test-trigger'),
        dcc.Store(id='debug-download-data'),
        dcc.Download(id='download-debug')
    ], fluid=True)