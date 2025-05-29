#!/usr/bin/env python3
"""Test OAuth callback handling"""

from app.tiny_oauth import TinyOAuth

# Initialize OAuth handler
tiny_oauth = TinyOAuth()

# Test with the code from the URL
test_code = "cb786bf4-c822-4320-9f68-53669adf5e6b.e496af24-e078-4669-8d0c-d8375b9448cd.9144d1e4-6ed0-4fd1-8305-f60e54a5aa1f"

print("[OAuth] Testing token exchange")
print(f"  Code: {test_code[:30]}...")
print(f"  Redirect: {tiny_oauth.redirect_uri}")

# Try to exchange the code
result = tiny_oauth.exchange_code_for_token(test_code)

print(f"\n[Result] {'Success' if result else 'Failed'}")

if result:
    print(f"  Token: ...{result.get('access_token', '')[-20:]}")
    print(f"  Type: {result.get('token_type', 'N/A')}")
    print(f"  Expires: {result.get('expires_in', 'N/A')}s")
else:
    print("  Check logs for error details")