#!/usr/bin/env python3
"""
Test script to verify proxy connectivity
"""

import os
import requests
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))
from common.config import CONFIG

def test_proxy():
    """Test if proxy is working"""
    print("Testing proxy connectivity...")
    
    # Check environment variables
    http_proxy = os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('HTTPS_PROXY')
    
    print(f"HTTP_PROXY: {http_proxy}")
    print(f"HTTPS_PROXY: {https_proxy}")
    
    # Check config
    if CONFIG['proxy']['enabled']:
        print(f"Config proxy: {CONFIG['proxy']['url']}")
        print(f"Config auth: {CONFIG['proxy']['auth']}")
    
    try:
        # Test with proxy if configured
        proxies = None
        if CONFIG['proxy']['enabled'] and CONFIG['proxy']['url']:
            proxies = {
                'http': CONFIG['proxy']['url'],
                'https': CONFIG['proxy']['url']
            }
            
            # Add authentication if provided
            if CONFIG['proxy']['auth']:
                from urllib.parse import urlparse
                proxy_url = urlparse(CONFIG['proxy']['url'])
                if '@' not in CONFIG['proxy']['url']:
                    username, password = CONFIG['proxy']['auth'].split(':', 1)
                    proxies['http'] = f"{proxy_url.scheme}://{username}:{password}@{proxy_url.netloc}"
                    proxies['https'] = f"{proxy_url.scheme}://{username}:{password}@{proxy_url.netloc}"
        
        # Test connection
        response = requests.get(
            'https://httpbin.org/ip', 
            proxies=proxies, 
            timeout=10,
            verify=CONFIG['proxy']['verify_ssl']
        )
        
        if response.status_code == 200:
            print("✅ Proxy test successful!")
            print(f"Your IP: {response.json()}")
            return True
        else:
            print("❌ Proxy test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing proxy: {e}")
        return False

def test_specific_proxy(proxy_url, auth=None):
    """Test a specific proxy URL"""
    print(f"Testing specific proxy: {proxy_url}")
    
    try:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Add authentication if provided
        if auth:
            from urllib.parse import urlparse
            proxy_url_parsed = urlparse(proxy_url)
            if '@' not in proxy_url:
                username, password = auth.split(':', 1)
                proxies['http'] = f"{proxy_url_parsed.scheme}://{username}:{password}@{proxy_url_parsed.netloc}"
                proxies['https'] = f"{proxy_url_parsed.scheme}://{username}:{password}@{proxy_url_parsed.netloc}"
        
        response = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            print("✅ Proxy test successful!")
            print(f"Your IP: {response.json()}")
            return True
        else:
            print("❌ Proxy test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing proxy: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test proxy connectivity")
    parser.add_argument("--proxy", help="Test specific proxy URL")
    parser.add_argument("--auth", help="Proxy authentication (username:password)")
    
    args = parser.parse_args()
    
    if args.proxy:
        success = test_specific_proxy(args.proxy, args.auth)
    else:
        success = test_proxy()
    
    sys.exit(0 if success else 1) 