import json
from pathlib import Path
from typing import Dict, Any, Set
from tqdm import tqdm
from common.logger import Logger
from common.utils import run_command, ensure_dir
from common.finder import find_urls_with_extension
from urllib.parse import urlparse

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Discovers hidden parameters for a given set of URLs using the fallparams tool.
    """
    target = workflow_data['target']
    
    live_urls = workflow_data['live_urls']
    if live_urls:
        seen_paths = set()
        urls_to_scan = [url for url in live_urls 
                        if urlparse(url).query and 
                        (urlparse(url).path not in seen_paths and 
                         seen_paths.add(urlparse(url).path) is None)]
        
        logger.info(f"[{target}] Found {len(urls_to_scan)}  URLs to scan with fallparams.")
    
    if not urls_to_scan:
        logger.warning(f"[{target}] No URLs to scan with fallparams. Skipping.")
        return {"fallparams_summary": {}}
    logger.info(f"[{target}] Starting dynamic parameter discovery with fallparams.")
    
    target_output_dir = workflow_data['target_output_dir']
    fallparams_results_dir = target_output_dir / config['dirs']['fallparams_results']
    ensure_dir(fallparams_results_dir)

    discovered_params_count = 0
    with tqdm(total=len(urls_to_scan), desc=f"[{target}] Running fallparams", unit="url", leave=False) as pbar:
        for url in urls_to_scan:
            found = run_fallparams_on_url(url, fallparams_results_dir, config, logger)
            if found:
                discovered_params_count += 1
            pbar.update(1)
            
    logger.success(f"[{target}] fallparams scan complete. Found parameters on {discovered_params_count} URLs.")
    
    return {
        "fallparams_summary": {
            "urls_with_params": discovered_params_count,
        }
    }

def run_fallparams_on_url(url: str, results_dir: Path, config: Dict, logger: Logger) -> bool:
    """Runs fallparams on a single URL and saves the output."""
    try:
        url_filename_safe = "".join(c if c.isalnum() else '_' for c in url)
        output_file = results_dir / f"{url_filename_safe[:100]}.txt"
        
        cmd = [
            'fallparams', '-u', url, '-o', str(output_file),
            '-t', str(config['fallparams']['threads']),
            #'-s' # Use headless, depth 2, and silent
        ]
        
        exit_code, _, stderr = run_command(cmd, timeout=config['timeouts']['command'])
        
        if exit_code == 0 and output_file.exists() and output_file.stat().st_size > 0:
            return True
        elif stderr:
            logger.debug(f"fallparams failed for {url}: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Exception running fallparams on {url}: {e}")
    return False
