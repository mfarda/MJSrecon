# GitHub Scanner Configuration Guide

This guide explains how to configure the GitHub scanner for API keys and tool mode selection in MJSRecon.

## 🔑 API Key Configuration

### 1. GitHub API Token Setup

The GitHub scanner requires a GitHub API token for enhanced rate limits and access to private repositories.

#### Option A: Environment Variable (Recommended)
```bash
# Set the environment variable
export GITHUB_TOKEN="your_github_token_here"

# Or add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
echo 'export GITHUB_TOKEN="your_github_token_here"' >> ~/.bashrc
source ~/.bashrc
```

#### Option B: Custom Environment Variable Name
You can change the environment variable name in the configuration:

```python
# In common/config.py, modify the api_token_env setting:
'github_scanner': {
    'api_token_env': 'MY_GITHUB_TOKEN',  # Custom environment variable name
    # ... other settings
}
```

Then set your token:
```bash
export MY_GITHUB_TOKEN="your_github_token_here"
```

### 2. Creating a GitHub API Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes:
   - `public_repo` (for public repositories)
   - `repo` (for private repositories if needed)
   - `read:org` (for organization access)
   - `read:user` (for user information)
4. Copy the generated token

## 🛠️ Tool Mode Selection

### 1. Available Tools

The GitHub scanner supports multiple secret detection tools:

| Tool | Description | Default |
|------|-------------|---------|
| `trufflehog` | Advanced secret scanning with entropy analysis | ✅ Enabled |
| `trufflehog_github_org` | Direct GitHub organization scanning | ✅ Enabled |
| `gitleaks` | Comprehensive leak detection | ✅ Enabled |
| `custom_patterns` | Custom regex pattern matching | ✅ Enabled |
| `gitrob` | Repository analysis tool | ❌ Disabled |
| `repo-supervisor` | Repository monitoring tool | ❌ Disabled |
| `git-secrets` | Git hooks for secret prevention | ❌ Disabled |

### 2. Configuring Tool Selection

Edit `common/config.py` to enable/disable tools:

```python
'github_scanner': {
    'enabled_tools': {
        'trufflehog': True,      # Enable TruffleHog
        'trufflehog_github_org': True,  # Enable TruffleHog GitHub org scanning
        'gitleaks': True,         # Enable GitLeaks
        'custom_patterns': True,  # Enable custom patterns
        'gitrob': False,          # Disable GitRob
        'repo-supervisor': False, # Disable Repo-Supervisor
        'git-secrets': False      # Disable Git-Secrets
    },
    # ... other settings
}
```

### 3. GitHub Organization Scanning

The scanner now includes direct GitHub organization scanning using TruffleHog's `github --org` command. This feature:

- **Scans repositories directly from GitHub API** without cloning
- **Uses your GitHub token** for authentication and rate limits
- **Extracts organization name** from target domain (removes TLD)
- **Provides additional coverage** beyond cloned repository scanning

**Example:** For target `example.com`, it will scan the `example` organization on GitHub.

**Requirements:**
- Valid GitHub API token with appropriate scopes
- TruffleHog installed and available in PATH

### 3. Installing Required Tools

#### TruffleHog
```bash
# Using pip
pip install trufflehog

# Using Homebrew (macOS)
brew install trufflehog

# Using Go
go install github.com/trufflesecurity/trufflehog/v3/cmd/trufflehog@latest
```

#### GitLeaks
```bash
# Using Homebrew (macOS)
brew install gitleaks

# Using Go
go install github.com/zricethezav/gitleaks/v8/cmd/gitleaks@latest

# Using Docker
docker pull zricethezav/gitleaks:latest
```

## ⚙️ Advanced Configuration

### 1. Scanning Configuration

