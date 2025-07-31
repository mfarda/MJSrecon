import json
from pathlib import Path
from typing import Dict, Any, Set
from tqdm import tqdm

from common.logger import Logger
from common.utils import run_command, ensure_dir

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Discovers hidden parameters for a given set of URLs using the fallparam tool.
    """
    target = workflow_data['target']
    
    live_urls = workflow_data['live_urls']
    if live_urls:
        urls_to_scan = set(live_urls)
        logger.info(f"[{target}] Found {len(urls_to_scan)}  URLs to scan with fallparam.")
    
    if not urls_to_scan:
        logger.warning(f"[{target}] No URLs to scan with fallparam. Skipping.")
        return {"fallparam_summary": {}}
    logger.info(f"[{target}] Starting dynamic parameter discovery with fallparam.")
    
    target_output_dir = workflow_data['target_output_dir']
    fallparam_results_dir = target_output_dir / config['dirs']['fallparam_results']
    ensure_dir(fallparam_results_dir)

    discovered_params_count = 0
    with tqdm(total=len(urls_to_scan), desc=f"[{target}] Running fallparam", unit="url", leave=False) as pbar:
        for url in urls_to_scan:
            found = run_fallparam_on_url(url, fallparam_results_dir, config, logger)
            if found:
                discovered_params_count += 1
            pbar.update(1)
            
    logger.success(f"[{target}] fallparam scan complete. Found parameters on {discovered_params_count} URLs.")
    
    return {
        "fallparam_summary": {
            "urls_with_params": discovered_params_count,
        }
    }

def run_fallparam_on_url(url: str, results_dir: Path, config: Dict, logger: Logger) -> bool:
    """Runs fallparam on a single URL and saves the output."""
    try:
        url_filename_safe = "".join(c if c.isalnum() else '_' for c in url)
        output_file = results_dir / f"{url_filename_safe[:100]}.txt"
        
        cmd = [
            'fallparams', '-u', url, '-o', str(output_file),
            '-t', str(config['fallparam']['threads']),
            #'-s' # Use headless, depth 2, and silent
        ]
        
        exit_code, _, stderr = run_command(cmd, timeout=config['timeouts']['command'])
        
        if exit_code == 0 and output_file.exists() and output_file.stat().st_size > 0:
            return True
        elif stderr:
            logger.debug(f"fallparam failed for {url}: {stderr}")
            return False
    except Exception as e:
        logger.error(f"Exception running fallparam on {url}: {e}")
    return False
