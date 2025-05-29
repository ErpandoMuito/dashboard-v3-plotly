import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from app.auth import create_login_layout, validate_login
from app.dashboard import create_dashboard_layout
from app.tiny_oauth import TinyOAuth
from urllib.parse import parse_qs, urlparse
import requests
from flask import jsonify

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server
tiny_oauth = TinyOAuth()

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='user-authenticated', storage_type='session'),
    dcc.Store(id='tiny-connected', storage_type='session'),
    dcc.Store(id='tiny-auth-url'),
    html.Div(id='page-content')
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
@app.callback(Output('tiny-auth-url', 'data'),
              Input('tiny-connect-button', 'n_clicks'),
              prevent_initial_call=True)
def get_tiny_auth_url(n_clicks):
    print(f"[DEBUG] get_tiny_auth_url called with n_clicks: {n_clicks}")
    if n_clicks:
        auth_url = tiny_oauth.get_auth_url()
        print(f"[DEBUG] Generated auth URL: {auth_url}")
        return auth_url
    return dash.no_update

# Client-side callback to handle redirect
app.clientside_callback(
    """
    function(url) {
        if (url) {
            console.log('[DEBUG] Redirecting to:', url);
            window.location.href = url;
        }
        return '';
    }
    """,
    Output('url', 'pathname', allow_duplicate=True),
    Input('tiny-auth-url', 'data'),
    prevent_initial_call=True
)

@app.callback([Output('tiny-status', 'children'),
               Output('product-info', 'children'),
               Output('debug-output', 'children')],
              Input('tiny-connected', 'data'))
def update_tiny_status(connected):
    from app.products_db import get_product_by_code
    
    debug_msg = f"Connected status: {connected}\n"
    
    # First test local database
    debug_msg += "\n=== Testing Local Database ===\n"
    local_product = get_product_by_code('PH-504')
    if local_product:
        debug_msg += f"Local DB: Found PH-504\n"
        debug_msg += f"ID: {local_product['id']}\n"
        debug_msg += f"Descrição: {local_product['descricao']}\n"
        debug_msg += f"Preço: R$ {local_product['preco']}\n"
        debug_msg += f"Marca: {local_product['marca']}\n"
    
    if connected:
        # Try to fetch product PH-504 from Tiny
        debug_msg += "\n=== Fetching from Tiny API ===\n"
        debug_msg += "Testing with ID 892471503 (PH-504)\n"
        product_data = tiny_oauth.fetch_product('PH-504')
        
        status = dbc.Alert("Conectado ao Tiny com sucesso!", color="success")
        
        if product_data and product_data.get('data'):
            products = product_data['data']
            debug_msg += f"Products found: {len(products)}\n"
            if products:
                product = products[0]
                # Use V3 field names
                product_info = dbc.Card([
                    dbc.CardBody([
                        html.H5("Produto Encontrado no Tiny:", className="card-title"),
                        html.P([html.Strong("Código: "), product.get('codigo', 'N/A')]),
                        html.P([html.Strong("ID: "), str(product.get('id', 'N/A'))]),
                        html.P([html.Strong("Descrição: "), product.get('nome', product.get('descricao', 'N/A'))]),
                        html.P([html.Strong("Preço: "), f"R$ {product.get('preco', 0):.2f}"]),
                        html.P([html.Strong("Marca: "), product.get('marca', 'N/A')]),
                        html.P([html.Strong("Situação: "), product.get('situacao', 'N/A')])
                    ])
                ], color="info", outline=True, className="mt-3")
            else:
                product_info = dbc.Alert("Produto PH-504 não encontrado no Tiny", color="warning")
        else:
            debug_msg += f"Error fetching product. Response: {product_data}\n"
            # Show local product if available
            if local_product:
                product_info = dbc.Card([
                    dbc.CardBody([
                        html.H5("Produto do Banco Local:", className="card-title"),
                        html.P([html.Strong("Código: "), local_product.get('codigo', 'N/A')]),
                        html.P([html.Strong("ID: "), str(local_product.get('id', 'N/A'))]),
                        html.P([html.Strong("Descrição: "), local_product.get('descricao', 'N/A')]),
                        html.P([html.Strong("Preço: "), f"R$ {local_product.get('preco', 0):.2f}"]),
                        html.P([html.Strong("Marca: "), local_product.get('marca', 'N/A')]),
                        html.Hr(),
                        html.Small("⚠️ Dados do banco local - API Tiny não disponível", className="text-muted")
                    ])
                ], color="warning", outline=True, className="mt-3")
            else:
                product_info = dbc.Alert("Erro ao buscar produto", color="danger")
        
        return status, product_info, debug_msg
    
    return dbc.Alert("Não conectado", color="secondary"), "", debug_msg

