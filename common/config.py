from pathlib import Path
from urllib.parse import urlparse
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG = {
    'tools': {
        'required': ["waybackurls", "gau", "katana", "httpx", "unfurl", "fallparams"],
        'full_mode': ["jsluice", "trufflehog"],
        'python_tools': {
            # These paths are now relative to the project's root, making it more portable.
            'secretfinder': BASE_DIR / "common" / "secretfinder.py",
            'linkfinder': BASE_DIR / "common" / "linkfinder.py"
        }
    },
    'github_scanner': {
        # GitHub API Configuration
        'api_token_env': 'GITHUB_TOKEN',  # Environment variable name for GitHub API token
        'rate_limit_wait': 60,  # Seconds to wait when rate limited
        
        # Tool Selection and Configuration
        'enabled_tools': {
            'trufflehog': True,              # Regular file system scanning
            'trufflehog_github_org': True,   # NEW: GitHub org scanning
            'gitleaks': True,
            'custom_patterns': True,
            'gitrob': False,          # Enable/disable GitRob (if available)
            'repo-supervisor': False, # Enable/disable Repo-Supervisor (if available)
            'git-secrets': False      # Enable/disable Git-Secrets (if available)
        },
        
        # Scanning Configuration
        'max_repos_to_scan': 4,     # Maximum number of repositories to clone and scan
        'max_file_size_mb': 10,      # Maximum file size to scan (in MB)
        'clone_timeout': 300,         # Timeout for git clone operations (seconds)
        'scan_timeout': 600,          # Timeout for scanning operations (seconds)
        
        # Search Configuration
        'search_per_page': 100,       # Number of results per GitHub API page (max 100)
        'max_search_results': 1000,   # Maximum total search results to process
        
        # Advanced GitHub Dorks
        'search_queries': [
            # Basic searches
            '"{target}"',
            'org:{target}',
            'user:{target}',            
            '{target}',
            '"{target}" language:javascript',
            '"{target}" language:python',
            '"{target}" language:go',
            '"{target}" language:java',
            
            # Category 1: Credential & Secret Leakage
            # 'org:"{target}" "aws_access_key_id"',
            # 'org:"{target}" "aws_secret_access_key"',
            # 'org:"{target}" "Authorization: Bearer"',
            # 'org:"{target}" "slack_token" path:*.json',
            # 'org:"{target}" "http://firebaseio.com" -fork',
            # 'org:"{target}" "access_token" path:*.json',
            # 'org:"{target}" "client_secret" path:*.yaml',
            # 'org:"{target}" "DATABASE_URL" path:*.env',
            # 'org:"{target}" "jwt_token" path:*.json',
            # 'org:"{target}" "sendgrid_api_key"',
            
            # Category 2: Internal Config & CI/CD
            # 'org:"{target}" path:**/.env',
            # 'org:"{target}" path:**/config.js',
            # 'org:"{target}" path:**/docker-compose.yml',
            # 'org:"{target}" path:**/config.yaml',
            # 'org:"{target}" path:**/sshd_config',
            # 'org:"{target}" path:**/.github/workflows',
            # 'org:"{target}" path:**/host.json language:json',
            # 'org:"{target}" "DATABASE_PASSWORD" path:*.properties',
            # 'org:"{target}" "service_account" path:*.json',
            
            # Category 3: Dev/Test & Staging Discovery
            # 'org:"{target}" "test_api_key"',
            # 'org:"{target}" "staging."',
            # 'org:"{target}" "debug=true"',
            # 'org:"{target}" "localhost:3000"',
            # 'org:"{target}" "internal_use_only"',
            # 'org:"{target}" "test_credentials"',
            # 'org:"{target}" "example_token" path:*.env',
            
            # Category 4: Cloud Pivot Points
            # 'org:"{target}" "http://s3.amazonaws.com"',
            # 'org:"{target}" "gcloud auth activate-service-account"',
            # 'org:"{target}" "jdbc:mysql://"',
            # 'org:"{target}" "private_key" path:*.txt',
            # 'org:"{target}" path:**/id_rsa',
            # 'org:"{target}" "http://rds.amazonaws.com"',
            
            # Smart Usage Tips - Recent commits
            # 'org:"{target}" "aws_access_key_id" pushed:>2024-01-01',
            # 'org:"{target}" "slack_token" pushed:>2024-01-01',
            # 'org:"{target}" "DATABASE_URL" pushed:>2024-01-01',
            # 'org:"{target}" "client_secret" pushed:>2024-01-01',
            # 'org:"{target}" "service_account" pushed:>2024-01-01',
            # 'org:"{target}" "private_key" pushed:>2024-01-01',
            
            # Reduce noise with -fork
            'org:"{target}" "aws_access_key_id" -fork',
            'org:"{target}" "slack_token" -fork',
            'org:"{target}" "DATABASE_URL" -fork',
            'org:"{target}" "client_secret" -fork',
            'org:"{target}" "service_account" -fork',
            'org:"{target}" "private_key" -fork'
        ],
        
        # Secret Patterns for Custom Scanning
        'secret_patterns': {
            'api_keys': [
                r'[aA][pP][iI][-_]?[kK][eE][yY].*[\'"][0-9a-zA-Z]{32,45}[\'"]',
                r'[aA][pP][iI][-_]?[tT][oO][kK][eE][nN].*[\'"][0-9a-zA-Z]{32,45}[\'"]',
                r'[sS][eE][cC][rR][eE][tT].*[\'"][0-9a-zA-Z]{32,45}[\'"]',
            ],
            'aws_keys': [
                r'AKIA[0-9A-Z]{16}',
                r'aws_access_key_id.*[\'"][0-9A-Z]{20}[\'"]',
                r'aws_secret_access_key.*[\'"][0-9A-Za-z/+=]{40}[\'"]',
            ],
            'google_keys': [
                r'AIza[0-9A-Za-z\-_]{35}',
                r'ya29\.[0-9A-Za-z\-_]+',
            ],
            'database_connections': [
                r'mysql://[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+:[0-9]+/[a-zA-Z0-9._-]+',
                r'postgresql://[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+:[0-9]+/[a-zA-Z0-9._-]+',
                r'mongodb://[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+:[0-9]+/[a-zA-Z0-9._-]+',
            ],
            'private_keys': [
                r'-----BEGIN PRIVATE KEY-----',
                r'-----BEGIN RSA PRIVATE KEY-----',
                r'-----BEGIN DSA PRIVATE KEY-----',
                r'-----BEGIN EC PRIVATE KEY-----',
            ],
            'passwords': [
                r'[pP][aA][sS][sS][wW][oO][rR][dD].*[\'"][^\'"]{8,}[\'"]',
                r'[pP][wW][dD].*[\'"][^\'"]{8,}[\'"]',
            ]
        },
        
        # Output Configuration
        'save_repositories': True,    # Save repository information
        'save_secrets': True,         # Save found secrets
        'save_useful_data': True,     # Save useful data analysis
        'save_organizations': True,   # Save organization information
        'save_users': True,           # Save user information
        'generate_report': True,      # Generate markdown summary report
        
        # Performance Configuration
        'max_concurrent_repos': 3,    # Max concurrent repository processing
        'max_concurrent_scans': 4,    # Max concurrent scans per repo
        'cache_enabled': True,        # Enable API response caching
        'cache_ttl': 3600,           # Cache TTL in seconds (1 hour)
    },
    'timeouts': {
        'command': 300,  # 5 minutes for long-running tools
        'download': 30,
        'analysis': 120, # Increased for potentially large JS files
        'verify': 10,    # Timeout for a single URL verification request
    },
    'excluded_extensions': {'.css', '.png', '.jpg', '.jpeg', '.svg', '.ico', '.gif', '.woff', '.woff2', '.swf', '.map'},
    
    'results_dirs': [
        "jsluice", "secretfinder", "linkfinder", "trufflehog"        
    ],
    'dirs': {
        'results': 'results',
        'downloaded_files': 'downloaded_files',
        'ffuf_results': 'ffuf_results',
        'param_passive': 'param_passive',  # Use underscore
        'fallparams_results': 'fallparams_results',
        'jsluice': 'jsluice',
        'secretfinder': 'secretfinder',
        'linkfinder': 'linkfinder',
        'trufflehog': 'trufflehog',
    },
    'files': {
        'live_js': 'live_js_urls.txt',
        'deduplicated_js': 'deduplicated_js_urls.txt',
        'permutation_wordlist': 'permutation_wordlist.txt',
        'fuzzing_all': 'js_urls_fuzzing_all.txt',
        'fuzzing_new': 'js_urls_fuzzing_new.txt',
    },
    'download': {
        'max_concurrent': 20,
    },
    'validation': {
        'max_workers': 10,  # Reduced from 50 to prevent high CPU usage
    },
    'analysis': {
        'max_workers': 5, # Analysis is CPU-bound, fewer workers are better
    },
    'fuzzingjs': {  # Changed from enumeration
        'fuzz_threads': 40,
        'fuzz_timeout': 10,
    },
    'param_passive': {  # Use underscore instead of param-passive
        'important_extensions': {'.php', '.asp', '.aspx', '.jsp', '.jspx', '.ashx', '.phpx', '.html', '.htm', '.ashx', },
        'max_workers': 20,
    },
    'fallparams': {
        'max_workers': 20,
        'threads': 5,
    },
    'performance': {
        'max_concurrent_downloads': 20,
        'max_concurrent_analysis': 5,
        'max_concurrent_github_requests': 3,
        'cache_enabled': True,
        'cache_ttl': 3600,  # 1 hour
        'timeout_multiplier': 1.5,  # Increase timeouts for slower connections
    },
}
