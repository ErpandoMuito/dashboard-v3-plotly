import os
import json
import time
import requests
from datetime import datetime, timedelta
import redis
from urllib.parse import urlencode

class TinyOAuth:
    def __init__(self):
        self.client_id = "tiny-api-0ec9fd177624e0c733a68cf61284a695e4f0d27f-1748519501"
        self.client_secret = "qTOelJ39VTV6nB6DsxFrm8bZcVZ9qTNY"
        
        # Check for environment variable or use the new domain
        import os
        # First check for custom domain, then Railway domain, then fallback
        custom_domain = os.environ.get('APP_DOMAIN')
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        
        # Use the original Railway domain for now while DNS propagates
        # TODO: Switch back to custom domain after DNS is fully propagated and OAuth app is updated
        self.redirect_uri = "https://web-production-e80e8.up.railway.app/"
        
        # Future implementation when DNS is ready:
        # if custom_domain:
        #     self.redirect_uri = f"https://{custom_domain}/"
        # elif railway_domain == 'pxn.app.br':
        #     self.redirect_uri = f"https://{railway_domain}/"
        # else:
        #     self.redirect_uri = "https://web-production-e80e8.up.railway.app/"
        
        print(f"[DEBUG] Using redirect URI: {self.redirect_uri}")
        
        # Store alternative redirect URIs for validation
        self.alternative_redirect_uris = [
            "https://pxn.app.br/",
            "https://web-production-e80e8.up.railway.app/"
        ]
        
        self.auth_base_url = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect"
        # According to the API documentation, the correct base URL is:
        self.api_base_url = "https://api.tiny.com.br/public-api/v3"
        
        # Try Redis, fallback to file storage
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
            print(f"[DEBUG] Attempting Redis connection: {redis_url}")
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            self.use_redis = True
            print("[DEBUG] Redis connection successful")
        except Exception as e:
            print(f"[DEBUG] Redis connection failed: {str(e)}")
            self.use_redis = False
            # Use a persistent directory instead of /tmp
            import pathlib
            token_dir = pathlib.Path.home() / '.tiny_oauth'
            token_dir.mkdir(exist_ok=True)
            self.token_file = str(token_dir / 'tokens.json')
            print(f"[DEBUG] Using file storage: {self.token_file}")
    
    def get_auth_url(self):
        """Generate OAuth authorization URL"""
        # According to the API documentation, only 'openid' scope is valid
        scope = 'openid'
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': scope,
            'response_type': 'code',
            'prompt': 'login'  # Force re-authentication
        }
        
        print(f"[DEBUG] OAuth scopes requested: {scope}")
        return f"{self.auth_base_url}/auth?{urlencode(params)}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        token_url = f"{self.auth_base_url}/token"
        
        # The redirect_uri must match exactly what was used in the authorization request
        # If Tiny redirected to /dashboard, we might need to use that
        redirect_uri = self.redirect_uri
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        print(f"[DEBUG] Token exchange URL: {token_url}")
        print(f"[DEBUG] Token exchange redirect_uri: {redirect_uri}")
        print(f"[DEBUG] Token exchange data: {data}")
        
        try:
            # Add headers that might be required
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            response = requests.post(token_url, data=data, headers=headers)
            print(f"[DEBUG] Token response status: {response.status_code}")
            print(f"[DEBUG] Token response headers: {dict(response.headers)}")
            print(f"[DEBUG] Token response: {response.text}")
            
            if response.status_code == 200:
                token_data = response.json()
                self._store_tokens(token_data)
                return token_data
            else:
                # Parse error response
                try:
                    error_data = response.json()
                    print(f"[DEBUG] Token error response: {error_data}")
                    error_msg = error_data.get('error_description', error_data.get('error', 'Unknown error'))
                    print(f"[DEBUG] Token exchange failed: {error_msg}")
                except:
                    print(f"[DEBUG] Token exchange failed with status {response.status_code}: {response.text}")
                    
        except Exception as e:
            print(f"[DEBUG] Token exchange error: {str(e)}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        
        return None
    
    def get_access_token(self):
        """Get valid access token, refresh if needed"""
        tokens = self._get_stored_tokens()
        if not tokens:
            return None
            
        # Check if token is expired
        if tokens.get('expires_at', 0) < time.time():
            # Try to refresh
            return self._refresh_token(tokens.get('refresh_token'))
        
        return tokens.get('access_token')
    
    def get_account_info(self):
        """Get account information to determine available endpoints"""
        token = self.get_access_token()
        if not token:
            return None
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        # Try info-conta endpoint from documentation
        info_url = f"{self.api_base_url}/info-conta"
        
        try:
            print(f"[DEBUG] Getting account info from: {info_url}")
            response = requests.get(info_url, headers=headers, timeout=5)
            print(f"[DEBUG] Account info response: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[DEBUG] Account info error: {response.text[:200]}")
        except Exception as e:
            print(f"[DEBUG] Error getting account info: {str(e)}")
        
        return None
    
    def validate_token(self):
        """Test if the current token is valid by making a simple API call"""
        token = self.get_access_token()
        if not token:
            return False, "No token available"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        # According to documentation, try the produtos endpoint with proper parameters
        test_url = f"{self.api_base_url}/produtos?limit=1&offset=0"
        
        try:
            print(f"[DEBUG] Testing token with URL: {test_url}")
            response = requests.get(test_url, headers=headers, timeout=5)
            print(f"[DEBUG] Token test response: {response.status_code}")
            
            if response.status_code == 200:
                return True, "Token is valid"
            elif response.status_code == 401:
                print(f"[DEBUG] 401 Response: {response.text[:200]}")
                # Check if we need empresa context
                if 'empresa' in response.text.lower():
                    return False, "Need to select empresa/company context"
                return False, "Token is expired or invalid - need to re-authenticate"
            elif response.status_code == 403:
                return False, "Access forbidden - check permissions"
            elif response.status_code == 404:
                return False, "API endpoint not found"
            else:
                return False, f"Unexpected status: {response.status_code}"
        except Exception as e:
            return False, f"Error validating token: {str(e)}"
    
    def _refresh_token(self, refresh_token):
        """Refresh access token"""
        if not refresh_token:
            return None
            
        token_url = f"{self.auth_base_url}/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self._store_tokens(token_data)
            return token_data.get('access_token')
        return None
    
    def _store_tokens(self, token_data):
        """Store tokens with expiration"""
        # Calculate expiration time
        expires_in = token_data.get('expires_in', 3600)
        expires_at = time.time() + expires_in - 60  # 1 minute buffer
        
        tokens = {
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': expires_at
        }
        
        print(f"[DEBUG] Storing tokens - use_redis: {self.use_redis}")
        print(f"[DEBUG] Access token: {tokens['access_token'][:20] if tokens['access_token'] else 'None'}...")
        
        if self.use_redis:
            # Store in Redis with TTL
            try:
                self.redis_client.setex('tiny_tokens', 86400, json.dumps(tokens))  # 24h TTL
                print("[DEBUG] Tokens stored in Redis")
            except Exception as e:
                print(f"[DEBUG] Redis storage error: {str(e)}")
        else:
            # Store in file
            try:
                with open(self.token_file, 'w') as f:
                    json.dump(tokens, f)
                print(f"[DEBUG] Tokens stored in file: {self.token_file}")
            except Exception as e:
                print(f"[DEBUG] File storage error: {str(e)}")
    
    def _get_stored_tokens(self):
        """Retrieve stored tokens"""
        print(f"[DEBUG] Getting stored tokens - use_redis: {self.use_redis}")
        
        if self.use_redis:
            try:
                data = self.redis_client.get('tiny_tokens')
                if data:
                    tokens = json.loads(data)
                    print(f"[DEBUG] Retrieved token from Redis: {tokens['access_token'][:20] if tokens.get('access_token') else 'None'}...")
                    return tokens
                else:
                    print("[DEBUG] No tokens in Redis")
            except Exception as e:
                print(f"[DEBUG] Redis retrieval error: {str(e)}")
        else:
            if os.path.exists(self.token_file):
                try:
                    with open(self.token_file, 'r') as f:
                        tokens = json.load(f)
                    print(f"[DEBUG] Retrieved token from file: {tokens['access_token'][:20] if tokens.get('access_token') else 'None'}...")
                    return tokens
                except Exception as e:
                    print(f"[DEBUG] File retrieval error: {str(e)}")
            else:
                print(f"[DEBUG] Token file does not exist: {self.token_file}")
        return None
    
    def get_openid_configuration(self):
        """Get OpenID configuration to check available scopes"""
        config_url = f"{self.auth_base_url}/.well-known/openid-configuration"
        try:
            response = requests.get(config_url, timeout=5)
            if response.status_code == 200:
                config = response.json()
                print("[DEBUG] OpenID Configuration retrieved")
                if 'scopes_supported' in config:
                    print(f"[DEBUG] Supported scopes: {config['scopes_supported']}")
                return config
        except Exception as e:
            print(f"[DEBUG] Error getting OpenID config: {str(e)}")
        return None
    
    def logout(self):
        """Clear stored tokens to force re-authentication"""
        print("[DEBUG] Clearing stored tokens")
        
        if self.use_redis:
            try:
                self.redis_client.delete('tiny_tokens')
                print("[DEBUG] Tokens cleared from Redis")
            except Exception as e:
                print(f"[DEBUG] Redis clear error: {str(e)}")
        else:
            if os.path.exists(self.token_file):
                try:
                    os.remove(self.token_file)
                    print(f"[DEBUG] Token file removed: {self.token_file}")
                except Exception as e:
                    print(f"[DEBUG] File removal error: {str(e)}")
    
    def ultra_verbose_debug(self):
        """ULTRA VERBOSE debugging - deixar TUDO claro!"""
        import base64
        import json as json_lib
        from datetime import datetime
        
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
        # TEST 1: Token Analysis
        token = self.get_access_token()
        if not token:
            debug_info["tests"].append({"test": "token_check", "result": "NO TOKEN FOUND!"})
            return debug_info
        
        debug_info["tests"].append({
            "test": "token_exists", 
            "result": "YES",
            "token_length": len(token),
            "token_preview": f"{token[:50]}...{token[-20:]}"
        })
        
        # Decode JWT token completely
        try:
            parts = token.split('.')
            if len(parts) == 3:
                # Decode header
                header = base64.b64decode(parts[0] + '=' * (4 - len(parts[0]) % 4))
                header_data = json_lib.loads(header)
                
                # Decode payload
                payload = base64.b64decode(parts[1] + '=' * (4 - len(parts[1]) % 4))
                payload_data = json_lib.loads(payload)
                
                debug_info["tests"].append({
                    "test": "jwt_decode",
                    "result": "SUCCESS",
                    "header": header_data,
                    "payload": payload_data,
                    "all_claims": list(payload_data.keys()),
                    "roles": payload_data.get('roles', {}),
                    "email": payload_data.get('email', 'NOT FOUND'),
                    "sub": payload_data.get('sub', 'NOT FOUND'),
                    "empresa_related_fields": {k: v for k, v in payload_data.items() if 'emp' in k.lower() or 'company' in k.lower()}
                })
        except Exception as e:
            debug_info["tests"].append({
                "test": "jwt_decode",
                "result": "FAILED",
                "error": str(e)
            })
        
        # TEST 2: Try EVERY possible header combination
        base_headers = [
            {"Authorization": f"Bearer {token}"},
            {"Authorization": f"Bearer {token}", "Accept": "application/json"},
            {"Authorization": f"Bearer {token}", "Accept": "application/json", "Content-Type": "application/json"},
            {"Authorization": f"Bearer {token}", "Accept": "*/*"},
            {"Authorization": token},  # Without Bearer
            {"Authorization": f"Bearer {token}", "X-Empresa": "phoenixfundicao"},
            {"Authorization": f"Bearer {token}", "X-Company": "phoenixfundicao"},
            {"Authorization": f"Bearer {token}", "X-Empresa-Id": "phoenixfundicao"},
            {"Authorization": f"Bearer {token}", "X-Tenant": "phoenixfundicao"},
        ]
        
        # TEST 3: Try MANY different endpoints (including empresa-specific)
        test_endpoints = [
            "/produtos?limit=1",
            "/produtos",
            "/info-conta",
            "/empresas",
            "/empresas/phoenixfundicao",
            "/empresa/phoenixfundicao/produtos",
            "/phoenixfundicao/produtos",
            "/conta",
            "/user",
            "/me",
            "/whoami",
            "/api/info",
            "/info",
            "/empresa",
            "/empresa/phoenixfundicao",
            "/",
            "",
        ]
        
        # TEST 4: Try different base URLs too!
        base_urls = [
            "https://api.tiny.com.br/public-api/v3",
            "https://api.tiny.com.br/api/v3",
            "https://api.tiny.com.br/v3",
            "https://api.tiny.com.br/openapi/v3",
            "https://erp.tiny.com.br/public-api/v3",
            "https://erp.tiny.com.br/api/v3",
        ]
        
        # Test each combination (but limit to avoid timeout)
        test_count = 0
        for base_url in base_urls[:3]:  # Test first 3 base URLs
            for endpoint in test_endpoints[:5]:  # Test first 5 endpoints
                for headers in base_headers[:5]:  # Test first 5 header combinations
                    test_count += 1
                    test_info = {
                        "test_number": test_count,
                        "base_url": base_url,
                        "endpoint": endpoint,
                        "full_url": f"{base_url}{endpoint}",
                        "headers": headers
                    }
                    
                    try:
                        response = requests.get(
                            f"{base_url}{endpoint}", 
                            headers=headers, 
                            timeout=2,
                            allow_redirects=False
                        )
                        
                        test_info["response"] = {
                            "status_code": response.status_code,
                            "reason": response.reason,
                            "headers": dict(response.headers),
                            "body_length": len(response.text),
                            "body": response.text[:1000],  # First 1000 chars
                            "is_json": False
                        }
                        
                        # Try to parse as JSON
                        try:
                            json_body = response.json()
                            test_info["response"]["is_json"] = True
                            test_info["response"]["json_body"] = json_body
                        except:
                            pass
                        
                        # Special attention to 401 responses
                        if response.status_code == 401:
                            test_info["401_analysis"] = {
                                "www_authenticate": response.headers.get('WWW-Authenticate', 'NOT PRESENT'),
                                "body_contains_empresa": 'empresa' in response.text.lower(),
                                "body_contains_company": 'company' in response.text.lower(),
                                "body_contains_tenant": 'tenant' in response.text.lower(),
                                "body_contains_phoenix": 'phoenix' in response.text.lower()
                            }
                        
                    except Exception as e:
                        test_info["response"] = {
                            "error": str(e),
                            "error_type": type(e).__name__
                        }
                    
                    debug_info["tests"].append(test_info)
                    
                    # If we find a successful response, highlight it!
                    if test_info.get("response", {}).get("status_code") == 200:
                        debug_info["SUCCESS_FOUND"] = test_info
                        break
        
        # TEST 5: Raw curl equivalent
        import subprocess
        try:
            curl_command = [
                'curl', '-v',
                '-H', f'Authorization: Bearer {token}',
                '-H', 'Accept: application/json',
                'https://api.tiny.com.br/public-api/v3/produtos?limit=1'
            ]
            curl_result = subprocess.run(curl_command, capture_output=True, text=True, timeout=5)
            debug_info["curl_test"] = {
                "command": ' '.join(curl_command),
                "stdout": curl_result.stdout[:500],
                "stderr": curl_result.stderr[:500],
                "return_code": curl_result.returncode
            }
        except Exception as e:
            debug_info["curl_test"] = {"error": str(e)}
        
        return debug_info
    
    def fetch_product(self, search_term):
        """
        Fetch product from Tiny API V3
        First tries local DB, then searches Tiny API by ID, code, or name
        
        API Documentation: https://api.tiny.com.br/public-api/v3
        
        Examples:
        - By ID: GET /produtos/{id}
        - By code: GET /produtos?codigo=PH-504&limit=20
        """
        # Import local to avoid circular import
        from app.products_db import get_product_by_code, get_product_by_id
        
        # First try local database
        local_product = get_product_by_code(search_term)
        if local_product:
            print(f"[DEBUG] Found product locally: {local_product}")
            product_id = local_product['id']
        else:
            # Try to parse as ID
            try:
                product_id = int(search_term)
            except ValueError:
                product_id = None
        
        token = self.get_access_token()
        if not token:
            print("[DEBUG] No access token available")
            return None
            
        # According to the API documentation, we need to get the empresa ID from the token
        # The API requires the empresa ID in the URL pattern
        import base64
        import json as json_lib
        
        empresa_id = None
        try:
            # Decode JWT to get empresa ID
            parts = token.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.b64decode(payload)
                token_data = json_lib.loads(decoded)
                # Try to extract empresa ID from token claims
                empresa_id = token_data.get('empresa_id') or token_data.get('emp_id') or token_data.get('company_id')
                print(f"[DEBUG] Token claims: {list(token_data.keys())}")
        except Exception as e:
            print(f"[DEBUG] Error decoding token for empresa ID: {str(e)}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Method 1: Try direct ID search if we have an ID
        if product_id:
            url = f"{self.api_base_url}/produtos/{product_id}"
            print(f"[DEBUG] Trying direct ID search: {url}")
            
            try:
                print(f"[DEBUG] Request URL: {url}")
                print(f"[DEBUG] Request Headers: {headers}")
                response = requests.get(url, headers=headers)
                print(f"[DEBUG] Response Status: {response.status_code}")
                print(f"[DEBUG] Response Headers: {dict(response.headers)}")
                print(f"[DEBUG] Response Body: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    # V3 returns single product, not array
                    return {"data": [data], "registros": 1}
                elif response.status_code == 401:
                    print("[DEBUG] Token expired, attempting refresh")
                    # Try to refresh token
                    new_token = self._refresh_token(self._get_stored_tokens().get('refresh_token'))
                    if new_token:
                        headers['Authorization'] = f'Bearer {new_token}'
                        response = requests.get(url, headers=headers)
                        if response.status_code == 200:
                            data = response.json()
                            return {"data": [data], "registros": 1}
            except Exception as e:
                print(f"[DEBUG] Error in ID search: {str(e)}")
        
        # Method 2: Try search by code
        url = f"{self.api_base_url}/produtos"
        params = {
            'pagina': 1,
            'numeroRegistros': 20,
            'codigo': search_term
        }
        
        print(f"[DEBUG] Trying code search: {url}")
        print(f"[DEBUG] Request Params: {params}")
        
        try:
            print(f"[DEBUG] Request Headers: {headers}")
            response = requests.get(url, headers=headers, params=params)
            print(f"[DEBUG] Full URL: {response.url}")
            print(f"[DEBUG] Response Status: {response.status_code}")
            print(f"[DEBUG] Response Headers: {dict(response.headers)}")
            print(f"[DEBUG] Response Body: {response.text}")
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[DEBUG] Error in code search: {str(e)}")
        
        # Method 3: Try search by name
        params = {
            'pagina': 1,
            'numeroRegistros': 20,
            'nome': search_term
        }
        
        print(f"[DEBUG] Trying name search: {url}")
        print(f"[DEBUG] Request Params: {params}")
        
        try:
            print(f"[DEBUG] Request Headers: {headers}")
            response = requests.get(url, headers=headers, params=params)
            print(f"[DEBUG] Full URL: {response.url}")
            print(f"[DEBUG] Response Status: {response.status_code}")
            print(f"[DEBUG] Response Headers: {dict(response.headers)}")
            print(f"[DEBUG] Response Body: {response.text}")
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[DEBUG] Error in name search: {str(e)}")
        
        return None