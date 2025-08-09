#!/usr/bin/env python3
"""
VPS-specific WARP proxy testing script
Run this on your VPS to test WARP proxy functionality
"""

import os
import requests
import sys
import socket
import subprocess
from pathlib import Path

def test_warp_proxy_on_vps():
    """Test WARP proxy specifically on VPS"""
    print("🔍 Testing WARP proxy on VPS...")
    
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
            return False
    except Exception as e:
        print(f"❌ Error checking port: {e}")
        return False
    
    # Test 2: Test HTTP request through proxy
    print("\n2️⃣ Testing HTTP request through WARP proxy...")
    try:
        proxies = {
            'http': 'socks5://127.0.0.1:40000',
            'https': 'socks5://127.0.0.1:40000'
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
        print("   This might be due to missing SOCKS support.")
        print("   Run: pip install requests[socks] PySocks")
        return False

def test_mjsrecon_with_proxy():
    """Test MJSRecon with proxy configuration"""
    print("\n3️⃣ Testing MJSRecon with proxy...")
    
    # Test a simple discovery command with proxy
    try:
        cmd = [
            'python', 'run_workflow.py', 
            'discovery', 
            '-t', 'example.com', 
            '--proxy', 'socks5://127.0.0.1:40000',
            '-o', './test_output'
        ]
        
        print(f"   Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ MJSRecon discovery with proxy works!")
            return True
        else:
            print(f"❌ MJSRecon failed with exit code: {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ MJSRecon test timed out")
        return False
    except Exception as e:
        print(f"❌ Error running MJSRecon: {e}")
        return False

def test_external_tools():
    """Test external tools with proxy"""
    print("\n4️⃣ Testing external tools with proxy...")
    
    # Set environment variables
    os.environ['HTTP_PROXY'] = 'socks5://127.0.0.1:40000'
    os.environ['HTTPS_PROXY'] = 'socks5://127.0.0.1:40000'
    
    tools_to_test = ['curl', 'wget', 'gau', 'waybackurls']
    working_tools = []
    
    for tool in tools_to_test:
        try:
            if tool == 'curl':
                result = subprocess.run(
                    ['curl', '-s', '--connect-timeout', '10', 'https://httpbin.org/ip'],
                    capture_output=True, text=True, timeout=15
                )
            elif tool == 'wget':
                result = subprocess.run(
                    ['wget', '-qO-', '--timeout=10', 'https://httpbin.org/ip'],
                    capture_output=True, text=True, timeout=15
                )
            elif tool == 'gau':
                result = subprocess.run(
                    ['gau', '--help'],
                    capture_output=True, text=True, timeout=10
                )
            elif tool == 'waybackurls':
                result = subprocess.run(
                    ['waybackurls', '--help'],
                    capture_output=True, text=True, timeout=10
                )
            
            if result.returncode == 0:
                print(f"✅ {tool} works with proxy")
                working_tools.append(tool)
            else:
                print(f"❌ {tool} failed")
                
        except FileNotFoundError:
            print(f"⚠️  {tool} not found")
        except Exception as e:
            print(f"❌ {tool} error: {e}")
    
    return working_tools

def main():
    """Main testing function for VPS"""
    print("🚀 VPS WARP Proxy Test")
    print("=" * 50)
    
    # Test 1: Basic proxy connection
    proxy_works = test_warp_proxy_on_vps()
    
    # Test 2: External tools
    working_tools = test_external_tools()
    
    # Test 3: MJSRecon integration (if proxy works)
    mjsrecon_works = False
    if proxy_works:
        mjsrecon_works = test_mjsrecon_with_proxy()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VPS TEST SUMMARY")
    print("=" * 50)
    
    if proxy_works:
        print("✅ WARP proxy is working on VPS")
    else:
        print("❌ WARP proxy is NOT working on VPS")
        
    if mjsrecon_works:
        print("✅ MJSRecon proxy integration is working")
    else:
        print("❌ MJSRecon proxy integration is NOT working")
    
    print(f"✅ External tools working: {', '.join(working_tools) if working_tools else 'None'}")
    
    print("\n💡 VPS RECOMMENDATIONS:")
    if not proxy_works:
        print("   - Install SOCKS support: pip install requests[socks] PySocks")
        print("   - Check WARP status: warp-cli status")
        print("   - Verify proxy mode: warp-cli settings")
    else:
        print("   - WARP proxy is working! You can use it with MJSRecon")
        print("   - Run: python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000")
        print("   - All external tools will automatically use the proxy via environment variables")

if __name__ == "__main__":
    main() 