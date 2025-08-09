# Code Hosting Platform Scanners

MJSRecon now includes scanners for 4 major code hosting platforms to help you discover secrets and sensitive information in repositories.

## Available Scanners

### 1. GitHub Scanner (`github`)
- **Platform**: GitHub.com and GitHub Enterprise
- **API**: GitHub REST API v3
- **Authentication**: Personal Access Token
- **Features**: Repository search, cloning, secret scanning

### 2. GitLab Scanner (`gitlab`)
- **Platform**: GitLab.com and self-hosted GitLab
- **API**: GitLab API v4
- **Authentication**: Personal Access Token
- **Features**: Project search, cloning, secret scanning

### 3. Bitbucket Scanner (`bitbucket`)
- **Platform**: Bitbucket Cloud and Bitbucket Server
- **API**: Bitbucket REST API v2
- **Authentication**: Username + App Password
- **Features**: Repository search, cloning, secret scanning

### 4. Gitea Scanner (`gitea`)
- **Platform**: Gitea instances (self-hosted)
- **API**: Gitea API v1
- **Authentication**: Personal Access Token
- **Features**: Repository search, cloning, secret scanning

## Setup Instructions

### Environment Variables

Set the appropriate environment variables for each platform:

#### GitHub
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

#### GitLab
```bash
export GITLAB_TOKEN="your_gitlab_personal_access_token"
```

#### Bitbucket
```bash
export BITBUCKET_USERNAME="your_bitbucket_username"
export BITBUCKET_TOKEN="your_bitbucket_app_password"
```

#### Gitea
```bash
export GITEA_TOKEN="your_gitea_personal_access_token"
export GITEA_URL="https://your-gitea-instance.com"  # Optional, defaults to https://gitea.com
```

### Required Tools

Each scanner uses the following tools for secret detection:
- **TruffleHog**: High-confidence secret detection
- **Gitleaks**: Comprehensive secret scanning
- **Custom Patterns**: Regex-based pattern matching

Install these tools:
```bash
# Install TruffleHog
pip install trufflehog

# Install Gitleaks
# Download from: https://github.com/zricethezav/gitleaks/releases

# Custom patterns use grep (usually pre-installed)
```

## Usage Examples

### Scan All Platforms
```bash
python -m mjsrecon github gitlab bitbucket gitea -t example.com -o ./output
```

### Scan Specific Platform
```bash
# GitHub only
python -m mjsrecon github -t example.com -o ./output

# GitLab only
python -m mjsrecon gitlab -t example.com -o ./output

# Bitbucket only
python -m mjsrecon bitbucket -t example.com -o ./output

# Gitea only
python -m mjsrecon gitea -t example.com -o ./output
```

### With Proxy Support
```bash
export HTTP_PROXY="http://proxy:8080"
export HTTPS_PROXY="http://proxy:8080"
python -m mjsrecon github gitlab -t example.com -o ./output
```

## Configuration

Each scanner can be configured in `common/config.py`:

### Rate Limiting
```python
'rate_limit_wait': 60,  # Seconds to wait when rate limited
```

### Repository Limits
```python
'max_repos_to_scan': 4,     # Maximum repositories to scan
'max_search_results': 1000,  # Maximum search results to process
```

### Scanning Tools
```python
'enabled_tools': {
    'trufflehog': True,
    'gitleaks': True,
    'custom_patterns': True,
}
```

### Custom Secret Patterns
```python
'secret_patterns': {
    'api_keys': [
        r'[aA][pP][iI][-_]?[kK][eE][yY].*[\'"][0-9a-zA-Z]{32,45}[\'"]',
    ],
    'aws_keys': [
        r'AKIA[0-9A-Z]{16}',
    ],
    # Add more patterns as needed
}
```

## Output Structure

Each scanner creates its own output directory:

```
output/
├── github/
│   ├── repositories.json
│   ├── secrets.json
│   └── useful_data.json
├── gitlab/
│   ├── repositories.json
│   ├── secrets.json
│   └── useful_data.json
├── bitbucket/
│   ├── repositories.json
│   ├── secrets.json
│   └── useful_data.json
└── gitea/
    ├── repositories.json
    ├── secrets.json
    └── useful_data.json
```

## Secret Detection

### Supported Secret Types
- **API Keys**: Various API key formats
- **AWS Credentials**: Access keys, secret keys
- **Google Keys**: API keys, OAuth tokens
- **Database Connections**: MySQL, PostgreSQL, MongoDB URLs
- **Private Keys**: RSA, DSA, EC private keys
- **Passwords**: Plain text passwords in code
- **Custom Patterns**: User-defined regex patterns

### Confidence Levels
- **High**: Detected by TruffleHog or Gitleaks
- **Medium**: Detected by custom pattern matching

## Best Practices

### 1. Rate Limiting
- Each platform has different rate limits
- Scanners automatically handle rate limiting
- Consider running scans during off-peak hours

### 2. Token Permissions
- Use tokens with minimal required permissions
- GitHub: `repo` scope for private repos
- GitLab: `read_api` scope
- Bitbucket: `repositories:read` scope
- Gitea: `repo` scope

### 3. Target Selection
- Use specific organization/user names
- Avoid overly broad searches
- Focus on relevant repositories

### 4. Output Management
- Regularly clean up cache directories
- Archive results for long-term storage
- Review findings before sharing

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
Error: No GitHub token provided. Skipping GitHub search.
```
**Solution**: Set the appropriate environment variable for the platform.

#### 2. Rate Limiting
```
Rate limited by GitHub API. Waiting...
```
**Solution**: Wait for rate limit to reset or reduce scan frequency.

#### 3. Repository Access
```
Failed to clone repository: Permission denied
```
**Solution**: Ensure your token has appropriate permissions for the repository.

#### 4. Tool Not Found
```
Error running TruffleHog: [Errno 2] No such file or directory
```
**Solution**: Install the required scanning tools.

### Debug Mode
Enable verbose logging to see detailed information:
```bash
python -m mjsrecon github -t example.com -v
```

## Security Considerations

### 1. Token Security
- Store tokens securely
- Use environment variables
- Rotate tokens regularly
- Use minimal required permissions

### 2. Data Handling
- Review findings before sharing
- Handle sensitive data appropriately
- Follow responsible disclosure practices

### 3. Rate Limiting
- Respect platform rate limits
- Avoid aggressive scanning
- Monitor API usage

## Integration with Workflow

The code hosting scanners can be integrated into your reconnaissance workflow:

```bash
# Full reconnaissance including code hosting
python -m mjsrecon discovery validation processing download analysis github gitlab bitbucket gitea reporting -t example.com -o ./output
```

This provides a comprehensive view of both web assets and code repositories related to your target. 