import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from app.auth import create_login_layout, validate_login
from app.dashboard import create_dashboard_layout
from app.tiny_oauth import TinyOAuth
from urllib.parse import parse_qs, urlparse

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server
tiny_oauth = TinyOAuth()

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='user-authenticated', storage_type='session'),
    dcc.Store(id='tiny-connected', storage_type='session'),
    html.Div(id='page-content')
])

@app.callback([Output('page-content', 'children'),
               Output('tiny-connected', 'data')],
              [Input('url', 'pathname'),
               Input('url', 'search')],
              State('user-authenticated', 'data'))
def display_page(pathname, search, authenticated):
    # Check for OAuth callback
    if search and authenticated:
        parsed = parse_qs(search[1:])  # Remove '?' from search
        if 'code' in parsed:
            code = parsed['code'][0]
            # Exchange code for token
            token_data = tiny_oauth.exchange_code_for_token(code)
            if token_data:
                return create_dashboard_layout(), True
    
    if authenticated:
        return create_dashboard_layout(), dash.no_update
    return create_login_layout(), dash.no_update

@app.callback([Output('user-authenticated', 'data'),
               Output('url', 'pathname'),
               Output('login-alert', 'children')],
              Input('login-button', 'n_clicks'),
              [State('login-username', 'value'),
               State('login-password', 'value')],
              prevent_initial_call=True)
def login(n_clicks, username, password):
    if username and password:
        if validate_login(username, password):
            return True, '/dashboard', ''
        return None, '/', dbc.Alert("Usuário ou senha inválidos!", color="danger")
    return None, '/', dbc.Alert("Preencha todos os campos!", color="warning")

@app.callback(Output('url', 'pathname', allow_duplicate=True),
              Input('logout-button', 'n_clicks'),
              prevent_initial_call=True)
def logout(n_clicks):
    return '/'

# Tiny OAuth callbacks
@app.callback(Output('url', 'href'),
              Input('tiny-connect-button', 'n_clicks'),
              prevent_initial_call=True)
def tiny_connect(n_clicks):
    if n_clicks:
        return tiny_oauth.get_auth_url()
    return dash.no_update

@app.callback([Output('tiny-status', 'children'),
               Output('product-info', 'children')],
              Input('tiny-connected', 'data'))
def update_tiny_status(connected):
    if connected:
        # Try to fetch product PH-504
        product_data = tiny_oauth.fetch_product('PH-504')
        
        status = dbc.Alert("Conectado ao Tiny com sucesso!", color="success")
        
        if product_data and product_data.get('data'):
            products = product_data['data']
            if products:
                product = products[0]
                product_info = dbc.Card([
                    dbc.CardBody([
                        html.H5("Produto Encontrado:", className="card-title"),
                        html.P(f"ID: {product.get('id', 'N/A')}"),
                        html.P(f"Nome: {product.get('nome', 'N/A')}"),
                        html.P(f"SKU: {product.get('codigo', 'N/A')}")
                    ])
                ], color="info", outline=True)
            else:
                product_info = dbc.Alert("Produto PH-504 não encontrado", color="warning")
        else:
            product_info = dbc.Alert("Erro ao buscar produto", color="danger")
        
        return status, product_info
    
    return dbc.Alert("Não conectado", color="secondary"), ""

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)