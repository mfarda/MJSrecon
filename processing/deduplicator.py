import hashlib
import requests
import urllib3
from pathlib import Path
from typing import List, Dict, Any, Set
import concurrent.futures
from tqdm import tqdm
import time

from common.logger import Logger
from common.utils import ensure_dir

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def download_and_hash_fast(url: str, timeout: int) -> tuple[str, str | None]:
    """Fast download and hash function with minimal overhead."""
    try:
        # Use a single request with optimized settings
        response = requests.get(
            url, 
            timeout=timeout, 
            allow_redirects=True, 
            verify=False,
            headers={'User-Agent': 'MJSRecon/1.0'},
            stream=False  # Load entire content for hashing
        )
        
        if response.status_code == 200 and response.content:
            return url, hashlib.sha256(response.content).hexdigest()
    except Exception:
        pass
    return url, None

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Fast deduplication of URLs by fetching their content and comparing hashes.
    """
    target = workflow_data['target']
    live_urls = workflow_data.get('live_urls', set())
    
    if not live_urls:
        logger.warning(f"[{target}] No live URLs to process for deduplication. Skipping.")
        return {"deduplicated_urls": []}

    logger.info(f"[{target}] Starting fast content-based deduplication for {len(live_urls)} URLs...")
    
    unique_urls: List[str] = []
    seen_hashes: Set[str] = set()
    timeout = config['timeouts']['download']
    max_workers = min(config['download']['max_concurrent'], 50)  # Cap at 50 workers
    
    start_time = time.time()
    
    with tqdm(total=len(live_urls), desc=f"[{target}] Deduplicating", unit="url", leave=False) as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks at once
            future_to_url = {
                executor.submit(download_and_hash_fast, url, timeout): url 
                for url in live_urls
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url, file_hash = future.result()
                if file_hash and file_hash not in seen_hashes:
                    seen_hashes.add(file_hash)
                    unique_urls.append(url)
                pbar.update(1)

    end_time = time.time()
    duplicates_removed = len(live_urls) - len(unique_urls)
    processing_time = end_time - start_time
    urls_per_second = len(live_urls) / processing_time if processing_time > 0 else 0
    
    logger.success(f"[{target}] Deduplication complete in {processing_time:.2f}s ({urls_per_second:.1f} URLs/sec)")
    logger.success(f"[{target}] Removed {duplicates_removed} duplicates, {len(unique_urls)} unique files remain.")
    
    target_output_dir = workflow_data['target_output_dir']
    deduplicated_file = target_output_dir / config['files']['deduplicated_js']
    with deduplicated_file.open('w') as f:
        for url in sorted(unique_urls):
            f.write(f"{url}\n")
    logger.info(f"[{target}] Deduplicated URLs saved to {deduplicated_file}")
    
    return {"deduplicated_urls": unique_urls}

# Keep the old function for backward compatibility
def download_and_hash(url: str, timeout: int) -> tuple[str, str | None]:
    """Legacy download and hash function for backward compatibility."""
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True, verify=False)
        if response.status_code == 200:
            return url, hashlib.sha256(response.content).hexdigest()
    except requests.exceptions.RequestException:
        pass
    return url, None
