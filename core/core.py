import argparse
import sys
from pathlib import Path

from common.config import CONFIG
from common.logger import Logger
from common.help_ui import show_help, show_command_help
from common.tool_checker import check_tools
from common.utils import ensure_dir

# Import run functions from all modules
from discovery.crawler import run as discovery_run
from validation.validator import run as validation_run
from processing.deduplicator import run as processing_run
from download.downloader import run as download_run
from analysis.analyzer import run as analysis_run
from enumeration.enumerator import run as enumeration_run
from reporting.reporter import run as reporting_run
from reconnaissance.github_scanner import run as reconnaissance_run
from passive_data.passive_data import run as passive_data_run
from fallparams.fallparams import run as fallparams_run

def main():
    parser = argparse.ArgumentParser(description="MJSRecon: Modular JavaScript Reconnaissance Tool", add_help=False)
    
    # Define commands and their corresponding functions
    COMMAND_MAP = {
        'discovery': discovery_run,
        'validation': validation_run,
        'processing': processing_run,
        'download': download_run,
        'analysis': analysis_run,
        'enumeration': enumeration_run,
        'passive-data': passive_data_run,
        'fallparams': fallparams_run,
        'reconnaissance': reconnaissance_run,
        'reporting': reporting_run,
    }
    
    parser.add_argument('commands', nargs='*', choices=COMMAND_MAP.keys(), help='Commands to run in sequence.')
    
    # Core arguments
    parser.add_argument('-t', '--target', help='A single target domain (e.g., example.com). For multiple targets, use --targets-file.')
    parser.add_argument('--targets-file', type=Path, help='A file containing a list of target domains, one per line.')
    parser.add_argument('-o', '--output', default='./output', type=Path, help='Base output directory.')
    
    # General options
    parser.add_argument('--independent', action='store_true', help='Run a single command independently. Requires --input.')
    parser.add_argument('--input', type=Path, help='Input file for a module in independent mode.')
    
    # Logging
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose (DEBUG level) logging.')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress console output except for warnings and errors.')
    
    # Discovery options
    parser.add_argument('--gather-mode', choices=['g', 'w', 'k', 'gw', 'gk', 'wk', 'gwk'], default='gwk', help='Tools to use for discovery: g=gau, w=wayback, k=katana.')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Katana crawl depth.')
    
    # Enumeration options
    parser.add_argument('--fuzz-mode', choices=['wordlist', 'permutation', 'both', 'off'], default='off', help='Fuzzing mode.')
    parser.add_argument('--fuzz-wordlist', type=Path, help='Custom wordlist for fuzzing.')
    
    # Help options
    parser.add_argument('-h', '--help', action='store_true', help='Show the main help message and exit.')
    parser.add_argument('--help-command', choices=COMMAND_MAP.keys(), help='Show detailed help for a specific command.')

    args = parser.parse_args()

    # Handle help requests
    if args.help or len(sys.argv) == 1:
        show_help()
        return
    if args.help_command:
        show_command_help(args.help_command)
        return
    
    # Setup logger
    logger = Logger(log_dir=args.output, verbose=args.verbose, quiet=args.quiet)

    # --- Argument Validation ---
    if not args.commands:
        logger.error("No commands specified. Please select one or more commands to run.")
        show_help()
        return

    if not args.independent:
        if not args.target and not args.targets_file:
            logger.error("A target is required. Use -t <domain> or --targets-file <file.txt>.")
            return
        if args.target and args.targets_file:
            logger.error("Please provide a single target with -t OR a file with --targets-file, not both.")
            return
    else: # Independent mode validation
        if len(args.commands) > 1:
            logger.error("Independent mode requires exactly one command.")
            return
        if not args.input:
            logger.error(f"The '{args.commands[0]}' command in independent mode requires an --input file.")
            return
        if not args.input.exists():
            logger.error(f"Input file not found: {args.input}")
            return
            
    if args.fuzz_mode in ['wordlist', 'both'] and not args.fuzz_wordlist:
        logger.error("--fuzz-wordlist is required for 'wordlist' or 'both' fuzzing modes.")
        return
    
    # --- Tool Availability Check ---
    if not check_tools(logger):
        return

    # --- Target Loading ---
    targets = []
    if args.target:
        targets.append(args.target)
    elif args.targets_file:
        try:
            with args.targets_file.open('r') as f:
                targets = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Could not read targets file {args.targets_file}: {e}")
            return
    
    # --- Workflow Execution ---
    for target in targets:
        logger.info(f"🚀 Starting workflow for target: {target}")
        target_output_dir = args.output / target
        ensure_dir(target_output_dir)
        
        workflow_data = {
            'target': target,
            'target_output_dir': target_output_dir
        }

        try:
            for command in args.commands:
                logger.info(f"Executing module: [ {command.upper()} ] for target: {target}")
                
                module_func = COMMAND_MAP[command]
                
                updated_data = module_func(
                    args=args,
                    config=CONFIG,
                    logger=logger,
                    workflow_data=workflow_data
                )

                if updated_data is None:
                    raise Exception(f"Module '{command}' failed to return data.")
                
                workflow_data.update(updated_data)
                
            logger.success(f"✅ Workflow completed for target: {target}")

        except Exception as e:
            logger.error(f"Workflow for target {target} failed during '{command}' module: {e}")
            logger.error("Skipping to next target if any.")
            continue
