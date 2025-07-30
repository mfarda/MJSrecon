#!/usr/bin/env python3
"""
Passive Data Collection Module
Runs gather, merges/dedups raw files, extracts parameters with unfurl, and finds/verifies important file URLs
"""

import re
import json
import subprocess
import concurrent.futures
from pathlib import Path
from urllib.parse import urlparse
from typing import Set, List
import requests
from tqdm import tqdm

from ..utils.utils import CONFIG, ensure_dir
from ..gather.gather import run as gather_run
from ..verify.verify import run as verify_run


def run(args, config, logger):
    """Run passive data collection module"""
    # Process each target
    for target in args.targets:
        logger.log('INFO', f"[{target}] Starting passive data collection...")
        
        target_dir = Path(args.output) / target
        ensure_dir(target_dir)
        
        # Step 1: Run gather module
        logger.log('INFO', f"[{target}] Step 1: Running gather module...")
        gather_args = type('Args', (), {
            'targets': [target],
            'output': args.output,
            'independent': False
        })()
        gather_run(gather_args, config, logger)
        
        # Step 2: Merge and deduplicate raw files
        logger.log('INFO', f"[{target}] Step 2: Merging and deduplicating raw files...")
        merged_urls = merge_and_dedup_raw_files(target, target_dir, logger)
        
        if not merged_urls:
            logger.log('WARN', f"[{target}] No URLs found in raw files")
            continue
        
        # Step 3: Use unfurl to find parameters
        logger.log('INFO', f"[{target}] Step 3: Extracting parameters with unfurl...")
        extract_parameters_with_unfurl(target, merged_urls, target_dir, logger)
        
        # Step 4: Find URLs with specific extensions and verify them
        logger.log('INFO', f"[{target}] Step 4: Finding and verifying important file URLs...")
        find_and_verify_important_files(target, merged_urls, target_dir, logger)
        
        logger.log('SUCCESS', f"[{target}] Passive data collection complete")


def merge_and_dedup_raw_files(target: str, target_dir: Path, logger) -> Set[str]:
    """Merge and deduplicate raw files from gather output"""
    all_urls = set()
    
    # Check all gather output files
    gather_files = [
        target_dir / CONFIG['files']['wayback_raw'],
        target_dir / CONFIG['files']['gau_raw'],
        target_dir / CONFIG['files']['katana_raw'],
        target_dir / CONFIG['files']['all_js']
    ]
    
    for file_path in gather_files:
        if file_path.exists():
            logger.log('INFO', f"[{target}] Processing {file_path.name}...")
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
                all_urls.update(urls)
    
    # Save merged and deduplicated URLs
    merged_file = target_dir / CONFIG['passive_data']['files']['merged_raw']
    with open(merged_file, 'w') as f:
        for url in sorted(all_urls):
            f.write(f"{url}\n")
    
    logger.log('INFO', f"[{target}] Merged and deduplicated {len(all_urls)} URLs")
    return all_urls


def extract_parameters_with_unfurl(target: str, urls: Set[str], target_dir: Path, logger):
    """Extract parameters from URLs using unfurl"""
    logger.log('INFO', f"[{target}] Extracting parameters from {len(urls)} URLs...")
    
    parameters_dir = target_dir / CONFIG['passive_data']['files']['parameters_dir']
    ensure_dir(parameters_dir)
    
    all_parameters = set()
    url_parameters = {}
    
    for url in tqdm(urls, desc=f"[{target}] Extracting parameters", unit="url"):
        try:
            # Use unfurl to extract parameters
            exit_code, stdout, stderr = _run_command(["unfurl", "format", url])
            if exit_code == 0 and stdout.strip():
                # Parse unfurl output
                unfurl_data = json.loads(stdout)
                
                # Extract query parameters
                query_params = set()
                if 'query' in unfurl_data:
                    for param in unfurl_data['query']:
                        query_params.add(param['key'])
                
                # Extract path parameters (common patterns)
                path_params = extract_path_parameters(url)
                
                # Combine all parameters
                url_params = query_params.union(path_params)
                if url_params:
                    url_parameters[url] = url_params
                    all_parameters.update(url_params)
        
        except Exception as e:
            logger.log('WARN', f"[{target}] Failed to extract parameters from {url}: {e}")
            continue
    
    # Save results
    if url_parameters:
        # Save URL-specific parameters
        url_params_file = parameters_dir / CONFIG['passive_data']['files']['url_parameters']
        with open(url_params_file, 'w') as f:
            json.dump({url: list(params) for url, params in url_parameters.items()}, f, indent=2)
        
        # Save all unique parameters
        all_params_file = parameters_dir / CONFIG['passive_data']['files']['all_parameters']
        with open(all_params_file, 'w') as f:
            for param in sorted(all_parameters):
                f.write(f"{param}\n")
        
        logger.log('SUCCESS', f"[{target}] Extracted {len(all_parameters)} unique parameters")
        logger.log('INFO', f"[{target}] Parameters saved to: {parameters_dir}")
    else:
        logger.log('WARN', f"[{target}] No parameters found")