@app.callback(Output('debug-live', 'children'),
              Input('debug-interval', 'n_intervals'))
def update_debug_live(n):
    """Live debug info"""
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token = tiny_oauth.get_access_token()
    return f"Last update: {current_time}\nToken exists: {token is not None}"

# Callback for Test API button
@app.callback(
    [Output('test-modal', 'is_open'),
     Output('api-test-results', 'children')],
    [Input('test-api-button', 'n_clicks'),
     Input('close-test-modal', 'n_clicks')],
    [State('test-modal', 'is_open')],
    prevent_initial_call=True
)
def toggle_test_modal(test_clicks, close_clicks, is_open):
    ctx = callback_context
    
    if ctx.triggered[0]['prop_id'] == 'test-api-button.n_clicks':
        # Call the API test endpoint
        try:
            # Use relative URL for Railway compatibility
            import os
            base_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:8050')
            if not base_url.startswith('http'):
                base_url = f'https://{base_url}' if 'railway' in base_url else f'http://{base_url}'
            
            response = requests.get(f'{base_url}/api/test-tiny')
            data = response.json()
            results = '\n'.join(data.get('debug', ['No results']))
        except Exception as e:
            results = f"Error calling API: {str(e)}"
        
        return True, results
    
    # Close button clicked
    return False, ""

# Flask route for API testing
@server.route('/api/test-tiny')
def test_tiny_api():
    results = []
    
    # Test 1: Token exists
    token = tiny_oauth.get_access_token()
    results.append(f"Token exists: {bool(token)}")
    results.append(f"Token preview: {token[:20]}..." if token else "No token")
    
    # Test 2: Simple GET request
    try:
        url = "https://api.tiny.com.br/api/v3/produtos/892471503"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        results.append(f"\nURL: {url}")
        results.append(f"Headers: {headers}")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        results.append(f"Status Code: {response.status_code}")
        results.append(f"Response Headers: {dict(response.headers)}")
        results.append(f"Response Text: {response.text[:500]}")
        
        if response.status_code == 401:
            results.append("ERROR: Token inválido ou expirado")
        elif response.status_code == 404:
            results.append("ERROR: Endpoint não encontrado")
            
    except requests.exceptions.RequestException as e:
        results.append(f"Request Exception: {str(e)}")
    except Exception as e:
        results.append(f"General Exception: {str(e)}")
    
    # Test 3: Alternative endpoint
    try:
        url2 = "https://api.tiny.com.br/api/v3/produtos"
        params = {"codigo": "PH-504", "pagina": 1}
        results.append(f"\nAlternative URL: {url2}")
        results.append(f"Params: {params}")
        
        response2 = requests.get(url2, params=params, headers=headers, timeout=10)
        results.append(f"Alt Status: {response2.status_code}")
        results.append(f"Alt Response: {response2.text[:200]}")
    except Exception as e:
        results.append(f"Alt Exception: {str(e)}")
    
    return jsonify({"debug": results})

def run_server():
    """Entry point for running the server"""
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run_server(debug=debug, host='0.0.0.0', port=port)

if __name__ == '__main__':
    run_server()