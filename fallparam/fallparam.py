#!/usr/bin/env python3
"""
Fallparam Parameter Discovery Module
Uses fallparams to find dynamic parameters in live URLs
"""

import json
import subprocess
import concurrent.futures
from pathlib import Path
from urllib.parse import urlparse, urljoin
from typing import Set, List, Dict
import requests
from tqdm import tqdm

from ..common.config import CONFIG, ensure_dir


def run(args, config, logger):
    """Run fallparam parameter discovery module"""
    # Process each target
    for target in args.targets:
        logger.log('INFO', f"[{target}] Starting fallparam parameter discovery...")
        
        target_dir = Path(args.output) / target
        ensure_dir(target_dir)
        
        # Get live URLs with important extensions from passive_data output
        live_important_urls = get_live_important_urls(target, target_dir, logger)
        
        if not live_important_urls:
            logger.log('WARN', f"[{target}] No live important URLs found")
            continue
        
        # Run fallparams parameter discovery on each URL
        discover_parameters_with_fallparams(target, live_important_urls, target_dir, logger)
        
        logger.log('SUCCESS', f"[{target}] Fallparam parameter discovery complete")


def get_live_important_urls(target: str, target_dir: Path, logger) -> Set[str]:
    """Get live URLs with important extensions from passive_data output"""
    live_important_file = target_dir / CONFIG['passive_data']['files']['live_important']
    
    if not live_important_file.exists():
        logger.log('WARN', f"[{target}] Live important URLs file not found: {live_important_file}")
        return set()
    
    with open(live_important_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    logger.log('INFO', f"[{target}] Found {len(urls)} live important URLs")
    return set(urls)


def discover_parameters_with_fallparams(target: str, urls: Set[str], target_dir: Path, logger):
    """Discover parameters using fallparams"""
    logger.log('INFO', f"[{target}] Discovering parameters for {len(urls)} URLs...")
    
    fallparams_results_dir = target_dir / CONFIG['fallparam']['results_dir']
    ensure_dir(fallparams_results_dir)
    
    all_discovered_params = {}
    
    for url in tqdm(urls, desc=f"[{target}] Running fallparams", unit="url"):
        try:
            discovered_params = run_fallparams_on_url(target, url, fallparams_results_dir, logger)
            if discovered_params:
                all_discovered_params[url] = discovered_params
        except Exception as e:
            logger.log('WARN', f"[{target}] Failed to run fallparams on {url}: {e}")
            continue
    
    # Save results
    if all_discovered_params:
        save_fallparams_results(target, all_discovered_params, fallparams_results_dir, logger)
    else:
        logger.log('WARN', f"[{target}] No parameters discovered")


def run_fallparams_on_url(target: str, url: str, results_dir: Path, logger) -> Dict:
    """Run fallparams parameter discovery on a single URL"""
    try:
        # Create URL-safe filename
        url_filename = url.replace('://', '_').replace('/', '_').replace(':', '_')
        if len(url_filename) > 100:
            url_filename = url_filename[:100]
        
        output_file = results_dir / f"{url_filename}_fallparams.txt"
        
        # Prepare fallparams command - no wordlist needed, fallparams discovers parameters automatically
        fallparams_cmd = [
            'fallparams',
            '-u', url,
            '-o', str(output_file),
            '-t', str(CONFIG['fallparam']['threads']),  # Reuse ffuf config for threads
            '-c',  # Enable crawling to extract parameters
            '-d', '2',  # Crawl depth of 2
            '-hl'  # Use headless browser for better parameter discovery
        ]
        
        # Run fallparams
        exit_code, stdout, stderr = _run_command(fallparams_cmd, timeout=CONFIG['timeouts']['command'])
        
        if exit_code == 0 and output_file.exists():
            # Parse fallparams results
            discovered_params = parse_fallparams_results(output_file, logger)
            return discovered_params
        else:
            logger.log('WARN', f"[{target}] fallparams failed for {url}: {stderr}")
            return {}
    
    except Exception as e:
        logger.log('WARN', f"[{target}] Error running fallparams on {url}: {e}")
        return {}


def parse_fallparams_results(output_file: Path, logger) -> Dict:
    """Parse fallparams results"""
    try:
        discovered_params = {}
        
        with open(output_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # fallparams outputs discovered parameters directly
                    # Each line should be a parameter name
                    param_name = line
                    discovered_params[param_name] = {
                        'status_code': 200,  # fallparams typically discovers working parameters
                        'url': '',  # Not available in fallparams output
                        'length': 0,
                        'words': 0,
                        'lines': 0
                    }
        
        return discovered_params
    
    except Exception as e:
        logger.log('WARN', f"Failed to parse fallparams results: {e}")
        return {}


def save_fallparams_results(target: str, all_discovered_params: Dict, results_dir: Path, logger):
    """Save fallparams parameter discovery results"""
    # Save detailed results using config
    detailed_results_file = results_dir / CONFIG['fallparam']['files']['detailed_results']
    with open(detailed_results_file, 'w') as f:
        json.dump(all_discovered_params, f, indent=2)
    
    # Save summary using config
    summary_results_file = results_dir / CONFIG['fallparam']['files']['summary_results']
    with open(summary_results_file, 'w') as f:
        f.write(f"Fallparam Parameter Discovery Results for {target}\n")
        f.write("=" * 50 + "\n\n")
        
        total_urls = len(all_discovered_params)
        total_params = sum(len(params) for params in all_discovered_params.values())
        
        f.write(f"Total URLs tested: {total_urls}\n")
        f.write(f"Total parameters discovered: {total_params}\n\n")
        
        for url, params in all_discovered_params.items():
            f.write(f"URL: {url}\n")
            f.write(f"Parameters found: {len(params)}\n")
            for param_name, param_info in params.items():
                f.write(f"  - {param_name}\n")
            f.write("\n")
    
    logger.log('SUCCESS', f"[{target}] Discovered parameters for {len(all_discovered_params)} URLs")
    logger.log('INFO', f"[{target}] Results saved to: {results_dir}")


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