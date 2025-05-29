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
    
    def fetch_product(self, sku):
        """Fetch product from Tiny API"""
        token = self.get_access_token()
        if not token:
            return None
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.api_base_url}/produtos"
        params = {'cpesquisa': sku}
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        return None