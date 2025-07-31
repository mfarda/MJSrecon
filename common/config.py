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
        'fallparam_results': 'fallparam_results',
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
    'fallparam': {
        'max_workers': 20,
        'threads': 5,
    },
}
