import hashlib
import requests
import urllib3
from pathlib import Path
from typing import List, Dict, Any, Set
import concurrent.futures
from tqdm import tqdm

from common.logger import Logger
from common.utils import ensure_dir

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Deduplicates a list of URLs by fetching their content and comparing hashes.
    """
    target = workflow_data['target']
    live_urls = workflow_data.get('live_urls', set())
    
    if not live_urls:
        logger.warning(f"[{target}] No live URLs to process for deduplication. Skipping.")
        return {"deduplicated_urls": []}

    logger.info(f"[{target}] Starting content-based deduplication for {len(live_urls)} URLs...")
    
    unique_urls: List[str] = []
    seen_hashes: Set[str] = set()
    timeout = config['timeouts']['download']
    max_workers = config['download']['max_concurrent']

    with tqdm(total=len(live_urls), desc=f"[{target}] Deduplicating", unit="url", leave=False) as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(download_and_hash, url, timeout): url for url in live_urls}
            for future in concurrent.futures.as_completed(future_to_url):
                url, file_hash = future.result()
                if file_hash and file_hash not in seen_hashes:
                    seen_hashes.add(file_hash)
                    unique_urls.append(url)
                pbar.update(1)

    duplicates_removed = len(live_urls) - len(unique_urls)
    logger.success(f"[{target}] Deduplication complete. Removed {duplicates_removed} duplicates, {len(unique_urls)} unique files remain.")
    
    target_output_dir = workflow_data['target_output_dir']
    deduplicated_file = target_output_dir / config['files']['deduplicated_js']
    with deduplicated_file.open('w') as f:
        for url in sorted(unique_urls):
            f.write(f"{url}\n")
    logger.info(f"[{target}] Deduplicated URLs saved to {deduplicated_file}")
    
    return {"deduplicated_urls": unique_urls}

def download_and_hash(url: str, timeout: int) -> tuple[str, str | None]:
    """Downloads a URL's content and returns its SHA256 hash."""
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True, verify=False)
        if response.status_code == 200:
            return url, hashlib.sha256(response.content).hexdigest()
    except requests.exceptions.RequestException:
        pass
    return url, None
