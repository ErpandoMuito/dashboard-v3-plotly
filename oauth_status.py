#!/usr/bin/env python3
"""Check OAuth status and provide debugging info"""

from app.tiny_oauth import TinyOAuth
import json

tiny_oauth = TinyOAuth()

print("[OAuth] Configuration")
print(f"  Client ID: ...{tiny_oauth.client_id[-10:]}")
print(f"  Redirect: {tiny_oauth.redirect_uri}")
print(f"  API Base: {tiny_oauth.api_base_url}")

print("\n[Storage] Type: {'Redis' if tiny_oauth.use_redis else 'File'}")

print("\n[Token] Status")
tokens = tiny_oauth._get_stored_tokens()
if tokens:
    print(f"  Found: ...{tokens.get('access_token', '')[-20:]}")
    import time
    expires_at = tokens.get('expires_at', 0)
    current_time = time.time()
    if expires_at > current_time:
        print(f"  Expires in: {(expires_at - current_time)/60:.0f} minutes")
    else:
        print("  Status: EXPIRED")
else:
    print("  Status: No tokens")

print("\n[Validation] Testing token...")
is_valid, msg = tiny_oauth.validate_token()
print(f"  Valid: {is_valid}")
print(f"  Message: {msg}")

if not tokens or not is_valid:
    print("\n[Action] Authenticate at: https://web-production-e80e8.up.railway.app/")
    print("  1. Login: admin/admin123")
    print("  2. Click 'Conectar ao Tiny'")
    print("  3. Complete OAuth in Tiny")
else:
    print("\n[Status] Ready to make API calls!")