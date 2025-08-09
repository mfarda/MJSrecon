# MJSRecon Configuration Guide

This guide explains how to configure and customize MJSRecon for your specific needs.

## 📁 Configuration Structure

MJSRecon uses a hierarchical configuration system:

```
config/
├── defaults.yaml           # Base configuration for all modules
├── environments.yaml       # Environment-specific overrides
├── patterns.yaml          # Regex patterns for secret detection
├── secrets.yaml.example   # Template for API tokens and secrets
├── github_scanner.yaml    # GitHub scanner specific settings
├── gitlab_scanner.yaml    # GitLab scanner specific settings
├── bitbucket_scanner.yaml # Bitbucket scanner specific settings
└── gitea_scanner.yaml     # Gitea scanner specific settings
```

## 🔧 Default Configuration (`config/defaults.yaml`)

The `defaults.yaml` file contains all base configuration values. Here's a breakdown of each section:

### Global Tools Configuration
```yaml
tools:
  required:
    - "waybackurls"
    - "gau"
    - "katana"
    - "httpx"
    - "unfurl"
    - "fallparams"
    - "gf"
  full_mode:
    - "jsluice"
    - "trufflehog"
  python_tools:
    secretfinder: "src/tools/secretfinder.py"
    linkfinder: "src/tools/linkfinder.py"
```

### Proxy Configuration
```yaml
proxy:
  enabled: false
  url: null
  auth: null
  no_proxy: null
  timeout: 30
  verify_ssl: false
```

### File and Directory Configuration
```yaml
files:
  live_js: "live_js_urls.txt"
  deduplicated_js: "deduplicated_js_urls.txt"
  all_urls: "all_urls.txt"
  uro_urls: "uro_urls.txt"
  fuzzing_all: "fuzzing_all_urls.txt"
  fuzzing_new: "fuzzing_new_urls.txt"
  permutation_wordlist: "fuzz_permutations.txt"
  sqli_targets: "sqli_targets.txt"

dirs:
  downloaded_files: "downloaded_files"
  results: "results"
  ffuf_results: "ffuf_results"
  sqli_results: "sqli_results"
  param_passive: "param_passive"
  fallparams_results: "fallparams_results"
```

### Timeout Configuration
```yaml
timeouts:
  command: 300
  download: 60
  analysis: 300
  verify: 30
```

## 📥 Download Module Configuration

The download module now supports multiple file extensions and is fully configurable:

```yaml
download:
  max_file_size_mb: 10
  timeout: 30
  max_concurrent: 10
  allowed_extensions:
    - ".js"
    - ".jsx"
    - ".ts"
    - ".tsx"
    - ".vue"
    - ".json"
```

### Adding New File Extensions

To add support for additional file types:

```yaml
download:
  allowed_extensions:
    - ".js"
    - ".jsx"
    - ".ts"
    - ".tsx"
    - ".vue"
    - ".json"
    - ".map"    # Source maps
    - ".mjs"    # ES modules
    - ".cjs"    # CommonJS modules
    - ".coffee" # CoffeeScript
```

## 🔍 Fuzzing Module Configuration

The fuzzing module uses configurable patterns to generate wordlists:

```yaml
enumeration:
  fuzz_threads: 10
  fuzz_timeout: 30
  # Fuzzing wordlist generation settings
  prefixes:
    - "app"
    - "lib"
    - "vendor"
    - "dist"
    - "src"
    - "core"
    - "main"
  suffixes:
    - "bundle"
    - "min"
    - "dev"
    - "prod"
    - "v1"
    - "v2"
  separators:
    - ""
    - "-"
    - "_"
    - "."
```

### Customizing Fuzzing Patterns

Add your own prefixes, suffixes, or separators:

```yaml
enumeration:
  prefixes:
    - "app"
    - "lib"
    - "vendor"
    - "dist"
    - "src"
    - "core"
    - "main"
    - "myapp"      # Custom prefix
    - "company"    # Company-specific prefix
  suffixes:
    - "bundle"
    - "min"
    - "dev"
    - "prod"
    - "v1"
    - "v2"
    - "latest"     # Custom suffix
    - "stable"     # Custom suffix
  separators:
    - ""
    - "-"
    - "_"
    - "."
    - "~"          # Custom separator
```

## 🛡️ SQL Injection Module Configuration

The SQLi module uses configurable patterns for vulnerability detection:

```yaml
sqli:
  scanner: "sqlmap"  # sqlmap, ghauri
  full_scan: false
  manual_blind: true
  header_test: false
  xor_test: false
  timeout: 300
  delay_threshold: 3
  sqlmap_args: "--batch --random-agent --level=2 --risk=1"
  ghauri_args: "--batch --random-agent"
  
  # Vulnerable file extensions
  vulnerable_extensions:
    - ".php"
    - ".asp"
    - ".aspx"
    - ".jsp"
    - ".jspx"
    - ".do"
    - ".action"
  
  # Common vulnerable file patterns
  vulnerable_files:
    - "product.php"
    - "view.php"
    - "show.php"
    - "display.php"
    - "detail.php"
    # ... 40+ file patterns
  
  # SQL injection indicators in URLs
  sql_indicators:
    - "select"
    - "union"
    - "insert"
    - "update"
    - "delete"
    - "drop"
    - "create"
    - "alter"
    - "exec"
    - "execute"
    - "script"
    - "javascript"
    - "vbscript"
```

### Adding Custom SQL Injection Patterns

