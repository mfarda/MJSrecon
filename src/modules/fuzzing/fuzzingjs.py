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
    Performs directory and file fuzzing based on discovered JS file paths.
    """
    if args.fuzz_mode == "off":
        logger.info("Fuzzing is disabled. Skipping enumeration module.")
        return {"fuzzing_summary": {"status": "skipped"}}

    target = workflow_data['target']
    live_urls = workflow_data.get('uro_urls', workflow_data.get('live_urls', set()))

    if not live_urls:
        logger.warning(f"[{target}] No live URLs available for fuzzing. Skipping enumeration.")
        return {"fuzzing_summary": {"status": "skipped"}}

    logger.info(f"[{target}] Starting enumeration (fuzzing) with mode: {args.fuzz_mode}")
    
    # Count JavaScript files for transparency
    js_files = {url for url in live_urls if url.lower().endswith('.js')}
    logger.info(f"[{target}] Found {len(js_files)} JavaScript files out of {len(live_urls)} total discovered URLs")

    unique_paths = get_unique_paths_from_urls(live_urls, config, args, logger)
    if not unique_paths:
        logger.warning(f"[{target}] No JavaScript files found in discovered URLs. No paths available for fuzzing.")
        logger.info(f"[{target}] Total URLs discovered: {len(live_urls)}")
        logger.info(f"[{target}] Consider checking if the target has JavaScript files or if discovery tools are working correctly.")
        return {"fuzzing_summary": {"status": "skipped", "reason": "no_js_files_found"}}

    target_output_dir = workflow_data['target_output_dir']
    ffuf_results_dir = target_output_dir / config['dirs']['ffuf_results']
    ensure_dir(ffuf_results_dir)

    permutation_wordlist = None
    if args.fuzz_mode in ["permutation", "both"]:
        js_filenames = get_unique_js_filenames(live_urls)
        permutation_wordlist = generate_permutation_wordlist(js_filenames, ffuf_results_dir, config)
        logger.info(f"[{target}] Generated {len(permutation_wordlist.read_text().splitlines())} permutations.")

    fuzzing_results = set()
    with tqdm(total=len(unique_paths), desc=f"[{target}] Fuzzing paths", unit="path", leave=False) as pbar:
        for dir_path, base_url in unique_paths.items():
            found_urls = execute_fuzzing_for_path(
                base_url, dir_path, ffuf_results_dir, args, config, permutation_wordlist, logger
            )
            fuzzing_results.update(found_urls)
            pbar.update(1)

    new_findings = fuzzing_results - live_urls
    logger.success(f"[{target}] Fuzzing complete. Found {len(fuzzing_results)} total URLs, including {len(new_findings)} new ones.")

    (target_output_dir / config['files']['fuzzing_all']).write_text('\n'.join(sorted(fuzzing_results)))
    (target_output_dir / config['files']['fuzzing_new']).write_text('\n'.join(sorted(new_findings)))

    return {
        "fuzzing_summary": {
            "total_found": len(fuzzing_results),
            "new_found": len(new_findings),
        }
    }

def get_unique_paths_from_urls(urls: Set[str], config: Dict, args: Any, logger: Logger) -> Dict[str, str]:
    """Extracts unique base URLs and directory paths from JavaScript file URLs only."""
    unique_paths = {}
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
    
    max_paths = config.get('fuzzingjs', {}).get('max_paths', 50)
    
    # Define file extensions to include
    if js_only:
        if include_related:
            valid_extensions = {'.js', '.ts', '.jsx', '.tsx', '.vue', '.mjs'}
        else:
            valid_extensions = {'.js'}
    else:
        # Fallback to old behavior - include all URLs
        valid_extensions = None
    
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
            if dir_path not in unique_paths:
                unique_paths[dir_path] = base_url
                js_urls_processed += 1
                logger.debug(f"Discovered unique path for fuzzing from JS file: {base_url}{dir_path}")
                
                # Stop if we've reached the maximum paths limit
                if len(unique_paths) >= max_paths:
                    logger.info(f"Reached maximum paths limit ({max_paths}). Stopping path discovery.")
                    break
                    
        except Exception:
            continue
    
    if js_only:
        logger.info(f"Processed {js_urls_processed} JavaScript URLs, found {len(unique_paths)} unique paths for fuzzing")
    else:
        logger.info(f"Processed all URLs, found {len(unique_paths)} unique paths for fuzzing")
    return unique_paths

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