```python
'github_scanner': {
    # Scanning limits
    'max_repos_to_scan': 10,     # Max repositories to clone and scan
    'max_file_size_mb': 10,      # Max file size to scan (MB)
    'clone_timeout': 300,         # Git clone timeout (seconds)
    'scan_timeout': 600,          # Scanning timeout (seconds)
    
    # Search limits
    'search_per_page': 100,       # Results per GitHub API page (max 100)
    'max_search_results': 1000,   # Maximum total search results to process
    
    # Rate limiting
    'rate_limit_wait': 60,        # Wait time when rate limited (seconds)
}
```

### 2. Repository Limits Explained

| Limit Type | Default | Description |
|------------|---------|-------------|
| **Search Results** | 100 per page | GitHub API limit (max 100 per request) |
| **Total Search Results** | 1000 | Maximum total results to process across all queries |
| **Repositories to Clone** | 10 | Only top N repos by stars are cloned and scanned |
| **File Size** | 10MB | Files larger than this are skipped during scanning |

**Why These Limits Exist:**
- **GitHub API Rate Limits:** 5000 requests/hour for authenticated users
- **Performance:** Cloning large repositories takes time and disk space
- **Efficiency:** Focus on most relevant repositories (highest stars)
- **Resource Management:** Prevent excessive disk usage and scanning time

### 3. Search Query Configuration

Customize search queries for better results:

```python
'search_queries': [
    '"{target}"',                    # Exact target name
    'org:{target}',                  # Organization search
    'user:{target}',                 # User search
    '{target}',                      # General search
    '"{target}" language:javascript', # JavaScript repositories
    '"{target}" language:python',     # Python repositories
    '"{target}" language:go',         # Go repositories
    '"{target}" language:java',       # Java repositories
    # Add custom queries as needed
    '"{target}" in:readme',          # Search in README files
    '"{target}" in:description',     # Search in descriptions
]
```

### 4. Output Configuration

Control what data is saved:

```python
'github_scanner': {
    'save_repositories': True,    # Save repository information
    'save_secrets': True,         # Save found secrets
    'save_useful_data': True,     # Save useful data analysis
    'save_organizations': True,   # Save organization information
    'save_users': True,           # Save user information
    'generate_report': True,      # Generate markdown summary report
}
```

## 🚀 Usage Examples

### Basic Usage
```bash
# Set your GitHub token
export GITHUB_TOKEN="your_token_here"

# Run GitHub reconnaissance
python run_workflow.py reconnaissance -t example.com -o ./output
```

### Custom Configuration
```bash
# Use custom environment variable
export MY_GITHUB_TOKEN="your_token_here"

# Edit config.py to use MY_GITHUB_TOKEN
# Then run the scanner
python run_workflow.py reconnaissance -t example.com
```

### Tool-Specific Configuration
```python
# Enable only TruffleHog and GitHub org scanning
'enabled_tools': {
    'trufflehog': True,
    'trufflehog_github_org': True,  # Enable GitHub org scanning
    'gitleaks': False,        # Disable GitLeaks
    'custom_patterns': True,
    'gitrob': False,
    'repo-supervisor': False,
    'git-secrets': False
}
```

## 📊 Output Files

The scanner generates several output files:

- `repositories.json` - Found repositories
- `secrets_found.json` - Detected secrets
- `useful_data.json` - Repository analysis
- `organizations.json` - Organization information
- `users.json` - User information
- `summary_report.md` - Markdown summary report

## 🔧 Troubleshooting

### Rate Limiting Issues
- Ensure you have a valid GitHub token
- Check your token permissions
- Increase `rate_limit_wait` in configuration

### Tool Not Found Errors
- Install missing tools using the installation commands above
- Check if tools are in your PATH
- Disable tools you don't need in configuration

### Permission Errors
- Ensure your GitHub token has the necessary scopes
- Check if you're trying to access private repositories without proper permissions

## 📝 Notes

- The scanner automatically detects available tools and skips missing ones
- Rate limiting is handled automatically
- Large repositories are automatically skipped to save time
- All cloned repositories are cleaned up after scanning
- Results are saved in JSON format for easy parsing 