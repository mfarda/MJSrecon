#// ===== IMPORTS & DEPENDENCIES =====
from pathlib import Path
from typing import Dict, Any, List, Tuple
import concurrent.futures
from tqdm import tqdm

from common.logger import Logger
from common.utils import run_command, ensure_dir

#// ===== UTILITY FUNCTIONS =====
def run_analysis_tool(tool_name: str, cmd_config: Tuple[List[str], str, str], results_dir: Path, config: Dict, logger: Logger):
    """
    Runs a single analysis tool as a subprocess and saves its output.

    Args:
        tool_name (str): The name of the tool being run.
        cmd_config (Tuple): A tuple containing the command list, output filename, and output subdirectory.
        results_dir (Path): The base directory to save results.
        config (Dict): The application configuration.
        logger (Logger): The logger instance.
    """
    command, output_filename, output_subdir = cmd_config
    
    try:
        logger.debug(f"Running tool '{tool_name}' with command: {' '.join(command)}")
        exit_code, stdout, stderr = run_command(command, timeout=config['timeouts']['analysis'])

        if exit_code == 0 and stdout:
            output_dir = results_dir / output_subdir
            ensure_dir(output_dir)
            output_file = output_dir / output_filename
            output_file.write_text(stdout, encoding='utf-8')
            logger.info(f"Tool '{tool_name}' completed successfully. Output at {output_file}")
        elif exit_code != 0:
            # Log non-zero exit codes as warnings, as some tools exit non-zero when nothing is found.
            logger.warning(f"Tool '{tool_name}' finished with exit code {exit_code}.")
            if stderr:
                logger.debug(f"Tool '{tool_name}' stderr: {stderr}")
        else: # exit_code == 0 but no stdout
            logger.info(f"Tool '{tool_name}' ran successfully but produced no output.")

    except Exception as e:
        logger.error(f"An exception occurred while running tool '{tool_name}': {e}")


#// ===== CORE BUSINESS LOGIC =====
def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Analyzes downloaded JavaScript files using various configured tools.
    This function runs each tool once over the directory of downloaded files.
    """
    target = workflow_data['target']
    downloaded_files = workflow_data.get('downloaded_files', [])

    if not downloaded_files:
        logger.warning(f"[{target}] No downloaded files to analyze. Skipping.")
        return {"analysis_summary": {}}

    target_output_dir = workflow_data['target_output_dir']
    download_dir = target_output_dir / config['dirs']['downloaded_files']
    results_dir = target_output_dir / config['dirs']['results']
    ensure_dir(results_dir)

    logger.info(f"[{target}] Analyzing {len(downloaded_files)} files in {download_dir}...")

    # Construct the wildcard path for scripts that need it.
    js_files_pattern = f"{download_dir}/*.js"

    tools_to_run = {
        # Tool Name      Command                                                                          Output File         Output Subdir
        "jsluice_secrets": (["jsluice", "secrets", str(download_dir)],                                     "secrets.json",     "jsluice"),
        "jsluice_urls":    (["jsluice", "urls", str(download_dir)],                                        "urls.json",        "jsluice"),
        "secretfinder":    (["python3", str(config['tools']['python_tools']['secretfinder']), "-i", js_files_pattern, "-o", "cli"], "findings.txt", "secretfinder"),
        "linkfinder":      (["python3", str(config['tools']['python_tools']['linkfinder']), "-i", js_files_pattern, "-o", "cli"],   "findings.txt", "linkfinder"),
        "trufflehog":      (["trufflehog", "filesystem", str(download_dir), "--json"],                       "findings.json",    "trufflehog")
    }

    max_workers = config['analysis']['max_workers']
    with tqdm(total=len(tools_to_run), desc=f"[{target}] Running analysis tools", unit="tool", leave=False) as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_tool = {
                executor.submit(run_analysis_tool, tool_name, cmd_config, results_dir, config, logger): tool_name
                for tool_name, cmd_config in tools_to_run.items()
            }
            for future in concurrent.futures.as_completed(future_to_tool):
                tool_name = future_to_tool[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(f"[{target}] Tool '{tool_name}' generated an exception: {exc}")
                pbar.update(1)

    logger.success(f"[{target}] Analysis complete. Results are in {results_dir}")

    return {"analysis_summary": {"status": "Completed", "results_dir": str(results_dir)}}