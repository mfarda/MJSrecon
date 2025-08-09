import asyncio
import aiohttp
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from tqdm.asyncio import tqdm
from src.common.finder import find_urls_with_extension
from src.common.logger import Logger
from src.common.utils import ensure_dir

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Asynchronously downloads JavaScript files from a list of URLs.
    """
    target = workflow_data['target']
    urls_dl = workflow_data.get('uro_urls', workflow_data.get('deduplicated_urls', workflow_data.get('live_urls', [])))
    # Get allowed extensions from config
    allowed_extensions = config['download']['allowed_extensions']
    urls_to_download = []
    
    # Find URLs with any of the allowed extensions
    for ext in allowed_extensions:
        urls_to_download.extend(find_urls_with_extension(urls_dl, ext))
    
    # Remove duplicates while preserving order
    seen = set()
    urls_to_download = [url for url in urls_to_download if not (url in seen or seen.add(url))]
    
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
    
    # Configure proxy for aiohttp session
    proxy = None
    if config['proxy']['enabled'] and config['proxy']['url']:
        proxy = config['proxy']['url']
        logger.info(f"Using proxy for downloads: {proxy}")
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = [download_one_file(session, url, dl_files_dir, logger, proxy) for url in urls]
        results = await tqdm.gather(*tasks, desc=f"[{'Downloading':<12}]", unit="file", leave=False)
        downloaded_files = [path for path in results if path is not None]

    return downloaded_files

def generate_filename_from_url(url: str) -> str:
    """Generate a safe filename from a URL."""
    # Extract original filename and extension
    original_filename = url.split('/')[-1]
    if '.' in original_filename:
        name_part, ext_part = original_filename.rsplit('.', 1)
        file_extension = f".{ext_part}"
    else:
        name_part = original_filename
        file_extension = ".js"  # Default fallback
    
    sanitized_name = "".join(c if c.isalnum() else '_' for c in name_part)
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{sanitized_name[:50]}_{url_hash}{file_extension}"

async def download_one_file(session: aiohttp.ClientSession, url: str, dl_files_dir: Path, logger: Logger, proxy: str = None) -> Path | None:
    """Coroutine to download a single file."""
    try:
        # Use proxy if provided
        if proxy:
            async with session.get(url, proxy=proxy) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    filename = generate_filename_from_url(url)
                    file_path = dl_files_dir / filename
                    
                    with file_path.open('wb') as f:
                        f.write(content)
                    return file_path
                else:
                    logger.debug(f"Failed to download {url}: Status {response.status}")
                    return None
        else:
            # No proxy
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    filename = generate_filename_from_url(url)
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
