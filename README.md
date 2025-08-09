# MJSRecon - Modular JavaScript Reconnaissance Tool

A comprehensive, modular JavaScript reconnaissance tool designed for security researchers and bug bounty hunters. MJSRecon provides a complete pipeline for discovering, analyzing, and testing JavaScript files and endpoints.

## 🚀 Features

### Core Capabilities
- **URL Discovery**: Multi-source JavaScript URL discovery using gau, waybackurls, and katana
- **URL Validation**: Verify discovered URLs are live and accessible
- **Content Deduplication**: Remove duplicate content using hash-based deduplication
- **Asynchronous Downloads**: Fast, concurrent JavaScript file downloads
- **Secret Analysis**: Advanced secret detection using multiple tools and patterns
- **Directory Fuzzing**: Discover additional JavaScript files through fuzzing
- **Parameter Extraction**: Passive and active parameter discovery
- **SQL Injection Testing**: Comprehensive SQL injection reconnaissance
- **Code Hosting Scanners**: GitHub, GitLab, Bitbucket, and Gitea scanning
- **Report Generation**: Comprehensive reporting and analysis

### Advanced Features
- **Environment Configuration**: Development, production, and testing profiles
- **Proxy Support**: SOCKS5 and HTTP proxy support with authentication
- **Timeout Management**: Configurable timeouts with partial output preservation
- **Independent Mode**: Run individual modules with custom input
- **URL Deduplication**: uro integration for URL shortening and deduplication
- **Progress Tracking**: Real-time progress bars and logging
- **Modular Architecture**: Easy to extend and customize

## 📦 Installation

