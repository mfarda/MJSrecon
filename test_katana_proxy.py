#!/usr/bin/env python3
"""
Test script specifically for testing katana with proxy
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_katana_proxy():
    """Test katana with proxy to debug hanging issue"""
    print("🔍 Testing Katana with Proxy")
    print("=" * 50)
    
    # Test 1: Test katana without proxy (should work)
    print("\n1️⃣ Testing katana without proxy...")
    try:
        cmd = [
            'python', 'run_workflow.py', 
            'discovery', 
            '-t', 'example.com', 
            '--gather-mode', 'k',
            '-o', './test_output_katana_no_proxy'
        ]
        
        print(f"   Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Katana without proxy works!")
        else:
            print(f"❌ Katana without proxy failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Katana without proxy timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Test katana with proxy (may hang)
    print("\n2️⃣ Testing katana with proxy...")
    try:
        cmd = [
            'python', 'run_workflow.py', 
            'discovery', 
            '-t', 'example.com', 
            '--gather-mode', 'k',
            '--proxy', 'socks5://127.0.0.1:40000',
            '-o', './test_output_katana_with_proxy'
        ]
        
        print(f"   Running: {' '.join(cmd)}")
        print("   ⚠️  This may hang if proxy is not working properly")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Katana with proxy works!")
            if "Command: katana" in result.stdout:
                print("✅ Command logging is working!")
        else:
            print(f"❌ Katana with proxy failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Katana with proxy timed out (likely hanging)")
        print("   This indicates the proxy connection is not working properly")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Test katana command directly
    print("\n3️⃣ Testing katana command directly...")
    try:
        # Test katana help to see available options
        result = subprocess.run(['katana', '--help'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Katana help works")
            if '-proxy' in result.stdout:
                print("✅ Katana supports -proxy parameter")
            else:
                print("❌ Katana does NOT support -proxy parameter")
        else:
            print("❌ Katana help failed")
    except FileNotFoundError:
        print("❌ Katana not found")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Test katana with proxy directly
    print("\n4️⃣ Testing katana with proxy directly...")
    try:
        cmd = ['katana', '-u', 'https://example.com', '-jc', '-d', '1', '-proxy', 'socks5://127.0.0.1:40000']
        print(f"   Running: {' '.join(cmd)}")
        print("   ⚠️  This may hang if proxy is not working")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Direct katana with proxy works!")
            print(f"   Found {len(result.stdout.splitlines())} URLs")
        else:
            print(f"❌ Direct katana with proxy failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("❌ Direct katana with proxy timed out (hanging)")
        print("   The issue is with katana + proxy combination")
    except FileNotFoundError:
        print("❌ Katana not found")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Check proxy connectivity
    print("\n5️⃣ Checking proxy connectivity...")
    try:
        # Test if proxy port is listening
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 40000))
        sock.close()
        
        if result == 0:
            print("✅ Proxy port 40000 is listening")
        else:
            print("❌ Proxy port 40000 is NOT listening")
            print("   Make sure WARP proxy is running")
    except Exception as e:
        print(f"❌ Error checking proxy: {e}")
    
    print("\n" + "=" * 50)
    print("📊 KATANA PROXY TEST SUMMARY")
    print("=" * 50)
    print("✅ Command logging added to discovery module")
    print("✅ Silent mode removed for katana with proxy")
    print("✅ You can now see the exact katana command being executed")
    print("\n💡 TROUBLESHOOTING:")
    print("   - If katana hangs, check if WARP proxy is running")
    print("   - Try running katana directly with proxy to isolate the issue")
    print("   - Check if katana supports the -proxy parameter")

if __name__ == "__main__":
    test_katana_proxy() 