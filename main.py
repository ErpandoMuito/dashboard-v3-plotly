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
    html.Div(id='page-content'),
    # Hidden div to trigger JavaScript
    html.Div(id='redirect-trigger', style={'display': 'none'})
])

@app.callback([Output('page-content', 'children'),
               Output('tiny-connected', 'data')],
              [Input('url', 'pathname'),
               Input('url', 'search')],
              State('user-authenticated', 'data'))
def display_page(pathname, search, authenticated):
    print(f"[DEBUG] display_page - pathname: {pathname}, search: {search}, authenticated: {authenticated}")
    
    # Check for OAuth callback
    if search and authenticated:
        parsed = parse_qs(search[1:])  # Remove '?' from search
        print(f"[DEBUG] Parsed query params: {parsed}")
        if 'code' in parsed:
            code = parsed['code'][0]
            print(f"[DEBUG] OAuth code received: {code}")
            # Exchange code for token
            token_data = tiny_oauth.exchange_code_for_token(code)
            print(f"[DEBUG] Token exchange result: {token_data is not None}")
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
@app.callback(Output('redirect-trigger', 'children'),
              Input('tiny-connect-button', 'n_clicks'),
              prevent_initial_call=True)
def tiny_connect(n_clicks):
    if n_clicks:
        auth_url = tiny_oauth.get_auth_url()
        print(f"[DEBUG] Redirecting to: {auth_url}")
        # Return JavaScript to redirect
        return html.Script(f'window.location.href = "{auth_url}";')
    return dash.no_update

@app.callback([Output('tiny-status', 'children'),
               Output('product-info', 'children'),
               Output('debug-output', 'children')],
              Input('tiny-connected', 'data'))
def update_tiny_status(connected):
    debug_msg = f"Connected status: {connected}\n"
    
    if connected:
        # Try to fetch product PH-504
        debug_msg += "Fetching product PH-504...\n"
        product_data = tiny_oauth.fetch_product('PH-504')
        
        status = dbc.Alert("Conectado ao Tiny com sucesso!", color="success")
        
        if product_data and product_data.get('data'):
            products = product_data['data']
            debug_msg += f"Products found: {len(products)}\n"
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
            debug_msg += f"Error fetching product. Response: {product_data}\n"
            product_info = dbc.Alert("Erro ao buscar produto", color="danger")
        
        return status, product_info, debug_msg
    
    return dbc.Alert("Não conectado", color="secondary"), "", debug_msg

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run_server(debug=debug, host='0.0.0.0', port=port)