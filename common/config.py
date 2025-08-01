from pathlib import Path
from urllib.parse import urlparse

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
        'search_queries': [
            '"{target}"',
            'org:{target}',
            'user:{target}',            

            '{target}',
            '"{target}" language:javascript',
            '"{target}" language:python',
            '"{target}" language:go',
            '"{target}" language:java'
        ],
        
        # Output Configuration
        'save_repositories': True,    # Save repository information
        'save_secrets': True,         # Save found secrets
        'save_useful_data': True,     # Save useful data analysis
        'save_organizations': True,   # Save organization information
        'save_users': True,           # Save user information
        'generate_report': True,      # Generate markdown summary report
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
        'passive_data': 'passive_data',
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
        'max_workers': 50,
    },
    'analysis': {
        'max_workers': 5, # Analysis is CPU-bound, fewer workers are better
    },
    'enumeration': {
        'fuzz_threads': 40,
        'fuzz_timeout': 10,
    },
    'passive_data': {
        'important_extensions': {'.php', '.asp', '.aspx', '.jsp', '.jspx', '.ashx', '.phpx', '.html', '.htm', '.ashx', },
        'max_workers': 20,
    },
    'fallparams': {
        'max_workers': 20,
        'threads': 5,
    },
}
