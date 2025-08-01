import requests
import urllib3
from pathlib import Path
from typing import Set, Dict, Any
import concurrent.futures
from tqdm import tqdm

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
    
    live_urls: Set[str] = set()
    max_workers = config['validation']['max_workers']
    timeout = config['timeouts']['verify']

    with tqdm(total=len(all_urls), desc=f"[{target}] Verifying URLs", unit="url", leave=False) as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(check_url, url, timeout): url for url in all_urls}
            for future in concurrent.futures.as_completed(future_to_url):
                if future.result():
                    live_urls.add(future.result())
                pbar.update(1)

    logger.success(f"[{target}] Validation complete. Found {len(live_urls)} live URLs out of {len(all_urls)}.")
    
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
    return None
