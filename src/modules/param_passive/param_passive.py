import json
from pathlib import Path
from typing import Dict, Any, Set
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs

from src.common.logger import Logger
from src.common.utils import run_command, ensure_dir
from src.common.finder import find_urls_with_extension

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Extracts parameters from discovered URLs and identifies important file types.
    """
    target = workflow_data['target']
    
    # Always use all_urls from discovery module (raw discovered URLs)
    if 'all_urls' in workflow_data:
        urls_to_process = workflow_data['all_urls']
        logger.info(f"[{target}] Using all discovered URLs for parameter extraction ({len(urls_to_process)} URLs)")
    else:
        logger.warning(f"[{target}] No discovered URLs available for parameter extraction. Run discovery module first.")
        return {"param_passive_summary": {}}

    logger.info(f"[{target}] Starting parameter extraction for {len(urls_to_process)} URLs...")
    
    target_output_dir = workflow_data['target_output_dir']
    param_passive_dir = target_output_dir / config['dirs']['param_passive']  # Changed from param-passive
    ensure_dir(param_passive_dir)
    
    # Extract important file types
    important_extensions = config['param_passive']['important_extensions']  # Changed from passive_data
    important_urls = set()
    all_params = set()
    
    for url in urls_to_process:
        parsed = urlparse(url)
        
        # Check for important file extensions
        if any(ext in parsed.path.lower() for ext in important_extensions):
            important_urls.add(url)
        
        # Extract parameters using unfurl
        params = extract_parameters_with_unfurl(url, logger)
        for param_name in params:
            all_params.add(param_name)
    
    # Save results
    if important_urls:
        (param_passive_dir / 'important_file_urls.txt').write_text('\n'.join(sorted(important_urls)))
        logger.success(f"[{target}] Found {len(important_urls)} URLs with important file extensions")
    
    if all_params:
        (param_passive_dir / 'all_parameters.txt').write_text('\n'.join(sorted(all_params)))
        logger.success(f"[{target}] Found {len(all_params)} unique parameters")
    
    logger.success(f"[{target}] Parameter extraction complete")
    
    return {
        "param_passive_summary": {
            "important_files": len(important_urls),
            "unique_parameters": len(all_params)
        }
    }

def extract_parameters_with_unfurl(url: str, logger: Logger) -> Set[str]:
    """Uses unfurl to extract parameter keys from a single URL."""
    params = set()
    exit_code, stdout, stderr = run_command(["unfurl", "keys"], input=url)
    if exit_code == 0 and stdout:
        params.update(stdout.splitlines())
    elif stderr:
        logger.debug(f"Unfurl failed for {url}: {stderr}")
    return params
