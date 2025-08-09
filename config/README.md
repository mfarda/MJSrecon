# MJSRecon Configuration

This directory contains all configuration files for MJSRecon. The configuration system is designed to be flexible, secure, and environment-aware.

## 📁 Configuration Files

### Core Configuration
- **`defaults.yaml`** - Default configuration values for all modules
- **`environments.yaml`** - Environment-specific overrides (development, production, testing)

### Scanner Configurations
- **`github_scanner.yaml`** - GitHub-specific configuration
- **`gitlab_scanner.yaml`** - GitLab-specific configuration  
- **`bitbucket_scanner.yaml`** - Bitbucket-specific configuration
- **`gitea_scanner.yaml`** - Gitea-specific configuration

### Security and Patterns
- **`patterns.yaml`** - Secret detection patterns and regex rules
- **`secrets.yaml.example`** - Example secrets file (copy to `secrets.yaml`)

## 🔧 Configuration Loading

The configuration system loads files in the following order:

1. **`defaults.yaml`** - Base configuration
2. **`environments.yaml`** - Environment-specific overrides
3. **Scanner-specific files** - Individual scanner configurations
4. **`patterns.yaml`** - Secret detection patterns
5. **`secrets.yaml`** - Sensitive configuration (if exists)

## 🌍 Environment Support

### Development
- Reduced resource usage
- Faster execution
- Limited repository scanning
- Shorter timeouts

### Production
- Full resource utilization
- Comprehensive scanning
- Extended timeouts
- Caching enabled

### Testing
- Minimal resource usage
- Single repository scanning
- Very short timeouts
- Quick execution

## 🔐 Secrets Management

### Using Environment Variables (Recommended)
```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITLAB_TOKEN="glpat_your_token_here"
export BITBUCKET_TOKEN="your_bitbucket_token"
export GITEA_TOKEN="your_gitea_token"
```

### Using secrets.yaml
1. Copy `secrets.yaml.example` to `secrets.yaml`
2. Fill in your actual values
3. **DO NOT commit `secrets.yaml` to version control**

```yaml
api_tokens:
  github: "ghp_your_actual_token_here"
  gitlab: "glpat_your_actual_token_here"
  bitbucket: "your_actual_token_here"
  gitea: "your_actual_token_here"
```

## 🛠️ Usage in Code

```python
from src.common.config_loader import load_config, get_scanner_config

# Load full configuration
config = load_config(environment="production")

# Get specific scanner configuration
github_config = get_scanner_config("github")

# Access specific values
max_repos = github_config.get("max_repos_to_scan", 4)
```

## 📝 Configuration Structure

### Global Settings
```yaml
tools:
  required: ["waybackurls", "gau", "katana", "httpx"]
  full_mode: ["jsluice", "trufflehog"]

proxy:
  enabled: false
  url: null
  timeout: 30
```

### Module Settings
```yaml
discovery:
  gather_mode: "gwk"  # g=gau, w=wayback, k=katana
  depth: 2
  use_uro: false

processing:
  max_file_size_mb: 10
  max_concurrent_downloads: 10
```

### Scanner Settings
```yaml
github_scanner:
  api_token_env: "GITHUB_TOKEN"
  max_repos_to_scan: 4
  search_queries:
    - '"{target}"'
    - 'org:{target}'
```

## 🔄 Configuration Updates

### Adding New Settings
1. Add the setting to `defaults.yaml`
2. Override in `environments.yaml` if needed
3. Update the code to use the new setting

### Environment-Specific Changes
1. Edit the appropriate section in `environments.yaml`
2. The changes will be automatically merged with defaults

### Scanner-Specific Changes
1. Edit the appropriate scanner file (e.g., `github_scanner.yaml`)
2. Changes apply to all environments unless overridden

## 🚨 Security Best Practices

1. **Never commit secrets to version control**
2. **Use environment variables for sensitive data**
3. **Keep `secrets.yaml` in `.gitignore`**
4. **Use different tokens for different environments**
5. **Regularly rotate API tokens**

## 📊 Configuration Validation

The configuration loader includes validation:
- File existence checks
- YAML syntax validation
- Environment variable resolution
- Path normalization

## 🔍 Troubleshooting

### Common Issues
1. **Configuration file not found** - Check file paths and permissions
2. **YAML syntax errors** - Validate YAML syntax
3. **Environment variables not resolved** - Check variable names and values
4. **Tool paths not found** - Verify tool installations

### Debug Mode
Enable debug logging to see configuration loading details:
```python
from src.common.logger import Logger
logger = Logger(verbose=True)
```

## 📚 Examples

See the `examples/` directory for configuration examples and use cases. 