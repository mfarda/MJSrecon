# VPS WARP Proxy Setup and Testing Guide

## 🚀 Quick Setup for VPS

### Step 1: Install SOCKS Support
```bash
# In your virtual environment
pip install requests[socks] PySocks
```

### Step 2: Test WARP Proxy
```bash
# Run the VPS-specific test
python vps_proxy_test.py
```

### Step 3: Test MJSRecon with Proxy
```bash
# Test discovery with proxy
python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000 -o ./test_output
```

## 📊 Your Current VPS Status

Based on your test results:
- ✅ **WARP is running** and connected
- ✅ **Proxy port 40000 is listening**
- ✅ **External tools (curl, wget) work with proxy**
- ❌ **Python SOCKS support missing** (needs `pip install requests[socks] PySocks`)
- ❌ **MJSRecon proxy integration not tested yet**

## 🔧 Complete VPS Setup

### 1. Install Missing Dependencies
```bash
# In your virtual environment
pip install requests[socks] PySocks

# Verify installation
python -c "import requests; import socks; print('SOCKS support installed!')"
```

### 2. Test Proxy After Installation
```bash
# Run the comprehensive test again
python proxy_test_comprehensive.py
```

### 3. Test MJSRecon Integration
```bash
# Test discovery module with proxy
python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000 -o ./test_output

# Test full workflow with proxy
python run_workflow.py discovery validation processing download analysis --proxy socks5://127.0.0.1:40000 -t example.com -o ./test_output
```

## 🌐 How Proxy Works in MJSRecon

### Modules That Use Proxy:
1. **Discovery Module** ✅ - External tools inherit proxy via environment variables
2. **Validation Module** ✅ - Uses configured requests.Session with proxy
3. **Processing Module** ❌ - Missing proxy support (needs fix)
4. **Download Module** ❌ - Missing proxy support (needs fix)
5. **External Tools** ✅ - All inherit proxy via HTTP_PROXY/HTTPS_PROXY environment variables

### Environment Variables Set:
When you use `--proxy socks5://127.0.0.1:40000`, MJSRecon sets:
- `HTTP_PROXY=socks5://127.0.0.1:40000`
- `HTTPS_PROXY=socks5://127.0.0.1:40000`

## 🧪 Testing Commands

### Test 1: Basic Proxy Functionality
```bash
python vps_proxy_test.py
```

### Test 2: MJSRecon Discovery with Proxy
```bash
python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000 -o ./test_output
```

### Test 3: Full Workflow with Proxy
```bash
python run_workflow.py discovery validation processing download analysis --proxy socks5://127.0.0.1:40000 -t example.com -o ./test_output
```

### Test 4: External Tools with Proxy
```bash
# Set environment variables
export HTTP_PROXY=socks5://127.0.0.1:40000
export HTTPS_PROXY=socks5://127.0.0.1:40000

# Test individual tools
curl -s https://httpbin.org/ip
wget -qO- https://httpbin.org/ip
gau --help
waybackurls --help
```

## 🔍 Troubleshooting

### If Proxy Still Doesn't Work:

1. **Check WARP Status:**
   ```bash
   warp-cli status
   warp-cli settings
   ```

2. **Restart WARP:**
   ```bash
   warp-cli disconnect
   warp-cli connect
   ```

3. **Verify Proxy Mode:**
   ```bash
   warp-cli set-mode proxy
   ```

4. **Check Port:**
   ```bash
   netstat -tlnp | grep 40000
   ```

5. **Test with curl:**
   ```bash
   curl --socks5 127.0.0.1:40000 https://httpbin.org/ip
   ```

## 📝 Expected Results

After proper setup, you should see:
- ✅ Port 40000 listening
- ✅ HTTP requests through proxy successful
- ✅ External tools working with proxy
- ✅ MJSRecon discovery working with proxy
- ✅ Different IP address when using proxy vs direct connection

## 🎯 Next Steps

1. Install SOCKS support: `pip install requests[socks] PySocks`
2. Run VPS test: `python vps_proxy_test.py`
3. Test MJSRecon: `python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000`
4. Use in production workflows with `--proxy socks5://127.0.0.1:40000` flag 