### Prerequisites
- Python 3.8+
- External tools (see [External Tools](#external-tools) section)

### Quick Install
```bash
# Clone the repository
git clone https://github.com/your-username/mjsrecon.git
cd mjsrecon

# Install Python dependencies
pip install -r requirements.txt

# Install external tools (see External Tools section)
```

### External Tools
MJSRecon requires several external tools for full functionality:

#### Discovery Tools
```bash
# gau - URL discovery
go install github.com/lc/gau/v2/cmd/gau@latest

# waybackurls - Wayback Machine URL extraction
go install github.com/tomnomnom/waybackurls@latest

# katana - Web crawling
go install github.com/projectdiscovery/katana/cmd/katana@latest

# uro - URL deduplication
pip install uro
```

#### Analysis Tools
```bash
# linkfinder - JavaScript endpoint extraction
git clone https://github.com/GerbenJavado/LinkFinder.git
cd LinkFinder
pip install -r requirements.txt
python setup.py install

# secretfinder - Secret detection
# (included in src/tools/)

# trufflehog - Advanced secret scanning
pip install trufflehog

# gitleaks - Git repository scanning
# Download from: https://github.com/zricethezav/gitleaks/releases
```

#### Testing Tools
```bash
# sqlmap - SQL injection testing
git clone https://github.com/sqlmapproject/sqlmap.git

# ghauri - Alternative SQL injection scanner
pip install ghauri
```

## 🛠️ Configuration

### Environment Configuration
MJSRecon uses environment-specific configuration files:

- `config/defaults.yaml` - Base configuration
- `config/environments.yaml` - Environment-specific overrides
- `config/*_scanner.yaml` - Scanner-specific configurations

### Environment Profiles
- **Development**: Fast scans, minimal timeouts, debug logging
- **Production**: Optimized for real-world scanning, extended timeouts
- **Testing**: Minimal resource usage, quick validation

### Setting Up API Tokens
Create `config/secrets.yaml` from `config/secrets.yaml.example`:

```yaml
# GitHub Scanner
github_token: "your_github_token_here"

# GitLab Scanner  
gitlab_token: "your_gitlab_token_here"

# Bitbucket Scanner
bitbucket_token: "your_bitbucket_token_here"

# Gitea Scanner
gitea_token: "your_gitea_token_here"
```

## 📖 Usage

### Basic Usage
```bash
# Simple discovery scan
python run_workflow.py discovery -t example.com

# Full reconnaissance workflow
python run_workflow.py discovery validation processing download analysis -t example.com

# With custom output directory
python run_workflow.py discovery validation -t example.com -o ./results
```

### Advanced Usage
```bash
# Using proxy for stealth
python run_workflow.py discovery validation -t example.com --proxy socks5://127.0.0.1:40000 --env production

# Large target with extended timeout
python run_workflow.py discovery -t large-target.com --command-timeout 7200 --env production

# Multiple targets from file
python run_workflow.py discovery validation processing --targets-file targets.txt

# Independent mode - single module
python run_workflow.py discovery --independent --input discovered_urls.txt

# Custom discovery tools
python run_workflow.py discovery -t example.com --gather-mode gk --depth 3

# URL deduplication with uro
python run_workflow.py discovery validation processing -t example.com --uro
```

### Workflow Commands
| Command | Description |
|---------|-------------|
| `discovery` | Discovers JavaScript URLs from various sources |
| `validation` | Validates discovered URLs are live |
| `processing` | Deduplicates URLs based on content hash |
| `download` | Downloads JavaScript files asynchronously |
| `analysis` | Analyzes files for secrets and endpoints |
| `fuzzingjs` | Performs directory and file fuzzing |
| `param-passive` | Extracts parameters from URLs |
| `fallparams` | Dynamic parameter discovery |
| `sqli` | SQL injection reconnaissance |
| `github` | GitHub secrets and repository scanning |
| `gitlab` | GitLab secrets and repository scanning |
| `bitbucket` | Bitbucket secrets and repository scanning |
| `gitea` | Gitea secrets and repository scanning |
| `reporting` | Generates comprehensive reports |

### Key Options
| Option | Description |
|--------|-------------|
| `-t, --target` | Target domain or URL |
| `--targets-file` | File with multiple targets |
| `-o, --output` | Output directory |
| `--env` | Configuration environment |
| `--proxy` | Proxy URL (SOCKS5/HTTP) |
| `--command-timeout` | Override command timeout |
| `--independent` | Run single module mode |
| `--input` | Input file for independent mode |
| `--uro` | Use uro for URL deduplication |
| `--gather-mode` | Discovery tools selection |
| `-v, --verbose` | Verbose logging |

## 🔧 Configuration Files

### Default Configuration (`config/defaults.yaml`)
Contains base settings for all modules, timeouts, and tool configurations.

### Environment Overrides (`config/environments.yaml`)
Environment-specific settings for development, production, and testing.

### Scanner Configurations
- `config/github_scanner.yaml` - GitHub scanner settings
- `config/gitlab_scanner.yaml` - GitLab scanner settings
- `config/bitbucket_scanner.yaml` - Bitbucket scanner settings
- `config/gitea_scanner.yaml` - Gitea scanner settings

### Patterns (`config/patterns.yaml`)
Regex patterns for secret detection and analysis.

## 📁 Output Structure
```
output/
├── example.com/
│   ├── discovery/
│   │   ├── discovered_urls.txt
│   │   └── logs/
│   ├── validation/
│   │   ├── validated_urls.txt
│   │   └── logs/
│   ├── processing/
│   │   ├── unique_urls.txt
│   │   └── logs/
│   ├── download/
│   │   ├── downloaded_js_files/
│   │   └── logs/
│   ├── analysis/
│   │   ├── analysis_results.json
│   │   └── logs/
│   └── reports/
│       ├── summary.html
│       └── detailed_report.json
```

## 🔍 Proxy Support

MJSRecon supports various proxy configurations:

### SOCKS5 Proxy (WARP)
```bash
python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000
```

### HTTP Proxy
```bash
python run_workflow.py discovery -t example.com --proxy http://proxy:8080
```

### Proxy with Authentication
```bash
python run_workflow.py discovery -t example.com --proxy http://user:pass@proxy:8080
```

### Proxy Bypass
```bash
python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000 --no-proxy localhost,127.0.0.1
```

## 🚨 Performance Optimization

### Large Targets
For large targets that may timeout:
```bash
python run_workflow.py discovery -t large-target.com --command-timeout 7200 --env production
```

### Concurrent Processing
Adjust concurrency settings in `config/environments.yaml`:
```yaml
production:
  download:
    concurrent_downloads: 50
  validation:
    max_workers: 20
```

### Memory Management
Use testing environment for memory-constrained systems:
```bash
python run_workflow.py discovery -t example.com --env testing
```

## 🐛 Troubleshooting

### Common Issues

#### Command Timeouts
- Increase timeout: `--command-timeout 7200`
- Use production environment: `--env production`
- Check network connectivity

#### Proxy Issues
- Verify proxy is running: `curl --socks5 127.0.0.1:40000 http://ipinfo.io`
- Install SOCKS support: `pip install requests[socks] PySocks`
- Check proxy authentication

#### Missing Tools
- Run tool check: `python run_workflow.py --help`
- Install missing tools (see External Tools section)
- Verify PATH environment variable

#### Permission Issues
- Check file permissions
- Run with appropriate user privileges
- Verify output directory is writable

### Debug Mode
Enable verbose logging for troubleshooting:
```bash
python run_workflow.py discovery -t example.com -v --timestamp-format "%Y-%m-%d %H:%M:%S"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Check code style
flake8 src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and authorized security testing purposes only. Users are responsible for ensuring they have proper authorization before scanning any targets. The authors are not responsible for any misuse of this tool.

## 🙏 Acknowledgments

- [gau](https://github.com/lc/gau) - URL discovery
- [waybackurls](https://github.com/tomnomnom/waybackurls) - Wayback Machine integration
- [katana](https://github.com/projectdiscovery/katana) - Web crawling
- [uro](https://github.com/s0md3v/uro) - URL deduplication
- [linkfinder](https://github.com/GerbenJavado/LinkFinder) - JavaScript analysis
- [trufflehog](https://github.com/trufflesecurity/trufflehog) - Secret scanning
- [sqlmap](https://github.com/sqlmapproject/sqlmap) - SQL injection testing 