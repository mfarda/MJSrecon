#!/usr/bin/env python3
"""
Comprehensive proxy testing script for WARP proxy and MJSRecon
"""

import os
import requests
import sys
import socket
import subprocess
from pathlib import Path
from urllib.parse import urlparse

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))
from common.config import CONFIG

def test_warp_proxy_connection(proxy_url="socks5://127.0.0.1:40000"):
    """Test WARP proxy connection specifically"""
    print(f"🔍 Testing WARP proxy connection: {proxy_url}")
    
    # Test 1: Check if port is listening
    print("\n1️⃣ Testing if proxy port is listening...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 40000))
        sock.close()
        
        if result == 0:
            print("✅ Port 40000 is listening on 127.0.0.1")
        else:
            print("❌ Port 40000 is NOT listening on 127.0.0.1")
            print("   Make sure WARP proxy is running!")
            return False
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return False
    
    # Test 2: Test HTTP request through proxy
    print("\n2️⃣ Testing HTTP request through WARP proxy...")
    try:
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        response = requests.get(
            'https://httpbin.org/ip', 
            proxies=proxies, 
            timeout=15,
            verify=False
        )
        
        if response.status_code == 200:
            ip_info = response.json()
            print("✅ HTTP request successful!")
            print(f"   Your IP: {ip_info.get('origin', 'Unknown')}")
            return True
        else:
            print(f"❌ HTTP request failed with status: {response.status_code}")
            return False
            
    except requests.exceptions.ProxyError as e:
        print(f"❌ Proxy connection error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Request timeout: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_mjsrecon_proxy_integration():
    """Test if MJSRecon can use the proxy"""
    print("\n3️⃣ Testing MJSRecon proxy integration...")
    
    # Check current environment
    http_proxy = os.environ.get('HTTP_PROXY')
    https_proxy = os.environ.get('HTTPS_PROXY')
    
    print(f"   HTTP_PROXY env var: {http_proxy}")
    print(f"   HTTPS_PROXY env var: {https_proxy}")
    
    # Check CONFIG
    if CONFIG['proxy']['enabled']:
        print(f"   CONFIG proxy enabled: {CONFIG['proxy']['enabled']}")
        print(f"   CONFIG proxy URL: {CONFIG['proxy']['url']}")
    else:
        print("   CONFIG proxy: Not enabled")
    
    # Test with CONFIG proxy if enabled
    if CONFIG['proxy']['enabled'] and CONFIG['proxy']['url']:
        try:
            proxies = {
                'http': CONFIG['proxy']['url'],
                'https': CONFIG['proxy']['url']
            }
            
            response = requests.get(
                'https://httpbin.org/ip', 
                proxies=proxies, 
                timeout=15,
                verify=CONFIG['proxy']['verify_ssl']
            )
            
            if response.status_code == 200:
                print("✅ MJSRecon proxy configuration works!")
                return True
            else:
                print(f"❌ MJSRecon proxy test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ MJSRecon proxy test error: {e}")
            return False
    else:
        print("⚠️  MJSRecon proxy not configured - run with --proxy flag")
        return False

def test_external_tools_proxy():
    """Test if external tools can use the proxy via environment variables"""
    print("\n4️⃣ Testing external tools proxy support...")
    
    # Set environment variables temporarily
    original_http_proxy = os.environ.get('HTTP_PROXY')
    original_https_proxy = os.environ.get('HTTPS_PROXY')
    
    try:
        os.environ['HTTP_PROXY'] = 'socks5://127.0.0.1:40000'
        os.environ['HTTPS_PROXY'] = 'socks5://127.0.0.1:40000'
        
        print("   Set HTTP_PROXY=socks5://127.0.0.1:40000")
        print("   Set HTTPS_PROXY=socks5://127.0.0.1:40000")
        
        # Test curl (if available)
        try:
            result = subprocess.run(
                ['curl', '-s', '--connect-timeout', '10', 'https://httpbin.org/ip'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print("✅ curl works with proxy")
            else:
                print(f"❌ curl failed: {result.stderr}")
        except FileNotFoundError:
            print("⚠️  curl not found, skipping curl test")
        
        # Test wget (if available)
        try:
            result = subprocess.run(
                ['wget', '-qO-', '--timeout=10', 'https://httpbin.org/ip'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                print("✅ wget works with proxy")
            else:
                print(f"❌ wget failed: {result.stderr}")
        except FileNotFoundError:
            print("⚠️  wget not found, skipping wget test")
            
    finally:
        # Restore original environment
        if original_http_proxy:
            os.environ['HTTP_PROXY'] = original_http_proxy
        else:
            os.environ.pop('HTTP_PROXY', None)
            
        if original_https_proxy:
            os.environ['HTTPS_PROXY'] = original_https_proxy
        else:
            os.environ.pop('HTTPS_PROXY', None)

def test_warp_status():
    """Check WARP status and configuration"""
    print("\n5️⃣ Checking WARP status...")
    
    # Check if warp-cli is available
    try:
        result = subprocess.run(['warp-cli', 'status'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ warp-cli found")
            print(f"   Status: {result.stdout.strip()}")
        else:
            print("❌ warp-cli not working properly")
    except FileNotFoundError:
        print("⚠️  warp-cli not found - WARP may not be installed")
    
    # Check if WARP proxy is enabled
    try:
        result = subprocess.run(['warp-cli', 'settings'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            if 'proxy' in result.stdout.lower():
                print("✅ WARP proxy settings found")
            else:
                print("⚠️  WARP proxy settings not found in output")
        else:
            print("❌ Could not get WARP settings")
    except FileNotFoundError:
        print("⚠️  warp-cli not available for settings check")

def main():
    """Main testing function"""
    print("🚀 WARP Proxy Comprehensive Test")
    print("=" * 50)
    
    # Test 1: Basic WARP proxy connection
    warp_works = test_warp_proxy_connection()
    
    # Test 2: MJSRecon integration
    mjsrecon_works = test_mjsrecon_proxy_integration()
    
    # Test 3: External tools
    test_external_tools_proxy()
    
    # Test 4: WARP status
    test_warp_status()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    if warp_works:
        print("✅ WARP proxy is working")
    else:
        print("❌ WARP proxy is NOT working")
        
    if mjsrecon_works:
        print("✅ MJSRecon proxy integration is working")
    else:
        print("❌ MJSRecon proxy integration is NOT working")
    
    print("\n💡 RECOMMENDATIONS:")
    if not warp_works:
        print("   - Check if WARP is running: warp-cli status")
        print("   - Enable WARP proxy: warp-cli set-mode proxy")
        print("   - Check WARP proxy port: warp-cli settings")
    else:
        print("   - WARP proxy is working! You can use it with MJSRecon")
        print("   - Run: python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000")

if __name__ == "__main__":
    main() 