import requests
import urllib3
from pathlib import Path
from typing import Set, Dict, Any
import concurrent.futures
from tqdm import tqdm
import time

from common.config import CONFIG
from common.logger import Logger
from common.utils import ensure_dir

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Verifies which of the discovered URLs are live and accessible.
    """
    target = workflow_data['target']
    all_urls = workflow_data.get('all_urls', set())
    
    if not all_urls:
        logger.warning(f"[{target}] No URLs provided to the validation module. Skipping.")
        return {"live_urls": set()}

    logger.info(f"[{target}] Verifying {len(all_urls)} URLs...")
    
    # Process URLs in chunks to prevent memory exhaustion
    chunk_size = 10000  # Process 10k URLs at a time
    live_urls: Set[str] = set()
    max_workers = min(config['validation']['max_workers'], 20)  # Cap at 20 workers
    timeout = config['timeouts']['verify']
    
    # Convert to list for chunking
    url_list = list(all_urls)
    total_chunks = (len(url_list) + chunk_size - 1) // chunk_size
    
    logger.info(f"[{target}] Processing {len(url_list)} URLs in {total_chunks} chunks of {chunk_size}")
    
    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, len(url_list))
        chunk_urls = url_list[start_idx:end_idx]
        
        logger.info(f"[{target}] Processing chunk {chunk_idx + 1}/{total_chunks} ({len(chunk_urls)} URLs)")
        
        chunk_live_urls = set()
        
        with tqdm(total=len(chunk_urls), desc=f"[{target}] Chunk {chunk_idx + 1}/{total_chunks}", unit="url", leave=False) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_url = {executor.submit(check_url, url, timeout): url for url in chunk_urls}
                
                for future in concurrent.futures.as_completed(future_to_url):
                    try:
                        result = future.result()
                        if result:
                            chunk_live_urls.add(result)
                    except Exception as e:
                        logger.debug(f"Error validating URL: {e}")
                    pbar.update(1)
        
        # Add chunk results to main results
        live_urls.update(chunk_live_urls)
        
        # Save intermediate results
        if chunk_live_urls:
            target_output_dir = workflow_data['target_output_dir']
            intermediate_file = target_output_dir / f"live_urls_chunk_{chunk_idx + 1}.txt"
            with intermediate_file.open('w') as f:
                for url in sorted(chunk_live_urls):
                    f.write(f"{url}\n")
            logger.info(f"[{target}] Saved {len(chunk_live_urls)} live URLs from chunk {chunk_idx + 1}")

    logger.success(f"[{target}] Validation complete. Found {len(live_urls)} live URLs out of {len(all_urls)}.")
    
    # Save final results
    target_output_dir = workflow_data['target_output_dir']
    live_js_file = target_output_dir / config['files']['live_js']
    with live_js_file.open('w') as f:
        for url in sorted(list(live_urls)):
            f.write(f"{url}\n")
    logger.info(f"[{target}] Live URLs saved to {live_js_file}")

    return {"live_urls": live_urls}

def check_url(url: str, timeout: int) -> str | None:
    """
    Checks a single URL to see if it's live (returns a 2xx or 3xx status code).
    """
    try:
        with requests.Session() as session:
            session.headers.update({'User-Agent': 'MJSRecon/1.0'})
            response = session.get(url, timeout=timeout, allow_redirects=True, verify=False, stream=True)
            if 200 <= response.status_code < 400:
                return url
    except requests.exceptions.RequestException:
        return None
    except Exception as e:
        # Log unexpected errors but don't crash
        return None
    return None
