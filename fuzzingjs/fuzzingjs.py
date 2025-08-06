import json
import re
from pathlib import Path
from typing import Dict, Any, Set
from urllib.parse import urlparse
from tqdm import tqdm

from common.logger import Logger
from common.utils import run_command, ensure_dir

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

    unique_paths = get_unique_paths_from_urls(live_urls, logger)
    if not unique_paths:
        logger.warning(f"[{target}] Could not derive any valid directory paths from live URLs. Skipping fuzzing.")
        return {"fuzzing_summary": {"status": "skipped"}}

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

def get_unique_paths_from_urls(urls: Set[str], logger: Logger) -> Dict[str, str]:
    """Extracts unique base URLs and directory paths from a set of URLs."""
    unique_paths = {}
    for url in urls:
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            dir_path = '/'.join(parsed.path.split('/')[:-1])
            if dir_path and not dir_path.endswith('/'):
                dir_path += '/'
            if not dir_path:
                dir_path = '/'
            if dir_path not in unique_paths:
                unique_paths[dir_path] = base_url
                logger.debug(f"Discovered unique path for fuzzing: {base_url}{dir_path}")
        except Exception:
            continue
    return unique_paths

def get_unique_js_filenames(urls: Set[str]) -> Set[str]:
    """Extracts unique JS filenames from a set of URLs."""
    return {url.split('/')[-1] for url in urls if url.endswith('.js')}

def generate_permutation_wordlist(js_filenames: Set[str], output_dir: Path, config: Dict) -> Path:
    """Generates a wordlist based on permutations of existing JS filenames."""
    permutations = set()
    prefixes = ['app', 'lib', 'vendor', 'dist', 'src', 'core', 'main']
    suffixes = ['bundle', 'min', 'dev', 'prod', 'v1', 'v2']
    separators = ['', '-', '_', '.']

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
