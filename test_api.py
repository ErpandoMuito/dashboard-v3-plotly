#!/usr/bin/env python3
"""
Test script to debug Tiny API authentication
"""
import requests
import json
import sys
from app.tiny_oauth import TinyOAuth

def test_api():
    tiny = TinyOAuth()
    token = tiny.get_access_token()
    
    if not token:
        print("No token available!")
        return
    
    print(f"Token: {token[:50]}...")
    
    # Test 1: Basic request
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    
    endpoints = [
        'https://api.tiny.com.br/public-api/v3/info-conta',
        'https://api.tiny.com.br/public-api/v3/produtos?limit=1',
        'https://api.tiny.com.br/public-api/v3/categorias/todas'
    ]
    
    for url in endpoints:
        print(f"\n=== Testing: {url} ===")
        try:
            response = requests.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 401:
                # Try without Bearer prefix
                headers2 = {
                    'Authorization': token,
                    'Accept': 'application/json'
                }
                print("\nTrying without Bearer prefix...")
                response2 = requests.get(url, headers=headers2)
                print(f"Status: {response2.status_code}")
                print(f"Response: {response2.text[:200]}...")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_api()