```yaml
sqli:
  vulnerable_extensions:
    - ".php"
    - ".asp"
    - ".aspx"
    - ".jsp"
    - ".jspx"
    - ".do"
    - ".action"
    - ".custom"    # Add your custom extension
    - ".internal"  # Internal application extension
  
  vulnerable_files:
    - "product.php"
    - "view.php"
    # ... existing patterns
    - "custom.php"     # Add your custom file pattern
    - "internal.php"   # Internal application file
  
  sql_indicators:
    - "select"
    - "union"
    - "insert"
    # ... existing indicators
    - "custom_query"   # Add your custom indicator
    - "internal_sql"   # Internal application indicator
```

## 🌍 Environment Configuration (`config/environments.yaml`)

Environment-specific overrides allow you to optimize settings for different use cases:

```yaml
development:
  proxy:
    enabled: false
  discovery:
    depth: 1
  validation:
    max_workers: 5
  download:
    max_concurrent: 5
  analysis:
    max_workers: 2

production:
  proxy:
    enabled: true
  discovery:
    depth: 3
  validation:
    max_workers: 20
  download:
    max_concurrent: 50
  analysis:
    max_workers: 8
  timeouts:
    command: 3600

testing:
  proxy:
    enabled: false
  discovery:
    depth: 1
  validation:
    max_workers: 2
  download:
    max_concurrent: 2
  analysis:
    max_workers: 1
  timeouts:
    command: 300
```

## 🔐 Secrets Configuration

Create `config/secrets.yaml` from the example:

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

## 🎯 Module-Specific Configuration

### Discovery Module
```yaml
discovery:
  gather_mode: "gwk"  # g=gau, w=wayback, k=katana
  depth: 2
  use_uro: false
```

### Validation Module
```yaml
validation:
  max_workers: 10
  timeout: 30
  verify_ssl: false
```

### Processing Module
```yaml
processing:
  max_file_size_mb: 10
  download_timeout: 30
  max_concurrent_downloads: 10
```

### Analysis Module
```yaml
analysis:
  max_workers: 4
  max_file_size_mb: 10
```

### Parameter Extraction
```yaml
param_passive:
  important_extensions:
    - ".js"
    - ".json"
    - ".map"
```

### Parameter Enumeration
```yaml
fallparams:
  threads: 10
```

### Reporting
```yaml
reporting:
  generate_html: true
  generate_json: true
  generate_markdown: true
  include_timestamps: true
```

## 🚀 CLI Overrides

You can override configuration values via command line:

```bash
# Override command timeout
python run_workflow.py discovery -t example.com --command-timeout 7200

# Use specific environment
python run_workflow.py discovery -t example.com --env production

# Override proxy settings
python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000
```

## 🔄 Configuration Loading Order

Configuration is loaded in this order (later values override earlier ones):

1. `config/defaults.yaml` - Base configuration
2. `config/environments.yaml` - Environment-specific overrides
3. `config/*_scanner.yaml` - Scanner-specific configurations
4. `config/patterns.yaml` - Regex patterns
5. `config/secrets.yaml` - API tokens and secrets
6. CLI arguments - Command line overrides

## 🛠️ Customization Examples

### Example 1: Add Source Map Support
```yaml
# In config/defaults.yaml
download:
  allowed_extensions:
    - ".js"
    - ".jsx"
    - ".ts"
    - ".tsx"
    - ".vue"
    - ".json"
    - ".map"    # Add source map support
```

### Example 2: Custom Fuzzing for React Apps
```yaml
# In config/defaults.yaml
enumeration:
  prefixes:
    - "app"
    - "lib"
    - "vendor"
    - "dist"
    - "src"
    - "core"
    - "main"
    - "react"     # React-specific
    - "component" # Component-specific
  suffixes:
    - "bundle"
    - "min"
    - "dev"
    - "prod"
    - "v1"
    - "v2"
    - "chunk"     # Webpack chunks
    - "vendor"    # Vendor bundles
```

### Example 3: Custom SQL Injection for Internal Apps
```yaml
# In config/defaults.yaml
sqli:
  vulnerable_extensions:
    - ".php"
    - ".asp"
    - ".aspx"
    - ".jsp"
    - ".jspx"
    - ".do"
    - ".action"
    - ".internal"  # Internal application extension
    - ".api"       # API endpoints
  
  vulnerable_files:
    - "product.php"
    - "view.php"
    # ... existing patterns
    - "internal.php"   # Internal application files
    - "api.php"        # API files
```

## 🔍 Troubleshooting Configuration

### Common Issues

1. **Missing Configuration Keys**
   - Ensure all required keys are present in `config/defaults.yaml`
   - Check that environment overrides don't remove required keys

2. **Configuration Syntax Errors**
   - Validate YAML syntax using online YAML validators
   - Check for proper indentation and quotes

3. **Environment-Specific Issues**
   - Verify environment name matches `config/environments.yaml`
   - Check that environment overrides are properly formatted

4. **File Path Issues**
   - Ensure all file paths in configuration are correct
   - Check that Python tool paths point to valid files

### Debugging Configuration

Enable verbose logging to see configuration loading:

```bash
python run_workflow.py discovery -t example.com -v
```

This will show which configuration files are loaded and any errors during the process.

## 📝 Best Practices

1. **Keep Defaults Minimal**: Use `defaults.yaml` for essential settings only
2. **Use Environment Overrides**: Put environment-specific settings in `environments.yaml`
3. **Document Customizations**: Add comments to explain custom configuration choices
4. **Version Control**: Keep `secrets.yaml` out of version control
5. **Test Configurations**: Test custom configurations in development environment first
6. **Backup Configurations**: Keep backups of working configurations

## 🔄 Migration from Old Configuration

If you're upgrading from an older version:

1. **Backup Current Config**: Save your current configuration files
2. **Review New Defaults**: Check `config/defaults.yaml` for new settings
3. **Update Custom Settings**: Move custom settings to appropriate configuration files
4. **Test Configuration**: Run a test scan to verify everything works
5. **Update Documentation**: Update any custom documentation with new configuration structure
