#!/usr/bin/env python3
"""
Test script to debug Tiny API authentication with reduced verbose output
"""
import requests
import json
import sys
from app.tiny_oauth import TinyOAuth

def test_api():
    print("=" * 50)
    print("TINY API CONNECTION TEST")
    print("=" * 50)
    
    tiny = TinyOAuth()
    token = tiny.get_access_token()
    
    if not token:
        print("❌ No token available!")
        return
    
    print(f"✅ Token: {token[:30]}...")
    
    # Test endpoints
    endpoints = [
        ('info-conta', 'https://api.tiny.com.br/public-api/v3/info-conta'),
        ('produtos', 'https://api.tiny.com.br/public-api/v3/produtos?limit=1'),
        ('categorias', 'https://api.tiny.com.br/public-api/v3/categorias/todas')
    ]
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    print("\n[Headers]")
    print(f"  Auth: Bearer {token[:20]}...")
    print(f"  Accept: {headers['Accept']}")
    
    results = []
    for name, url in endpoints:
        print(f"\n[Test] {name}")
        print(f"  URL: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Success! Type: {type(data).__name__}")
                if isinstance(data, dict) and 'data' in data:
                    print(f"  Data items: {len(data.get('data', []))}")
                results.append((name, True))
            else:
                print(f"  ❌ Error: {response.text[:100]}...")
                results.append((name, False))
                
        except requests.exceptions.Timeout:
            print(f"  ⏱️ Timeout after 10s")
            results.append((name, False))
        except Exception as e:
            print(f"  ❌ Exception: {type(e).__name__}: {str(e)[:50]}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    success = sum(1 for _, ok in results if ok)
    print(f"✅ Successful: {success}/{len(results)}")
    print(f"❌ Failed: {len(results) - success}/{len(results)}")
    
    if success == 0:
        print("\n⚠️  All API calls failed - check authentication")
    elif success < len(results):
        print("\n⚠️  Some API calls failed - partial connectivity")
    else:
        print("\n✅ All API calls successful - full connectivity")
    
    print("=" * 50)

if __name__ == "__main__":
    test_api()