#!/usr/bin/env python3
"""
Test script to verify proxy connectivity
"""

import requests
import os
import sys

def test_proxy():
    """Test if proxy is working"""
    print("Testing proxy connectivity...")
    
    # Check environment variables
    http_proxy = os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('HTTPS_PROXY')
    
    print(f"HTTP_PROXY: {http_proxy}")
    print(f"HTTPS_PROXY: {https_proxy}")
    
    try:
        # Test with a simple request
        response = requests.get('http://httpbin.org/ip', timeout=10)
        print(f"Response status: {response.status_code}")
        print(f"Your IP: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Proxy test successful!")
            return True
        else:
            print("❌ Proxy test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing proxy: {e}")
        return False

if __name__ == "__main__":
    success = test_proxy()
    sys.exit(0 if success else 1) 