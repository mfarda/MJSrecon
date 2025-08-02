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
from fuzzingjs.fuzzingjs import run as fuzzingjs_run
from reporting.reporter import run as reporting_run
from github.github import run as github_run
from gitlab.gitlab_scanner import run as gitlab_run
from bitbucket.bitbucket_scanner import run as bitbucket_run
from gitea.gitea_scanner import run as gitea_run
from param_passive.param_passive import run as param_passive_run
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
        'fuzzingjs': fuzzingjs_run,
        'param-passive': param_passive_run,
        'fallparams': fallparams_run,
        'github': github_run,
        'gitlab': gitlab_run,
        'bitbucket': bitbucket_run,
        'gitea': gitea_run,
        'reporting': reporting_run,
    }
    
    parser.add_argument('commands', nargs='*', help='Commands to run in sequence.')
    
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
    parser.add_argument('--timestamp-format', default='%H:%M:%S', help='Timestamp format for console output (default: %%H:%%M:%%S)')
    
    # Proxy options
    parser.add_argument('--proxy', help='Proxy URL (e.g., socks5://127.0.0.1:1080, http://proxy:8080)')
    parser.add_argument('--proxy-auth', help='Proxy authentication (username:password)')
    parser.add_argument('--no-proxy', help='Comma-separated list of hosts to bypass proxy')
    parser.add_argument('--proxy-timeout', type=int, default=30, help='Proxy connection timeout in seconds (default: 30)')
    parser.add_argument('--proxy-verify-ssl', action='store_true', help='Verify SSL certificates when using proxy')
    
    # Discovery options
    parser.add_argument('--gather-mode', choices=['g', 'w', 'k', 'gw', 'gk', 'wk', 'gwk'], default='gwk', help='Tools to use for discovery: g=gau, w=wayback, k=katana.')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Katana crawl depth.')
    
    # Fuzzing options
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
    
    # Setup logger with timestamp format
    logger = Logger(log_dir=args.output, verbose=args.verbose, quiet=args.quiet, timestamp_format=args.timestamp_format)
    
    # Validate commands after parsing
    if args.commands:
        invalid_commands = [cmd for cmd in args.commands if cmd not in COMMAND_MAP]
        if invalid_commands:
            logger.error(f"Invalid commands: {', '.join(invalid_commands)}")
            logger.error(f"Valid commands: {', '.join(COMMAND_MAP.keys())}")
            return
    
    # Configure proxy settings
    if args.proxy:
        logger.info(f"Configuring proxy: {args.proxy}")
        CONFIG['proxy']['enabled'] = True
        CONFIG['proxy']['url'] = args.proxy
        CONFIG['proxy']['auth'] = args.proxy_auth
        CONFIG['proxy']['no_proxy'] = args.no_proxy
        CONFIG['proxy']['timeout'] = args.proxy_timeout
        CONFIG['proxy']['verify_ssl'] = args.proxy_verify_ssl
        
        # Set environment variables for external tools
        import os
        os.environ['HTTP_PROXY'] = args.proxy
        os.environ['HTTPS_PROXY'] = args.proxy
        if args.no_proxy:
            os.environ['NO_PROXY'] = args.no_proxy

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

        # Load input file for independent mode
        if args.independent and args.input:
            try:
                logger.info(f"Loading URLs from input file: {args.input}")
                with args.input.open('r') as f:
                    urls = set(line.strip() for line in f if line.strip())
                workflow_data['all_urls'] = urls
                logger.info(f"Loaded {len(urls)} URLs from input file")
            except Exception as e:
                logger.error(f"Could not read input file {args.input}: {e}")
                return

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

if __name__ == "__main__":
    main()
