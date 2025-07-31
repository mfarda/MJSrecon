import json
from pathlib import Path
import concurrent.futures
from typing import Dict, Any, List
from tqdm import tqdm
from common.logger import Logger
from common.utils import run_command, ensure_dir
from common.finder import find_urls_with_extension

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Analyzes JavaScript files using various tools.
    """
    target = workflow_data['target']
    all_urls = workflow_data.get('all_urls', set())
    js_urls = find_urls_with_extension(all_urls, '.js')
    if not js_urls:
        logger.warning(f"[{target}] No JS files to analyze. Skipping.")
        return {"analysis_summary": {}}

    target_output_dir = workflow_data['target_output_dir']
    results_dir = target_output_dir / config['dirs']['results']
    ensure_dir(results_dir)

    logger.info(f"[{target}] Analyzing {len(js_urls)} JS files...")

    max_workers = config['analysis']['max_workers']
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyze_single_file, Path(js_url), results_dir, config, logger) for js_url in js_urls]

    for future in tqdm(concurrent.futures.as_completed(futures), total=len(js_urls), desc=f"[{target}] Analyzing files", unit="file", leave=False):
        future.result()

    logger.success(f"[{target}] Analysis complete. Results are in {results_dir}")

    return {"analysis_summary": {"status": "Completed"}}

def analyze_single_file(js_file: Path, results_dir: Path, config: Dict, logger: Logger):
    """
    Runs all analysis tools on a single JavaScript file.
    """
    tools = {
    "jsluice_secrets": ["jsluice", "secrets", str(js_file)],
    "jsluice_urls": ["jsluice", "urls", str(js_file)],
    "secretfinder": ["python3", str(config['tools']['python_tools']['secretfinder']), "-i", str(js_file), "-o", "cli"],
    "linkfinder": ["python3", str(config['tools']['python_tools']['linkfinder']), "-i", str(js_file), "-o", "cli"],
    "trufflehog": ["trufflehog", "filesystem", str(js_file), "--json"]}
    for tool_name, cmd in tools.items():
        try:
            exit_code, stdout, stderr = run_command(cmd, timeout=config['timeouts']['analysis'])
            if exit_code == 0 and stdout:
                if "secretfinder" in tool_name or "linkfinder" in tool_name:
                    sub_dir_name = tool_name.split('_')[0]
                    ext = ".txt"
                elif "trufflehog" in tool_name:
                    sub_dir_name = "trufflehog"
                    ext = ".json"
                else:
                    sub_dir_name = "jsluice"
                    ext = ".json"

                output_dir = results_dir / sub_dir_name
                ensure_dir(output_dir)
                output_file = output_dir / f"{js_file.stem}_{tool_name}{ext}"
                output_file.write_text(stdout)
            elif exit_code != 0:
               logger.debug(f"Tool '{tool_name}' failed on {js_file.name} (Exit: {exit_code}). Stderr: {stderr}")

        except Exception as e:
               logger.error(f"Exception running '{tool_name}' on {js_file.name}: {e}")
