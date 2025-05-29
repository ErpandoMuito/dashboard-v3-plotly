#!/usr/bin/env python3
"""Check OAuth status and provide debugging info"""

from app.tiny_oauth import TinyOAuth
import json

tiny_oauth = TinyOAuth()

print("=== OAuth Configuration ===")
print(f"Client ID: {tiny_oauth.client_id}")
print(f"Redirect URI: {tiny_oauth.redirect_uri}")
print(f"Auth URL: {tiny_oauth.auth_base_url}")
print(f"API URL: {tiny_oauth.api_base_url}")

print("\n=== Token Storage ===")
print(f"Using Redis: {tiny_oauth.use_redis}")
if not tiny_oauth.use_redis:
    print(f"Token file: {tiny_oauth.token_file}")

print("\n=== Current Token Status ===")
tokens = tiny_oauth._get_stored_tokens()
if tokens:
    print("Tokens found!")
    print(f"Access token: {tokens.get('access_token', '')[:50]}...")
    import time
    expires_at = tokens.get('expires_at', 0)
    current_time = time.time()
    if expires_at > current_time:
        print(f"Token expires in: {(expires_at - current_time)/60:.1f} minutes")
    else:
        print("Token is EXPIRED")
else:
    print("No tokens stored")

print("\n=== Testing Token Validity ===")
is_valid, msg = tiny_oauth.validate_token()
print(f"Token valid: {is_valid}")
print(f"Validation message: {msg}")

print("\n=== Next Steps ===")
if not tokens or not is_valid:
    print("You need to authenticate with Tiny:")
    print("1. Go to your app at https://web-production-e80e8.up.railway.app/")
    print("2. Login with admin/admin123")
    print("3. Click 'Conectar ao Tiny'")
    print("4. Complete the OAuth flow in Tiny")
    print("5. You'll be redirected back to the dashboard")
    print("\nAuth URL for manual testing:")
    print(tiny_oauth.get_auth_url())
else:
    print("Token is valid! You can make API calls.")