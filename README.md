# MJSRecon - Modular JavaScript Reconnaissance Tool

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

A comprehensive, modular reconnaissance tool designed for JavaScript file discovery, analysis, and secret detection. MJSRecon provides a complete workflow from URL discovery to detailed analysis, with support for multiple code hosting platforms and advanced proxy configurations.

## 🚀 Features

### Core Modules
- **Discovery**: Multi-tool URL gathering (gau, waybackurls, katana)
- **Validation**: URL validation and live endpoint detection
- **Processing**: Deduplication and URL filtering
- **Download**: JavaScript file downloading and processing
- **Analysis**: JavaScript analysis and beautification
- **Fuzzing**: Parameter fuzzing with wordlists and permutations
- **Reporting**: Comprehensive report generation

### Code Hosting Scanners
- **GitHub**: Repository scanning with TruffleHog and GitLeaks
- **GitLab**: Project analysis and secret detection
- **Bitbucket**: Repository reconnaissance
- **Gitea**: Self-hosted repository scanning

### Advanced Features
- **Proxy Support**: HTTP/SOCKS5 proxy with authentication
- **Independent Mode**: Run single modules with custom input
- **Large Dataset Processing**: Handle massive URL datasets
- **Performance Monitoring**: Real-time resource usage tracking
- **Comprehensive Logging**: Timestamped logs with multiple levels
- **Modular Design**: Easy to extend and customize

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Modules](#-modules)
- [Code Hosting Scanners](#-code-hosting-scanners)
- [Configuration](#-configuration)
- [Proxy Support](#-proxy-support)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Git
- External tools (see below)

### 1. Clone the Repository

```bash
git clone https://github.com/mfarda/mjsrecon.git
cd mjsrecon
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install External Tools

#### Required Tools
```bash
# URL Discovery Tools
go install github.com/lc/gau/v2/cmd/gau@latest
go install github.com/tomnomnom/waybackurls@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest

# HTTP Client
go install github.com/projectdiscovery/httpx/cmd/httpx@latest

# URL Processing
go install github.com/tomnomnom/unfurl@latest

# URL Deduplication (optional, for --uro switch)
pip install uro

# Secret Detection
pip install trufflehog
# Download GitLeaks from: https://github.com/zricethezav/gitleaks/releases

# JavaScript Analysis
go install github.com/tagatac/jsluice/cmd/jsluice@latest

# Parameter Discovery
go install github.com/jaeles-project/fallparams@latest
```

#### Optional Tools
```bash
# Additional secret detection
go install github.com/michenriksen/gitrob@latest
go install github.com/repo-supervisor/repo-supervisor@latest
```

### 4. Verify Installation

```bash
python run_workflow.py --help
```

## 🚀 Quick Start

### Basic Workflow

```bash
# Run complete reconnaissance
python run_workflow.py discovery validation processing download analysis reporting -t example.com -o ./output
```

### Independent Mode

```bash
# Run single module with custom input
python run_workflow.py validation --independent --input ./urls.txt -t example.com -o ./output
```

## 📖 Usage

### Command Structure

```bash
python run_workflow.py [COMMANDS] [OPTIONS] -t TARGET -o OUTPUT_DIR
```

### Core Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `COMMANDS` | Modules to run | `discovery validation processing` |
| `-t, --target` | Target domain | `-t example.com` |
| `-o, --output` | Output directory | `-o ./results` |
| `--targets-file` | File with multiple targets | `--targets-file targets.txt` |
| `--uro` | Use uro to deduplicate/shorten URLs after discovery | `--uro` |
| `--independent` | Run single module | `--independent` |
| `--input` | Input file for independent mode | `--input urls.txt` |

### Logging Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable debug logging |
| `-q, --quiet` | Suppress console output |
| `--timestamp-format` | Custom timestamp format |

### Proxy Options

| Option | Description | Example |
|--------|-------------|---------|
| `--proxy` | Proxy URL | `--proxy socks5://127.0.0.1:1080` |
| `--proxy-auth` | Proxy authentication | `--proxy-auth user:pass` |
| `--no-proxy` | Bypass proxy for hosts | `--no-proxy localhost,127.0.0.1` |
| `--proxy-timeout` | Connection timeout | `--proxy-timeout 30` |
| `--proxy-verify-ssl` | Verify SSL certificates | `--proxy-verify-ssl` |

## 🔧 Modules

### 1. Discovery (`discovery`)

Gathers URLs from multiple sources using various tools.

**Options:**
- `--gather-mode`: Tools to use (`g=gau`, `w=wayback`, `k=katana`)
- `-d, --depth`: Katana crawl depth (default: 2)

**Example:**
```bash
python run_workflow.py discovery -t example.com --gather-mode gwk -d 3
```

### 2. Validation (`validation`)

Validates discovered URLs and identifies live endpoints.

**Features:**
- HTTP status code checking
- Redirect following
- Timeout configuration
- Proxy support

**Example:**
```bash
python run_workflow.py validation --independent --input ./all_urls.txt -t example.com
```

### 3. Processing (`processing`)

Deduplicates and filters URLs for optimal processing.

**Features:**
- URL deduplication
- Extension filtering
- Custom filtering rules

### 4. Download (`download`)

Downloads JavaScript files from validated URLs.

**Features:**
- Concurrent downloading
- File size limits
- Error handling
- Progress tracking

### 5. Analysis (`analysis`)

Analyzes downloaded JavaScript files for insights.

**Features:**
- JavaScript beautification
- Endpoint extraction
- Variable analysis
- Comment extraction

### 6. Fuzzing (`fuzzingjs`)

Performs parameter fuzzing on JavaScript endpoints.

**Options:**
- `--fuzz-mode`: Fuzzing strategy (`wordlist`, `permutation`, `both`, `off`)
- `--fuzz-wordlist`: Custom wordlist file

**Example:**
```bash
python run_workflow.py fuzzingjs --fuzz-mode both --fuzz-wordlist ./wordlist.txt -t example.com
```

### 7. Parameter Discovery

#### Passive (`param-passive`)
Discovers parameters from JavaScript files without active requests.

#### Active (`fallparams`)
Uses active parameter discovery techniques.

### 8. Reporting (`reporting`)

Generates comprehensive reports of findings.

**Output:**
- Text summary
- JSON data
- Statistics and metrics

## 🔍 Code Hosting Scanners

### GitHub Scanner (`github`)

Scans GitHub repositories for secrets and sensitive information.

**Setup:**
```bash
export GITHUB_TOKEN="your_github_token"
```

**Features:**
- Repository search and cloning
- Secret detection with TruffleHog and GitLeaks
- Organization scanning
- Custom pattern matching

### GitLab Scanner (`gitlab`)

Scans GitLab projects for sensitive data.

**Setup:**
```bash
export GITLAB_TOKEN="your_gitlab_token"
```

### Bitbucket Scanner (`bitbucket`)

Scans Bitbucket repositories.

**Setup:**
```bash
export BITBUCKET_USERNAME="your_username"
export BITBUCKET_TOKEN="your_app_password"
```

### Gitea Scanner (`gitea`)

Scans Gitea instances.

**Setup:**
```bash
export GITEA_TOKEN="your_gitea_token"
export GITEA_URL="https://your-gitea-instance.com"  # Optional
```

## ⚙️ Configuration

### Main Configuration (`common/config.py`)

```python
CONFIG = {
    'timeouts': {
        'http': 30,
        'download': 60,
        'tool_execution': 300,
    },
    'proxy': {
        'enabled': False,
        'url': None,
        'auth': None,
        'no_proxy': None,
        'timeout': 30,
        'verify_ssl': True,
    },
    'files': {
        'live_js': 'live_js_urls.txt',
        'all_urls': 'all_urls.txt',
        # ... more file definitions
    },
    # ... other settings
}
```

### Scanner Configuration

Each scanner has its own configuration section:

```python
'github_scanner': {
    'enabled_tools': {
        'trufflehog': True,
        'gitleaks': True,
        'custom_patterns': True,
    },
    'max_repos_to_scan': 10,
    'max_search_results': 1000,
    'rate_limit_wait': 60,
}
```

## 🌐 Proxy Support

### HTTP Proxy

```bash
python run_workflow.py discovery -t example.com --proxy http://proxy:8080
```

### SOCKS5 Proxy (WARP)

```bash
python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:1080
```

### Proxy with Authentication

```bash
python run_workflow.py discovery -t example.com \
    --proxy http://proxy:8080 \
    --proxy-auth username:password
```

### Bypass Proxy for Local Hosts

```bash
python run_workflow.py discovery -t example.com \
    --proxy socks5://127.0.0.1:1080 \
    --no-proxy localhost,127.0.0.1,10.0.0.0/8
```

## 📝 Examples

### Complete Reconnaissance Workflow

```bash
# Full workflow with all modules
python run_workflow.py discovery validation processing download analysis fuzzingjs param-passive fallparams reporting -t example.com -o ./results
```

# Full workflow with URL deduplication (uro)
python run_workflow.py discovery validation processing download analysis fuzzingjs param-passive fallparams reporting --uro -t example.com -o ./results
```

### URL Deduplication with uro

```bash
# Use uro to deduplicate URLs after discovery
python run_workflow.py discovery validation download analysis --uro -t example.com -o ./results

# Quick scan with uro for large datasets
python run_workflow.py discovery validation download --uro -t example.com -o ./results
```

### Code Hosting Reconnaissance

```bash
# Scan all code hosting platforms
python run_workflow.py github gitlab bitbucket gitea -t example.com -o ./results
```

### Large Dataset Processing

```bash
# Process large URL datasets
python process_large_dataset.py --input large_urls.txt --output processed_urls.txt --target-output-dir ./results
```

### Performance Monitoring

```bash
# Monitor resource usage during execution
python monitor_performance.py --pid $(pgrep -f "python.*run_workflow")
```

### Proxy Testing

```bash
# Test proxy connectivity
python test_proxy.py --proxy socks5://127.0.0.1:1080
```

### Independent Mode Examples

```bash
# Validate URLs from file
python run_workflow.py validation --independent --input ./urls.txt -t example.com -o ./results

# Process downloaded files
python run_workflow.py processing --independent --input ./live_urls.txt -t example.com -o ./results

# Analyze JavaScript files
python run_workflow.py analysis --independent --input ./js_files.txt -t example.com -o ./results
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Tool Not Found
```
Error: Required tool 'gau' is not installed or not in PATH.
```
**Solution:** Install the missing tool using the installation commands above.

#### 2. Permission Errors
```
Error: Permission denied when accessing repository
```
**Solution:** Check your API token permissions and ensure it has the required scopes.

#### 3. Rate Limiting
```
Rate limited by GitHub API. Waiting...
```
**Solution:** Wait for rate limit to reset or use a token with higher limits.

#### 4. Proxy Issues
```
Error: Connection failed through proxy
```
**Solution:** Verify proxy settings and test connectivity with `test_proxy.py`.

#### 5. File Not Found
```
Error: Input file not found: urls.txt
```
**Solution:** Check file path and ensure the file exists in the specified location.

### Debug Mode

Enable verbose logging for detailed information:

```bash
python run_workflow.py discovery -t example.com -v
```

### Performance Issues

For large datasets, use the processing script:

```bash
python process_large_dataset.py --input large_file.txt --chunk-size 1000
```

## 📊 Output Structure

```
output/
├── example.com/
│   ├── discovery/
│   │   ├── all_urls.txt
│   │   ├── uro_urls.txt
│   │   ├── gau_urls.txt
│   │   ├── wayback_urls.txt
│   │   └── katana_urls.txt
│   ├── validation/
│   │   └── live_urls.txt
│   ├── processing/
│   │   └── deduplicated_urls.txt
│   ├── download/
│   │   └── js_files/
│   ├── analysis/
│   │   └── analysis_results.json
│   ├── fuzzingjs/
│   │   └── fuzzing_results.txt
│   ├── github/
│   │   ├── repositories.json
│   │   ├── secrets.json
│   │   └── useful_data.json
│   └── reporting/
│       ├── summary_report.txt
│       └── detailed_report.json
├── logs/
│   └── mjsrecon.log
└── performance/
    └── resource_usage.json
```

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Add docstrings to functions
- Include error handling

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=mjsrecon
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [gau](https://github.com/lc/gau) - URL discovery
- [waybackurls](https://github.com/tomnomnom/waybackurls) - Wayback machine URLs
- [katana](https://github.com/projectdiscovery/katana) - Web crawling
- [TruffleHog](https://github.com/trufflesecurity/trufflehog) - Secret detection
- [GitLeaks](https://github.com/zricethezav/gitleaks) - Comprehensive leak detection

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/mfarda/mjsrecon/issues)
- **Discussions:** [GitHub Discussions](https://github.com/mfarda/mjsrecon/discussions)
- **Documentation:** [Wiki](https://github.com/mfarda/mjsrecon/wiki)

---

**⚠️ Disclaimer:** This tool is for educational and authorized security testing purposes only. Always ensure you have proper authorization before scanning any target. 