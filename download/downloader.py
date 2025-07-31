import asyncio
import aiohttp
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from tqdm.asyncio import tqdm

from common.logger import Logger
from common.utils import ensure_dir

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Asynchronously downloads JavaScript files from a list of URLs.
    """
    target = workflow_data['target']
    urls_to_download = workflow_data.get('deduplicated_urls', workflow_data.get('live_urls', []))
    
    
    if not urls_to_download:
        logger.warning(f"[{target}] No URLs to download. Skipping.")
        return {"downloaded_files": []}

    target_output_dir = workflow_data['target_output_dir']
    dl_files_dir = target_output_dir / config['dirs']['downloaded_files']
    ensure_dir(dl_files_dir)

    logger.info(f"[{target}] Downloading {len(urls_to_download)} unique  files to {dl_files_dir}...")
    
    downloaded_files = asyncio.run(
        download_all_files(urls_to_download, dl_files_dir, config, logger)
    )

    logger.success(f"[{target}] Download complete. Successfully downloaded {len(downloaded_files)} files.")
    
    return {"downloaded_files": downloaded_files}

async def download_all_files(urls: List[str], dl_files_dir: Path, config: Dict, logger: Logger) -> List[Path]:
    """Manages the asynchronous download of all URLs."""
    timeout = aiohttp.ClientTimeout(total=config['timeouts']['download'])
    connector = aiohttp.TCPConnector(limit=config['download']['max_concurrent'])
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [download_one_file(session, url, dl_files_dir, logger) for url in urls]
        results = await tqdm.gather(*tasks, desc=f"[{'Downloading':<12}]", unit="file", leave=False)
        downloaded_files = [path for path in results if path is not None]

    return downloaded_files

async def download_one_file(session: aiohttp.ClientSession, url: str, dl_files_dir: Path, logger: Logger) -> Path | None:
    """Coroutine to download a single file."""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                content = await response.read()
                
                sanitized_name = "".join(c if c.isalnum() else '_' for c in url.split('/')[-1])
                url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
                filename = f"{sanitized_name[:50]}_{url_hash}.js"
                file_path = dl_files_dir / filename
                
                with file_path.open('wb') as f:
                    f.write(content)
                return file_path
            else:
                logger.debug(f"Failed to download {url}: Status {response.status}")
                return None
    except Exception as e:
        logger.debug(f"Exception downloading {url}: {e}")
        return None