def find_and_verify_important_files(target: str, urls: Set[str], target_dir: Path, logger):
    """Find URLs with specific extensions and verify them"""
    # Use config for important extensions
    important_extensions = CONFIG['passive_data']['important_extensions']
    
    important_urls = set()
    
    # Find URLs with important extensions
    for url in urls:
        if has_important_extension(url, important_extensions):
            important_urls.add(url)
    
    if not important_urls:
        logger.log('WARN', f"[{target}] No URLs with important extensions found")
        return
    
    logger.log('INFO', f"[{target}] Found {len(important_urls)} URLs with important extensions")
    
    # Save important URLs
    important_file = target_dir / CONFIG['passive_data']['files']['important_files']
    with open(important_file, 'w') as f:
        for url in sorted(important_urls):
            f.write(f"{url}\n")
    
    # Use existing verify module instead of custom verification
    logger.log('INFO', f"[{target}] Verifying {len(important_urls)} important URLs using verify module...")
    verify_important_urls_with_module(target, important_urls, target_dir, logger)


def has_important_extension(url: str, important_extensions: Set[str]) -> bool:
    """Check if URL has an important file extension"""
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in important_extensions:
            if path.endswith(ext):
                return True
        
        return False
    except:
        return False


def verify_important_urls_with_module(target: str, urls: Set[str], target_dir: Path, logger) -> Set[str]:
    """Verify important URLs using the existing verify module"""
    # Create a temporary file with the important URLs
    temp_input_file = target_dir / "temp_important_urls.txt"
    with open(temp_input_file, 'w') as f:
        for url in urls:
            f.write(f"{url}\n")
    
    # Use the existing verify module
    verify_args = type('Args', (), {
        'input': str(temp_input_file),
        'output': str(target_dir),
        'independent': True
    })()
    
    # Run verify module
    verify_run(verify_args, CONFIG, logger)
    
    # Read the verified URLs from verify module output
    live_important_file = target_dir / CONFIG['passive_data']['files']['live_important']
    live_urls = set()
    
    if live_important_file.exists():
        with open(live_important_file, 'r') as f:
            live_urls = {line.strip() for line in f if line.strip()}
    
    # Clean up temporary file
    if temp_input_file.exists():
        temp_input_file.unlink()
    
    logger.log('SUCCESS', f"[{target}] Found {len(live_urls)} live important URLs")
    return live_urls


def extract_path_parameters(url: str) -> Set[str]:
    """Extract potential path parameters from URL"""
    path_params = set()
    
    try:
        parsed = urlparse(url)
        path = parsed.path
        
        # Look for common parameter patterns in path
        path_patterns = [
            r'/([^/]+)/([^/]+)',  # /param1/param2
            r'/([^/]+)/([^/]+)/([^/]+)',  # /param1/param2/param3
            r'/([^/]+)/([^/]+)/([^/]+)/([^/]+)',  # /param1/param2/param3/param4
        ]
        
        for pattern in path_patterns:
            matches = re.findall(pattern, path)
            for match in matches:
                if isinstance(match, tuple):
                    path_params.update(match)
                else:
                    path_params.add(match)
        
        # Look for numeric IDs
        numeric_ids = re.findall(r'/(\d+)', path)
        path_params.update(numeric_ids)
        
        # Look for UUIDs
        uuid_pattern = r'/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
        uuids = re.findall(uuid_pattern, path, re.IGNORECASE)
        path_params.update(uuids)
        
    except Exception:
        pass
    
    return path_params


def _run_command(cmd, timeout=CONFIG['timeouts']['command']):
    """Run command and return exit code, stdout, stderr"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e) 