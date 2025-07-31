from pathlib import Path
from typing import Set, Dict, Any
import re
from common.config import CONFIG
from common.logger import Logger
from common.utils import run_command
from common.finder import exclude_urls_with_extensions
from common.finder import write_lines_to_file



def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Gathers all URLs from various sources for a single target.
    """
    target = workflow_data['target']
    logger.info(f"Gathering URLs for '{target}' using mode '{args.gather_mode}'...")
    all_urls = set()
    tool_map = {
        'w': ("waybackurls", ["waybackurls", target]),
        'g': ("gau", ["gau", "--subs", target]),
        'k': ("katana", ["katana", "-u", f"https://{target}", "-jc", "-d", str(args.depth), "-silent"])
    }

    for tool_char in args.gather_mode:
        if tool_char in tool_map:
            tool_name, cmd = tool_map[tool_char]
            logger.info(f"Running {tool_name} for {target}...")
            exit_code, stdout, stderr = run_command(cmd, timeout=config['timeouts']['command'])

            if exit_code == 0 and stdout:

                urls = set(stdout.splitlines())
                write_lines_to_file(f"{tool_name}_urls.txt", urls)
                filtered_urls = exclude_urls_with_extensions(urls)
                write_lines_to_file(f"{tool_name}_filtered_urls.txt", filtered_urls)
                all_urls.update(filtered_urls)
                write_lines_to_file(f"{tool_name}_all_urls.txt", all_urls)
                logger.success(f"{tool_name} found {len(filtered_urls)} new URLs.")
            elif stderr:
                logger.error(f"{tool_name} failed for target {target}. Stderr: {stderr}")

    total_found = len(all_urls)
    
    if total_found > 0:
        logger.success(f"Discovery complete. Found a total of {total_found} unique URLs for '{target}'.")
    else:
        logger.warning(f"Discovery complete. No URLs found for '{target}'.")

    return {"all_urls": all_urls}

