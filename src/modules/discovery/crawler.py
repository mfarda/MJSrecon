import asyncio
import concurrent.futures
from pathlib import Path
from typing import Set, Dict, Any, List, Tuple
import re

from src.common.logger import Logger
from src.common.utils import run_command
from src.common.finder import exclude_urls_with_extensions
from src.common.finder import write_lines_to_file

def get_tool_config(tool_char: str, target: str, depth: int, proxy_url: str = None) -> tuple:
    """Get tool configuration with appropriate proxy settings"""
    if tool_char == 'w':
        # waybackurls - no proxy
        return ("waybackurls", ["waybackurls", target], False, None)
    elif tool_char == 'g':
        # gau - no proxy
        return ("gau", ["gau", "--subs", target], False, None)
    elif tool_char == 'k':
        # katana - with proxy parameter
        if proxy_url:
            # Remove silent mode when using proxy to see output and debug issues
            # Add additional debugging flags for katana
            cmd = ["katana", "-u", f"https://{target}", "-jc", "-d", str(depth), "-proxy", proxy_url, "-v"]
            return ("katana", cmd, True, proxy_url)
        else:
            return ("katana", ["katana", "-u", f"https://{target}", "-jc", "-d", str(depth), "-silent"], False, None)
    else:
        return None

def run_tool_concurrent(tool_name: str, cmd: List[str], config: Dict, logger: Logger, output_dir: Path, use_proxy: bool = False, proxy_url: str = None) -> Tuple[str, Set[str]]:
    """
    Run a single discovery tool and return its results.
    This function is designed to be called concurrently.
    
    Args:
        tool_name: Name of the tool
        cmd: Command to run
        config: Configuration dictionary
        logger: Logger instance
        output_dir: Output directory
        use_proxy: Whether to use proxy for this tool
        proxy_url: Proxy URL to use (if use_proxy is True)
    """
    try:
        logger.info(f"Running {tool_name}...")
        logger.command(f"Command: {' '.join(cmd)}")
        
        # Show timeout info for user awareness
        discovery_timeout = config['timeouts'].get('discovery', config['timeouts']['command'])
        logger.info(f"{tool_name} timeout set to {discovery_timeout} seconds")
        
        # Handle proxy configuration for different tools
        
        if use_proxy and proxy_url:
            logger.debug(f"Using proxy {proxy_url} for {tool_name}")
            # For tools that need proxy, we'll handle it in the command itself
            # The proxy is already added to the command for katana
            exit_code, stdout, stderr = run_command(cmd, timeout=discovery_timeout)
        else:
            # For tools that don't use proxy (gau, waybackurls), clear environment variables
            logger.debug(f"Running {tool_name} without proxy")
            import os
            original_http_proxy = os.environ.get('HTTP_PROXY')
            original_https_proxy = os.environ.get('HTTPS_PROXY')
            
            try:
                # Clear proxy environment variables for this tool
                if 'HTTP_PROXY' in os.environ:
                    del os.environ['HTTP_PROXY']
                if 'HTTPS_PROXY' in os.environ:
                    del os.environ['HTTPS_PROXY']
                
                exit_code, stdout, stderr = run_command(cmd, timeout=discovery_timeout)
            finally:
                # Restore original environment variables
                if original_http_proxy:
                    os.environ['HTTP_PROXY'] = original_http_proxy
                if original_https_proxy:
                    os.environ['HTTPS_PROXY'] = original_https_proxy
        
        if exit_code == 0 and stdout:
            urls = set(stdout.splitlines())
            filtered_urls = exclude_urls_with_extensions(urls, config=config)
            
            # Save individual tool results to target output directory using config
            tool_urls_file = config['files'].get(f'{tool_name}_urls', f'{tool_name}_urls.txt')
            tool_filtered_file = config['files'].get(f'{tool_name}_filtered', f'{tool_name}_filtered_urls.txt')
            
            write_lines_to_file(output_dir / tool_urls_file, urls)
            write_lines_to_file(output_dir / tool_filtered_file, filtered_urls)
            
            logger.success(f"{tool_name} found {len(filtered_urls)} new URLs.")
            return tool_name, filtered_urls
        elif exit_code == -1 and "timed out" in stderr:
            logger.warning(f"{tool_name} timed out after {discovery_timeout} seconds. Partial results may be available.")
            if stdout:
                urls = set(stdout.splitlines())
                filtered_urls = exclude_urls_with_extensions(urls, config=config)
                
                # Save partial results
                tool_urls_file = config['files'].get(f'{tool_name}_urls', f'{tool_name}_urls.txt')
                tool_filtered_file = config['files'].get(f'{tool_name}_filtered', f'{tool_name}_filtered_urls.txt')
                
                write_lines_to_file(output_dir / tool_urls_file, urls)
                write_lines_to_file(output_dir / tool_filtered_file, filtered_urls)
                
                logger.info(f"{tool_name} partial results: {len(filtered_urls)} URLs (tool timed out)")
                return tool_name, filtered_urls
            else:
                logger.error(f"{tool_name} timed out with no output")
                return tool_name, set()
        elif stderr:
            logger.error(f"{tool_name} failed. Stderr: {stderr}")
            return tool_name, set()
        else:
            logger.warning(f"{tool_name} completed but returned no results.")
            return tool_name, set()
            
    except Exception as e:
        logger.error(f"{tool_name} generated an exception: {e}")
        return tool_name, set()

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Gathers all URLs from various sources for a single target using concurrent execution.
    """
    target = workflow_data['target']
    target_output_dir = workflow_data['target_output_dir']
    gather_mode = args.gather_mode
    
    logger.info(f"Gathering URLs for '{target}' using mode '{gather_mode}'...")
    
    # Warn about deep crawling
    if args.depth > 2:
        logger.warning(f"Deep crawling enabled (depth={args.depth}). This may take a long time and generate many URLs.")
    
    # Check if proxy is enabled
    proxy_enabled = hasattr(args, 'proxy') and args.proxy
    proxy_url = args.proxy if proxy_enabled else None
    
    if proxy_enabled:
        logger.info(f"Proxy enabled: {proxy_url}")
        logger.info("gau and waybackurls will run without proxy")
        logger.info(f"katana will use proxy parameter: {proxy_url}")
    
    # Filter tools based on gather mode
    tools_to_run = []
    for tool_char in gather_mode:
        tool_config = get_tool_config(tool_char, target, args.depth, proxy_url)
        if tool_config:
            tool_name, cmd, use_proxy, tool_proxy_url = tool_config
            tools_to_run.append((tool_name, cmd, use_proxy, tool_proxy_url))
    
    if not tools_to_run:
        logger.warning(f"No valid tools found in gather mode '{gather_mode}'")
        return {"all_urls": set()}
    
    # Determine concurrency strategy
    if len(tools_to_run) == 1:
        # Single tool - run sequentially (no benefit from concurrency)
        logger.info(f"Running single tool: {tools_to_run[0][0]}")
        tool_name, cmd, use_proxy, tool_proxy_url = tools_to_run[0]
        result_tool_name, result_urls = run_tool_concurrent(tool_name, cmd, config, logger, target_output_dir, use_proxy, tool_proxy_url)
        all_urls = result_urls
        
    else:
        # Multiple tools - run concurrently
        logger.info(f"Running {len(tools_to_run)} tools concurrently: {[tool[0] for tool in tools_to_run]}")
        
        # Use ThreadPoolExecutor for concurrent execution
        max_workers = min(len(tools_to_run), 10)  # Cap at 10 workers
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tool tasks
            future_to_tool = {
                executor.submit(run_tool_concurrent, tool_name, cmd, config, logger, target_output_dir, use_proxy, tool_proxy_url): tool_name
                for tool_name, cmd, use_proxy, tool_proxy_url in tools_to_run
            }
            
            # Collect results as they complete
            all_urls = set()
            completed_tools = []
            
            for future in concurrent.futures.as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                try:
                    result_tool_name, result_urls = future.result()
                    all_urls.update(result_urls)
                    completed_tools.append(result_tool_name)
                    
                    # Log progress
                    logger.info(f"Completed {result_tool_name} ({len(result_urls)} URLs)")
                    
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
    
    # Save combined results
    total_found = len(all_urls)
    if total_found > 0:
        # Save to target output directory instead of current directory using config
        all_urls_file = config['files'].get('all_urls', 'all_urls.txt')
        write_lines_to_file(target_output_dir / all_urls_file, all_urls)
        
        uro_urls = None
        if hasattr(args, 'uro') and args.uro:
            from src.common.utils import run_uro
            uro_file = target_output_dir / config['files']['uro_urls']
            exit_code, _, uro_stderr = run_uro(target_output_dir / all_urls_file, uro_file)
            if exit_code == 0:
                logger.success(f"Uro deduplication complete. Shortened URLs saved to {uro_file}")
                with uro_file.open('r') as f:
                    uro_urls = set(line.strip() for line in f if line.strip())
            else:
                logger.error(f"Uro failed: {uro_stderr}")
                uro_urls = set()
        
        # For very large datasets, return a smaller sample for immediate processing
        if total_found > 100000:  # If more than 100k URLs
            logger.warning(f"Large dataset detected ({total_found} URLs). Returning sample for immediate processing.")
            # Return a sample of 50k URLs for immediate processing
            sample_size = min(50000, total_found)
            sample_urls = set(list(all_urls)[:sample_size])
            logger.info(f"Returning sample of {len(sample_urls)} URLs for immediate processing.")
            all_urls = sample_urls
        
        logger.success(f"Discovery complete. Found a total of {total_found} unique URLs for '{target}'.")
        
        # Log breakdown by tool if multiple tools were used
        if len(tools_to_run) > 1:
            logger.info(f"Tools completed: {', '.join(completed_tools) if 'completed_tools' in locals() else 'N/A'}")
    else:
        logger.warning(f"Discovery complete. No URLs found for '{target}'.")
        uro_urls = set()

    result = {"all_urls": all_urls}
    if uro_urls is not None:
        result["uro_urls"] = uro_urls
    return result

# Alternative async version for even better performance (optional)
async def run_async(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Async version of the discovery module for maximum performance.
    """
    target = workflow_data['target']
    target_output_dir = workflow_data['target_output_dir']
    gather_mode = args.gather_mode
    
    logger.info(f"Gathering URLs for '{target}' using async mode '{gather_mode}'...")
    
    # Check if proxy is enabled
    proxy_enabled = hasattr(args, 'proxy') and args.proxy
    proxy_url = args.proxy if proxy_enabled else None
    
    if proxy_enabled:
        logger.info(f"Proxy enabled: {proxy_url}")
        logger.info("gau and waybackurls will run without proxy")
        logger.info(f"katana will use proxy parameter: {proxy_url}")
    
    tools_to_run = []
    for tool_char in gather_mode:
        tool_config = get_tool_config(tool_char, target, args.depth, proxy_url)
        if tool_config:
            tool_name, cmd, use_proxy, tool_proxy_url = tool_config
            tools_to_run.append((tool_name, cmd, use_proxy, tool_proxy_url))
    
    if not tools_to_run:
        logger.warning(f"No valid tools found in gather mode '{gather_mode}'")
        return {"all_urls": set()}
    
    async def run_tool_async(tool_name: str, cmd: List[str], use_proxy: bool = False, proxy_url: str = None) -> Tuple[str, Set[str]]:
        """Async version of tool execution with proxy handling"""
        try:
            logger.info(f"Running {tool_name}...")
            logger.command(f"Command: {' '.join(cmd)}")
            
            # Handle proxy configuration for different tools
            if use_proxy and proxy_url:
                logger.debug(f"Using proxy {proxy_url} for {tool_name}")
                # For tools that need proxy, we'll handle it in the command itself
                # The proxy is already added to the command for katana
                loop = asyncio.get_event_loop()
                exit_code, stdout, stderr = await loop.run_in_executor(
                    None, 
                    lambda: run_command(cmd, timeout=config['timeouts']['command'])
                )
            else:
                # For tools that don't use proxy (gau, waybackurls), clear environment variables
                logger.debug(f"Running {tool_name} without proxy")
                import os
                original_http_proxy = os.environ.get('HTTP_PROXY')
                original_https_proxy = os.environ.get('HTTPS_PROXY')
                
                try:
                    # Clear proxy environment variables for this tool
                    if 'HTTP_PROXY' in os.environ:
                        del os.environ['HTTP_PROXY']
                    if 'HTTPS_PROXY' in os.environ:
                        del os.environ['HTTPS_PROXY']
                    
                    loop = asyncio.get_event_loop()
                    exit_code, stdout, stderr = await loop.run_in_executor(
                        None, 
                        lambda: run_command(cmd, timeout=config['timeouts']['command'])
                    )
                finally:
                    # Restore original environment variables
                    if original_http_proxy:
                        os.environ['HTTP_PROXY'] = original_http_proxy
                    if original_https_proxy:
                        os.environ['HTTPS_PROXY'] = original_https_proxy
            
            if exit_code == 0 and stdout:
                urls = set(stdout.splitlines())
                filtered_urls = exclude_urls_with_extensions(urls, config=config)
                
                # Save to target output directory
                tool_urls_file = config['files'].get(f'{tool_name}_urls', f'{tool_name}_urls.txt')
                tool_filtered_file = config['files'].get(f'{tool_name}_filtered', f'{tool_name}_filtered_urls.txt')
                
                write_lines_to_file(target_output_dir / tool_urls_file, urls)
                write_lines_to_file(target_output_dir / tool_filtered_file, filtered_urls)
                
                logger.success(f"{tool_name} found {len(filtered_urls)} new URLs.")
                return tool_name, filtered_urls
            elif stderr:
                logger.error(f"{tool_name} failed. Stderr: {stderr}")
                return tool_name, set()
            else:
                logger.warning(f"{tool_name} completed but returned no results.")
                return tool_name, set()
                
        except Exception as e:
            logger.error(f"{tool_name} generated an exception: {e}")
            return tool_name, set()
    
    # Run all tools concurrently
    tasks = [run_tool_async(tool_name, cmd, use_proxy, tool_proxy_url) for tool_name, cmd, use_proxy, tool_proxy_url in tools_to_run]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Combine results
    all_urls = set()
    completed_tools = []
    
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Tool failed with exception: {result}")
        else:
            tool_name, urls = result
            all_urls.update(urls)
            completed_tools.append(tool_name)
    
    # Save combined results
    total_found = len(all_urls)
    if total_found > 0:
        all_urls_file = config['files'].get('all_urls', 'all_urls.txt')
        write_lines_to_file(target_output_dir / all_urls_file, all_urls)
        
        logger.success(f"Discovery complete. Found a total of {total_found} unique URLs for '{target}'.")
        if len(tools_to_run) > 1:
            logger.info(f"Tools completed: {', '.join(completed_tools)}")
    else:
        logger.warning(f"Discovery complete. No URLs found for '{target}'.")
    
    return {"all_urls": all_urls}

