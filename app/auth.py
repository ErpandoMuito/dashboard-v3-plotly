from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

def create_login_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2("Dashboard V3", className="text-center mb-4"),
                        html.Hr(),
                        dbc.Form([
                            dbc.Label("Usuário"),
                            dbc.Input(id="login-username", type="text", placeholder="Digite seu usuário"),
                            html.Br(),
                            dbc.Label("Senha"),
                            dbc.Input(id="login-password", type="password", placeholder="Digite sua senha"),
                            html.Br(),
                            dbc.Button("Entrar", id="login-button", color="primary", className="w-100"),
                        ]),
                        html.Div(id="login-alert", className="mt-3")
                    ])
                ], className="shadow")
            ], width=12, md=6, lg=4)
        ], justify="center", className="vh-100 align-items-center")
    ], fluid=True)

def validate_login(username, password):
    return username == "admin" and password == "admin123"