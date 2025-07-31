import json
from pathlib import Path
from typing import Dict, Any, Set
from tqdm import tqdm
from urllib.parse import urlparse

from common.logger import Logger
from common.utils import run_command, ensure_dir
from common.finder import find_urls_with_extension

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Extracts important file types and parameters from all discovered URLs.
    """
    target = workflow_data['target']
    all_urls = workflow_data.get('all_urls', set())

    if not all_urls:
        logger.warning(f"[{target}] No URLs to process for passive data. Skipping.")
        return {"passive_data_summary": {}}

    logger.info(f"[{target}] Starting passive data extraction from {len(all_urls)} URLs.")
    
    target_output_dir = workflow_data['target_output_dir']
    passive_data_dir = target_output_dir / config['dirs']['passive_data']
    ensure_dir(passive_data_dir)

    important_extensions = config['passive_data']['important_extensions']
    important_urls = set()
    for ext in important_extensions:
        important_urls.update(find_urls_with_extension(all_urls, ext))
    
    (passive_data_dir / 'important_file_urls.txt').write_text('\n'.join(sorted(important_urls)))
    logger.success(f"[{target}] Found {len(important_urls)} URLs with potentially important extensions.")

    all_params = set()
    with tqdm(total=len(all_urls), desc=f"[{target}] Extracting params", unit="url", leave=False) as pbar:
        for url in all_urls:
            params = extract_parameters_with_unfurl(url, logger)
            all_params.update(params)
            pbar.update(1)

    (passive_data_dir / 'all_parameters.txt').write_text('\n'.join(sorted(all_params)))
    logger.success(f"[{target}] Extracted {len(all_params)} unique parameters across all URLs.")
    
    return {
        "passive_data_summary": {
            "important_urls_found": len(important_urls),
            "unique_parameters_found": len(all_params)
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
