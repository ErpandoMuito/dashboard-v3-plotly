import dash
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from app.auth import create_login_layout, validate_login
from app.dashboard import create_dashboard_layout
from app.tiny_oauth import TinyOAuth
from urllib.parse import parse_qs, urlparse
import requests
from flask import jsonify, send_file, request
import json
import io

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
               Output('tiny-connected', 'data'),
               Output('url', 'search', allow_duplicate=True)],
              [Input('url', 'pathname'),
               Input('url', 'search')],
              State('user-authenticated', 'data'),
              prevent_initial_call=True)
def display_page(pathname, search, authenticated):
    print(f"[DEBUG] display_page - pathname: {pathname}, search: {search}, authenticated: {authenticated}")
    
    # Check for OAuth callback
    if search and authenticated:
        parsed = parse_qs(search[1:])  # Remove '?' from search
        print(f"[DEBUG] Parsed query params: {parsed}")
        
        # Check for OAuth error
        if 'error' in parsed:
            error = parsed.get('error', ['unknown'])[0]
            error_desc = parsed.get('error_description', ['No description'])[0]
            print(f"[DEBUG] OAuth error: {error} - {error_desc}")
            # Clear the URL parameters
            return create_dashboard_layout(), False, ""
            
        if 'code' in parsed:
            code = parsed['code'][0]
            state = parsed.get('state', [None])[0]
            print(f"[DEBUG] OAuth code received: {code}")
            print(f"[DEBUG] OAuth state: {state}")
            
            # Exchange code for token
            token_data = tiny_oauth.exchange_code_for_token(code)
            print(f"[DEBUG] Token exchange result: {token_data is not None}")
            
            # Clear the URL parameters after processing
            if token_data:
                return create_dashboard_layout(), True, ""
            else:
                # Token exchange failed, but still clear URL
                return create_dashboard_layout(), False, ""
    
    if authenticated:
        return create_dashboard_layout(), dash.no_update, dash.no_update
    return create_login_layout(), dash.no_update, dash.no_update

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
        # Clear existing tokens to force re-authentication
        tiny_oauth.logout()
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
    
    # Validate token if connected
    if connected:
        is_valid, validation_msg = tiny_oauth.validate_token()
        debug_msg += f"Token validation: {validation_msg}\n"
        if not is_valid:
            return dbc.Alert(f"Erro de autenticação: {validation_msg}", color="danger"), "", debug_msg
    
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
     Output('api-test-results', 'children'),
     Output('debug-download-data', 'data')],
    [Input('test-api-button', 'n_clicks'),
     Input('close-test-modal', 'n_clicks')],
    State('test-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_test_modal(test_clicks, close_clicks, is_open):
    ctx = callback_context
    
    if ctx.triggered[0]['prop_id'] == 'test-api-button.n_clicks':
        # Execute test directly instead of calling endpoint
        results = []
        
        # Test 1: Token exists
        token = tiny_oauth.get_access_token()
        results.append(f"Token exists: {bool(token)}")
        results.append(f"Token preview: {token[:20]}..." if token else "No token")
        
        # Decode JWT to check expiration
        try:
            import base64
            import json as json_lib
            # JWT has 3 parts separated by dots
            parts = token.split('.') if token else []
            if len(parts) >= 2:
                # Decode the payload (second part)
                payload = parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.b64decode(payload)
                token_data = json_lib.loads(decoded)
                
                # Check expiration
                exp = token_data.get('exp', 0)
                iat = token_data.get('iat', 0)
                import time
                current_time = time.time()
                
                import datetime
                results.append(f"Token issued at: {datetime.datetime.fromtimestamp(iat)}")
                results.append(f"Token expires at: {datetime.datetime.fromtimestamp(exp)}")
                results.append(f"Token valid: {current_time < exp}")
                results.append(f"Client ID in token: {token_data.get('azp', 'Not found')}")
        except Exception as e:
            results.append(f"Error decoding token: {str(e)}")
        
        # Test 2: Simple GET request
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            # Test 1: Check if API is reachable without auth
            results.append("\n=== Testing API availability (no auth) ===")
            base_url = "https://api.tiny.com.br/api/v3"
            try:
                # Try with User-Agent header
                base_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
                base_response = requests.get(base_url, headers=base_headers, timeout=10)
                results.append(f"Base API Status: {base_response.status_code}")
                if base_response.status_code == 403:
                    results.append("Note: API is blocking requests without proper auth/headers")
            except Exception as e:
                results.append(f"Base API Error: {str(e)}")
            
            # Test 2: Try with complete headers
            results.append("\n=== Testing with complete headers ===")
            full_headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://erp.tiny.com.br/",
                "Origin": "https://erp.tiny.com.br"
            }
            
            # Test empresas endpoint with full headers
            empresas_url = "https://api.tiny.com.br/api/v3/empresas"
            empresas_response = requests.get(empresas_url, headers=full_headers, timeout=10)
            results.append(f"Empresas Status: {empresas_response.status_code}")
            if empresas_response.status_code != 200:
                results.append(f"Response: {empresas_response.text[:200]}")
            else:
                results.append("SUCCESS! Found working headers configuration")
                results.append(f"Response: {empresas_response.text[:200]}")
            
            # Test 3: Try with session to handle cookies
            results.append("\n=== Testing with session (handles cookies) ===")
            session = requests.Session()
            session.headers.update({
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            
            # First request to get cookies
            product_url = "https://api.tiny.com.br/api/v3/produtos/892471503"
            session_response = session.get(product_url, timeout=10)
            results.append(f"Session Status: {session_response.status_code}")
            results.append(f"Cookies: {session.cookies.get_dict()}")
            
            if session_response.status_code == 403:
                # Try again after getting cookies
                retry_response = session.get(product_url, timeout=10)
                results.append(f"Retry Status: {retry_response.status_code}")
            
            # Test 5: Try curl-style request
            results.append("\n=== Testing with curl-style headers ===")
            curl_headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "*/*",
                "User-Agent": "curl/7.68.0"
            }
            curl_response = requests.get(product_url, headers=curl_headers, timeout=10)
            results.append(f"Curl-style Status: {curl_response.status_code}")
            
            # Test 6: Check token details from JWT
            results.append("\n=== Token Analysis ===")
            if 'exp' in locals() and 'current_time' in locals():
                results.append(f"Time until expiration: {(exp - current_time)/3600:.2f} hours")
            if 'token_data' in locals():
                results.append(f"Token scope: {token_data.get('scope', 'Not found')}")
                results.append(f"Token type: {token_data.get('typ', 'Not found')}")
                results.append(f"Token aud: {token_data.get('aud', 'Not found')}")
                results.append(f"Token iss: {token_data.get('iss', 'Not found')}")
            
            # Test 7: Show redirect URI config
            results.append("\n=== OAuth Configuration ===")
            results.append(f"Configured redirect URI: {tiny_oauth.redirect_uri}")
            results.append(f"Client ID: {tiny_oauth.client_id[:20]}...")
            import os
            results.append(f"Current host: {os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost')}")
                
        except requests.exceptions.RequestException as e:
            results.append(f"Request Exception: {str(e)}")
        except Exception as e:
            results.append(f"General Exception: {str(e)}")
        
        # Test 3: Check if we need to use a different base URL
        results.append("\n=== Testing alternative endpoints ===")
        
        # Try erp.tiny.com.br instead of api.tiny.com.br
        alt_urls = [
            "https://erp.tiny.com.br/api/v3/produtos/892471503",
            "https://api.tiny.com.br/openapi/v3/produtos/892471503",
            "https://tiny.com.br/api/v3/produtos/892471503"
        ]
        
        for alt_url in alt_urls:
            try:
                results.append(f"\nTrying: {alt_url}")
                alt_response = requests.get(alt_url, headers=headers, timeout=5)
                results.append(f"Status: {alt_response.status_code}")
                if alt_response.status_code != 403:
                    results.append(f"Different response! Body: {alt_response.text[:200]}")
            except Exception as e:
                results.append(f"Error: {str(e)}")
        
        # Test 4: Try using local proxy
        results.append("\n=== Testing via local proxy ===")
        try:
            proxy_url = "/api/proxy/produtos/892471503"
            results.append(f"Proxy URL: {proxy_url}")
            # Note: This won't work in the callback context, but shows the concept
            results.append("Note: Proxy endpoint available at /api/proxy/*")
        except Exception as e:
            results.append(f"Proxy note error: {str(e)}")
        
        # Create debug data for download
        debug_info = {
            "timestamp": datetime.datetime.now().isoformat() if 'datetime' in globals() else "unknown",
            "results": results,
            "token_exists": bool(token),
            "token_preview": token[:50] + "..." if token else None,
            "oauth_config": {
                "client_id": tiny_oauth.client_id,
                "redirect_uri": tiny_oauth.redirect_uri,
                "auth_base_url": tiny_oauth.auth_base_url,
                "api_base_url": tiny_oauth.api_base_url
            },
            "environment": {
                "railway_domain": os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost'),
                "redis_url": "configured" if os.environ.get('REDIS_URL') else "not_configured",
                "port": os.environ.get('PORT', '8050')
            }
        }
        
        return True, '\n'.join(results), json.dumps(debug_info, indent=2)
    
    # Close button clicked
    return False, "", dash.no_update

# Callback for download button
@app.callback(
    Output('download-debug', 'data'),
    Input('download-debug-button', 'n_clicks'),
    State('debug-download-data', 'data'),
    prevent_initial_call=True
)
def download_debug(n_clicks, debug_data):
    if n_clicks and debug_data:
        return dict(content=debug_data, filename="tiny_api_debug.json")
    return dash.no_update

# Server route for proxying API requests to avoid CORS issues
@server.route('/api/proxy/<path:path>')
def proxy_api_request(path):
    """Proxy requests to Tiny API to avoid CORS issues"""
    token = tiny_oauth.get_access_token()
    if not token:
        return jsonify({"error": "No authentication token"}), 401
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Forward the request to Tiny API
    api_url = f"https://api.tiny.com.br/api/v3/{path}"
    
    try:
        if request.method == 'GET':
            response = requests.get(api_url, headers=headers, params=request.args)
        else:
            response = requests.request(
                method=request.method,
                url=api_url,
                headers=headers,
                json=request.get_json(),
                params=request.args
            )
        
        # Return the response from Tiny API
        return response.content, response.status_code, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_server():
    """Entry point for running the server"""
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run_server(debug=debug, host='0.0.0.0', port=port)

if __name__ == '__main__':
    run_server()