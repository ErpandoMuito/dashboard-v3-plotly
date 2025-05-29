#!/usr/bin/env python3
"""Test OAuth callback handling"""

from app.tiny_oauth import TinyOAuth

# Initialize OAuth handler
tiny_oauth = TinyOAuth()

# Test with the code from the URL
test_code = "cb786bf4-c822-4320-9f68-53669adf5e6b.e496af24-e078-4669-8d0c-d8375b9448cd.9144d1e4-6ed0-4fd1-8305-f60e54a5aa1f"

print("Testing OAuth token exchange...")
print(f"Code: {test_code}")
print(f"Redirect URI: {tiny_oauth.redirect_uri}")
print("\n" + "="*50 + "\n")

# Try to exchange the code
result = tiny_oauth.exchange_code_for_token(test_code)

print("\n" + "="*50 + "\n")
print(f"Token exchange result: {result}")

if result:
    print("\nSuccess! Token obtained:")
    print(f"Access token: {result.get('access_token', '')[:50]}...")
    print(f"Token type: {result.get('token_type', 'N/A')}")
    print(f"Expires in: {result.get('expires_in', 'N/A')} seconds")
else:
    print("\nFailed to exchange code for token")