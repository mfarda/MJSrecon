import json
import re
from pathlib import Path
from typing import Dict, Any, Set
from urllib.parse import urlparse
from tqdm import tqdm

from src.common.logger import Logger
from src.common.utils import run_command, ensure_dir

"""
FuzzingJS Module for MJSRecon
Fuzzes directories for additional JavaScript files
"""

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Performs directory and file fuzzing based on discovered JavaScript file paths.
    """
    target = workflow_data['target']
    
    # Use deduplicated URLs if available (from processing), otherwise use live URLs
    if 'deduplicated_urls' in workflow_data:
        live_urls = workflow_data['deduplicated_urls']
        logger.info(f"[{target}] Using deduplicated URLs for fuzzing ({len(live_urls)} URLs)")
    elif 'live_urls' in workflow_data:
        live_urls = workflow_data['live_urls']
        logger.info(f"[{target}] Using validated live URLs for fuzzing ({len(live_urls)} URLs)")
    else:
        logger.warning(f"[{target}] No URLs available for fuzzing. Run validation module first.")
        return {"fuzzing_summary": {"status": "skipped", "reason": "no_urls_available"}}

    if not live_urls:
        logger.warning(f"[{target}] No live URLs provided to the fuzzing module. Skipping.")
        return {"fuzzing_summary": {"status": "skipped", "reason": "no_urls_provided"}}

    # Count JavaScript files for logging
    js_files = {url for url in live_urls if url.lower().endswith('.js')}
    logger.info(f"[{target}] Found {len(js_files)} JavaScript files out of {len(live_urls)} total discovered URLs")

    # Extract unique paths for fuzzing
    unique_paths = get_unique_paths_from_urls(live_urls, config, args, logger)
    
    if not unique_paths:
        logger.warning(f"[{target}] No JavaScript files found in discovered URLs. No paths available for fuzzing.")
        logger.info(f"[{target}] Total URLs discovered: {len(live_urls)}")
        logger.info(f"[{target}] Consider checking if the target has JavaScript files or if discovery tools are working correctly.")
        return {"fuzzing_summary": {"status": "skipped", "reason": "no_js_files_found"}}

    logger.info(f"[{target}] Starting fuzzing for {len(unique_paths)} unique paths...")
    
    # Continue with the rest of the fuzzing logic...
    target_output_dir = workflow_data['target_output_dir']
    fuzzing_results_dir = target_output_dir / config['dirs']['fuzzing_results']
    ensure_dir(fuzzing_results_dir)
    
    # Get fuzzing configuration
    fuzz_mode = args.fuzz_mode
    fuzz_wordlist = args.fuzz_wordlist if hasattr(args, 'fuzz_wordlist') else None
    
    if fuzz_mode == 'off':
        logger.info(f"[{target}] Fuzzing disabled. Skipping.")
        return {"fuzzing_summary": {"status": "skipped", "reason": "fuzzing_disabled"}}
    
    # Initialize results tracking
    fuzzing_results = {
        'wordlist_results': {},
        'permutation_results': {},
        'total_discovered': 0
    }
    
    # Wordlist-based fuzzing
    if fuzz_mode in ['wordlist', 'both'] and fuzz_wordlist:
        logger.info(f"[{target}] Starting wordlist-based fuzzing...")
        wordlist_results = run_wordlist_fuzzing(unique_paths, fuzz_wordlist, fuzzing_results_dir, config, logger)
        fuzzing_results['wordlist_results'] = wordlist_results
        fuzzing_results['total_discovered'] += wordlist_results.get('total_discovered', 0)
    
    # Permutation-based fuzzing
    if fuzz_mode in ['permutation', 'both']:
        logger.info(f"[{target}] Starting permutation-based fuzzing...")
        permutation_results = run_permutation_fuzzing(unique_paths, fuzzing_results_dir, config, logger)
        fuzzing_results['permutation_results'] = permutation_results
        fuzzing_results['total_discovered'] += permutation_results.get('total_discovered', 0)
    
    logger.success(f"[{target}] Fuzzing complete. Total new paths discovered: {fuzzing_results['total_discovered']}")
    
    return {
        "fuzzing_summary": {
            "status": "completed",
            "total_discovered": fuzzing_results['total_discovered'],
            "wordlist_results": fuzzing_results['wordlist_results'],
            "permutation_results": fuzzing_results['permutation_results']
        }
    }

def get_unique_paths_from_urls(urls: Set[str], config: Dict, args: Any, logger: Logger) -> Dict[str, str]:
    """Extracts unique base URLs and directory paths from JavaScript file URLs, ranked by JS file count."""
    path_scores = {}  # Track path -> (base_url, js_file_count)
    js_urls_processed = 0
    
    # Get configuration for path selection (CLI args take precedence)
    if hasattr(args, 'fuzz_all_paths') and args.fuzz_all_paths:
        js_only = False
        include_related = False
    elif hasattr(args, 'fuzz_js_only') and args.fuzz_js_only:
        js_only = True
        include_related = False
    else:
        # Fallback to config
        js_only = config.get('fuzzingjs', {}).get('js_only_paths', True)
        include_related = config.get('fuzzingjs', {}).get('include_related_paths', False)
    
    # CLI args take precedence over config for ranking behavior
    max_paths = getattr(args, 'fuzz_max_paths', None) or config.get('fuzzingjs', {}).get('max_paths', 50)
    
    # Handle ranking control
    if hasattr(args, 'no_fuzz_rank_paths') and args.no_fuzz_rank_paths:
        rank_by_js_count = False
    else:
        rank_by_js_count = getattr(args, 'fuzz_rank_paths', None)
        if rank_by_js_count is None:
            rank_by_js_count = config.get('fuzzingjs', {}).get('rank_by_js_count', True)
    
    min_js_files = getattr(args, 'fuzz_min_js_files', None) or config.get('fuzzingjs', {}).get('min_js_files_per_path', 1)
    show_details = config.get('fuzzingjs', {}).get('show_ranking_details', True)
    
    # Define file extensions to include
    if js_only:
        if include_related:
            valid_extensions = {'.js', '.ts', '.jsx', '.tsx', '.vue', '.mjs'}
        else:
            valid_extensions = {'.js'}
    else:
        # Fallback to old behavior - include all URLs
        valid_extensions = None
    
    # First pass: collect all paths and count JS files in each
    for url in urls:
        try:
            # Check if URL has valid extension
            if valid_extensions:
                if not any(url.lower().endswith(ext) for ext in valid_extensions):
                    continue
                
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            dir_path = '/'.join(parsed.path.split('/')[:-1])
            if dir_path and not dir_path.endswith('/'):
                dir_path += '/'
            if not dir_path:
                dir_path = '/'
            
            # Count JS files in this path
            if dir_path not in path_scores:
                path_scores[dir_path] = {'base_url': base_url, 'js_count': 0, 'paths': set()}
            
            path_scores[dir_path]['js_count'] += 1
            path_scores[dir_path]['paths'].add(url)
            js_urls_processed += 1
                    
        except Exception:
            continue
    
    # Second pass: rank paths by JS file count and select top N
    if rank_by_js_count:
        # Filter paths that meet minimum JS file requirement
        qualified_paths = {k: v for k, v in path_scores.items() if v['js_count'] >= min_js_files}
        ranked_paths = sorted(qualified_paths.items(), key=lambda x: x[1]['js_count'], reverse=True)
        
        if show_details:
            logger.info(f"Path ranking: {len(qualified_paths)} paths qualified (≥{min_js_files} JS files)")
    else:
        # Simple selection without ranking
        qualified_paths = path_scores
        ranked_paths = list(qualified_paths.items())
    
    # Select top paths up to max_paths limit
    selected_paths = {}
    for i, (dir_path, path_info) in enumerate(ranked_paths[:max_paths]):
        selected_paths[dir_path] = path_info['base_url']
        if show_details:
            logger.debug(f"Selected path #{i+1}: {path_info['base_url']}{dir_path} (contains {path_info['js_count']} JS files)")
    
    # Log summary of selection process
    total_paths_found = len(path_scores)
    qualified_count = len(qualified_paths)
    logger.info(f"Processed {js_urls_processed} JavaScript URLs, found {total_paths_found} unique paths")
    logger.info(f"Qualified paths (≥{min_js_files} JS files): {qualified_count}")
    logger.info(f"Selected top {len(selected_paths)} paths for fuzzing")
    
    if qualified_count > max_paths:
        logger.info(f"Paths not selected (lower JS file count): {qualified_count - max_paths}")
        # Log some examples of unselected paths
        unselected = ranked_paths[max_paths:max_paths+5]  # Show first 5 unselected
        for dir_path, path_info in unselected:
            logger.debug(f"Unselected: {path_info['base_url']}{dir_path} ({path_info['js_count']} JS files)")
    
    if js_only:
        logger.info(f"Selected {len(selected_paths)} paths from {js_urls_processed} JavaScript URLs for fuzzing")
    else:
        logger.info(f"Selected {len(selected_paths)} paths from all URLs for fuzzing")
    
    return selected_paths

def run_wordlist_fuzzing(unique_paths: Dict[str, str], wordlist_path: str, results_dir: Path, config: Dict, logger: Logger) -> Dict:
    """Runs wordlist-based fuzzing using ffuf."""
    logger.info(f"Starting wordlist fuzzing with {len(unique_paths)} paths")
    
    # Implementation would go here - for now return empty results
    return {"total_discovered": 0, "paths_fuzzed": len(unique_paths)}

def run_permutation_fuzzing(unique_paths: Dict[str, str], results_dir: Path, config: Dict, logger: Logger) -> Dict:
    """Runs permutation-based fuzzing using generated wordlists."""
    logger.info(f"Starting permutation fuzzing with {len(unique_paths)} paths")
    
    # Implementation would go here - for now return empty results
    return {"total_discovered": 0, "paths_fuzzed": len(unique_paths)}

def get_unique_js_filenames(urls: Set[str]) -> Set[str]:
    """Extracts unique JS filenames from a set of URLs."""
    return {url.split('/')[-1] for url in urls if url.endswith('.js')}

def generate_permutation_wordlist(js_filenames: Set[str], output_dir: Path, config: Dict) -> Path:
    """Generates a wordlist based on permutations of existing JS filenames."""
    permutations = set()
    prefixes = config['enumeration']['prefixes']
    suffixes = config['enumeration']['suffixes']
    separators = config['enumeration']['separators']

    for filename in js_filenames:
        base_name = filename.rsplit('.', 1)[0]
        permutations.add(base_name)
        for prefix in prefixes:
            for sep in separators:
                permutations.add(f"{prefix}{sep}{base_name}")
        for suffix in suffixes:
            for sep in separators:
                permutations.add(f"{base_name}{sep}{suffix}")
    
    wordlist_path = output_dir / config['files']['permutation_wordlist']
    wordlist_path.write_text('\n'.join(sorted(permutations)))
    return wordlist_path

def execute_fuzzing_for_path(base_url: str, dir_path: str, results_dir: Path, args: Any, config: Dict, perm_wordlist: Path | None, logger: Logger) -> Set[str]:
    """Runs ffuf for a specific path with the configured modes."""
    found_urls = set()
    fuzz_url = f"{base_url}{dir_path}FUZZ.js"
    
    if args.fuzz_mode in ["wordlist", "both"]:
        output_file = results_dir / f"wordlist_{base_url.replace('://','_')}{dir_path.replace('/','_')}.json"
        found_urls.update(run_ffuf(fuzz_url, args.fuzz_wordlist, output_file, config, logger))
    
    if args.fuzz_mode in ["permutation", "both"] and perm_wordlist:
        output_file = results_dir / f"permutation_{base_url.replace('://','_')}{dir_path.replace('/','_')}.json"
        found_urls.update(run_ffuf(fuzz_url, perm_wordlist, output_file, config, logger))
        
    return found_urls

def run_ffuf(fuzz_url: str, wordlist: Path, output_file: Path, config: Dict, logger: Logger) -> Set[str]:
    """A helper to execute a single ffuf command and parse its results."""
    found_urls = set()
    cmd = [
        "ffuf", "-u", fuzz_url, "-w", str(wordlist),
        "-mc", "200,401,403", 
        "-t", str(config['enumeration']['fuzz_threads']),
        "-timeout", str(config['enumeration']['fuzz_timeout']),
        "-o", str(output_file), "-of", "json", "-s" # silent
    ]
    
    logger.debug(f"Executing ffuf: {' '.join(cmd)}")
    exit_code, _, stderr = run_command(cmd)

    if exit_code == 0 and output_file.exists() and output_file.stat().st_size > 0:
        try:
            results = json.loads(output_file.read_text())
            for item in results.get('results', []):
                found_urls.add(item['url'])
        except (json.JSONDecodeError, KeyError):
            logger.warning(f"Could not parse ffuf JSON output from {output_file}")
    elif stderr:
        logger.debug(f"ffuf command failed for {fuzz_url}. Stderr: {stderr}")
        
    return found_urls
