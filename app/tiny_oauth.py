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
        self.redirect_uri = "https://web-production-e80e8.up.railway.app/"
        self.auth_base_url = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect"
        self.api_base_url = "https://api.tiny.com.br/api/v3"
        
        # Try Redis, fallback to file storage
        try:
            self.redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
            self.redis_client.ping()
            self.use_redis = True
        except:
            self.use_redis = False
            self.token_file = '/tmp/tiny_tokens.json'
    
    def get_auth_url(self):
        """Generate OAuth authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid',
            'response_type': 'code'
        }
        return f"{self.auth_base_url}/auth?{urlencode(params)}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        token_url = f"{self.auth_base_url}/token"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        print(f"[DEBUG] Token exchange URL: {token_url}")
        print(f"[DEBUG] Token exchange data: {data}")
        
        try:
            response = requests.post(token_url, data=data)
            print(f"[DEBUG] Token response status: {response.status_code}")
            print(f"[DEBUG] Token response: {response.text}")
            
            if response.status_code == 200:
                token_data = response.json()
                self._store_tokens(token_data)
                return token_data
        except Exception as e:
            print(f"[DEBUG] Token exchange error: {str(e)}")
        
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
        
        if self.use_redis:
            # Store in Redis with TTL
            self.redis_client.setex('tiny_tokens', 86400, json.dumps(tokens))  # 24h TTL
        else:
            # Store in file
            with open(self.token_file, 'w') as f:
                json.dump(tokens, f)
    
    def _get_stored_tokens(self):
        """Retrieve stored tokens"""
        if self.use_redis:
            data = self.redis_client.get('tiny_tokens')
            if data:
                return json.loads(data)
        else:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    return json.load(f)
        return None
    
    def fetch_product(self, search_term):
        """
        Fetch product from Tiny API V3
        First tries local DB, then searches Tiny API by ID, code, or name
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
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Method 1: Try direct ID search if we have an ID
        if product_id:
            url = f"{self.api_base_url}/produtos/{product_id}"
            print(f"[DEBUG] Trying direct ID search: {url}")
            
            try:
                response = requests.get(url, headers=headers)
                print(f"[DEBUG] URL: {response.url}")
                print(f"[DEBUG] Status: {response.status_code}")
                print(f"[DEBUG] Headers sent: {headers}")
                print(f"[DEBUG] Response: {response.text}")
                
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
            'numeroRegistros': 50,
            'codigo': search_term
        }
        
        print(f"[DEBUG] Trying code search: {url} with params: {params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"[DEBUG] URL: {response.url}")
            print(f"[DEBUG] Status: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[DEBUG] Error in code search: {str(e)}")
        
        # Method 3: Try search by name
        params = {
            'pagina': 1,
            'numeroRegistros': 50,
            'nome': search_term
        }
        
        print(f"[DEBUG] Trying name search: {url} with params: {params}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            print(f"[DEBUG] URL: {response.url}")
            print(f"[DEBUG] Status: {response.status_code}")
            print(f"[DEBUG] Response: {response.text}")
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[DEBUG] Error in name search: {str(e)}")
        
        return None