import os
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional
from urllib.parse import urlparse

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def run_command(cmd: list, timeout: int = 300) -> Tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, and stderr.
    
    Args:
        cmd: List of command and arguments
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy()  # Pass current environment including proxy vars
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)

def configure_proxy_session(session, config: dict) -> None:
    """
    Configure proxy settings for a requests session.
    
    Args:
        session: requests.Session object
        config: Configuration dictionary with proxy settings
    """
    if config['proxy']['enabled'] and config['proxy']['url']:
        proxies = {
            'http': config['proxy']['url'],
            'https': config['proxy']['url']
        }
        session.proxies.update(proxies)
        
        # Configure proxy authentication if provided
        if config['proxy']['auth']:
            proxy_url = urlparse(config['proxy']['url'])
            if '@' not in config['proxy']['url']:  # Auth not in URL
                username, password = config['proxy']['auth'].split(':', 1)
                session.proxies['http'] = f"{proxy_url.scheme}://{username}:{password}@{proxy_url.netloc}"
                session.proxies['https'] = f"{proxy_url.scheme}://{username}:{password}@{proxy_url.netloc}"

def get_proxy_config(config: dict) -> Optional[dict]:
    """
    Get proxy configuration for requests.
    
    Args:
        config: Configuration dictionary with proxy settings
        
    Returns:
        Proxy configuration dict or None if not enabled
    """
    if not config['proxy']['enabled'] or not config['proxy']['url']:
        return None
        
    proxies = {
        'http': config['proxy']['url'],
        'https': config['proxy']['url']
    }
    
    # Add authentication if provided
    if config['proxy']['auth']:
        proxy_url = urlparse(config['proxy']['url'])
        if '@' not in config['proxy']['url']:
            username, password = config['proxy']['auth'].split(':', 1)
            proxies['http'] = f"{proxy_url.scheme}://{username}:{password}@{proxy_url.netloc}"
            proxies['https'] = f"{proxy_url.scheme}://{username}:{password}@{proxy_url.netloc}"
    
    return proxies

def run_uro(input_file: Path, output_file: Path, timeout: int = 300) -> Tuple[int, str, str]:
    """
    Run uro on the input file and write output to output_file.
    Returns (exit_code, stdout, stderr).
    """
    cmd = ["uro", str(input_file)]
    try:
        with output_file.open('w') as out_f:
            result = subprocess.run(
                cmd,
                stdout=out_f,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )
        return result.returncode, '', result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', f"uro timed out after {timeout} seconds"
    except FileNotFoundError:
        return -1, '', "uro command not found"
    except Exception as e:
        return -1, '', str(e)
