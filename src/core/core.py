import argparse
import sys
from pathlib import Path

from src.common.config_loader import load_config
from src.common.logger import Logger
from src.common.help_ui import show_help, show_command_help
from src.common.tool_checker import check_tools
from src.common.utils import ensure_dir

# Import run functions from all modules
from src.modules.discovery.crawler import run as discovery_run
from src.modules.validation.validator import run as validation_run
from src.modules.processing.deduplicator import run as processing_run
from src.modules.download.downloader import run as download_run
from src.modules.analysis.analyzer import run as analysis_run
from src.modules.fuzzing.fuzzingjs import run as fuzzingjs_run
from src.modules.reporting.reporter import run as reporting_run
from src.scanners.github.github import run as github_run
from src.scanners.gitlab.gitlab_scanner import run as gitlab_run
from src.scanners.bitbucket.bitbucket_scanner import run as bitbucket_run
from src.scanners.gitea.gitea_scanner import run as gitea_run
from src.modules.param_passive.param_passive import run as param_passive_run
from src.modules.fallparams.fallparams import run as fallparams_run
from src.modules.sqli.sqli_recon import run as sqli_run

# Define command mapping
COMMAND_MAP = {
    'discovery': discovery_run,
    'validation': validation_run,
    'processing': processing_run,
    'download': download_run,
    'analysis': analysis_run,
    'fuzzingjs': fuzzingjs_run,
    'param-passive': param_passive_run,
    'fallparams': fallparams_run,
    'sqli': sqli_run,
    'github': github_run,
    'gitlab': gitlab_run,
    'bitbucket': bitbucket_run,
    'gitea': gitea_run,
    'reporting': reporting_run,
}

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="MJSRecon - Modular JavaScript Reconnaissance Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # Disable default help to avoid conflicts
        epilog="""
Examples:
  Basic discovery: python run_workflow.py discovery -t example.com
  Full workflow: python run_workflow.py discovery validation processing download analysis -t example.com
  With proxy: python run_workflow.py discovery -t example.com --proxy socks5://127.0.0.1:40000
  Large target: python run_workflow.py discovery -t large-target.com --command-timeout 7200

For detailed help with examples and customization: python run_workflow.py -hhh
        """
    )

    # Core arguments
    parser.add_argument('commands', nargs='+', help='Commands to run (discovery, validation, processing, download, analysis, fuzzingjs, param-passive, fallparams, sqli, github, gitlab, bitbucket, gitea, reporting)')
    parser.add_argument('-t', '--target', help='Target domain or URL')
    parser.add_argument('--targets-file', help='File with multiple targets (one per line)')
    parser.add_argument('-o', '--output', default='./output', help='Output directory (default: ./output)')
    parser.add_argument('--env', choices=['development', 'production', 'testing'], default='development', help='Configuration environment to use.')
    parser.add_argument('--independent', action='store_true', help='Run a single module independently (requires --input)')
    parser.add_argument('--input', help='Input file for independent mode')
    parser.add_argument('--command-timeout', type=int, help='Override command timeout in seconds (default: from config)')

    # Discovery arguments
    parser.add_argument('--gather-mode', default='gwk', help='Discovery tools to use: g=gau, w=waybackurls, k=katana (default: gwk)')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Katana crawl depth (default: 2)')
    parser.add_argument('--uro', action='store_true', help='Use uro to deduplicate/shorten URLs after discovery')

    # Proxy arguments
    parser.add_argument('--proxy', help='Proxy URL (e.g., socks5://127.0.0.1:40000, http://proxy:8080)')
    parser.add_argument('--proxy-auth', help='Proxy authentication (username:password)')
    parser.add_argument('--no-proxy', help='Comma-separated list of hosts to bypass proxy')
    parser.add_argument('--proxy-timeout', type=int, default=30, help='Proxy connection timeout in seconds (default: 30)')
    parser.add_argument('--proxy-verify-ssl', action='store_true', help='Verify SSL certificates when using proxy')

    # Fuzzing arguments
    parser.add_argument('--fuzz-mode', choices=['wordlist', 'permutation', 'both', 'off'], default='off', help='Fuzzing mode (default: off)')
    parser.add_argument('--fuzz-wordlist', help='Custom wordlist for fuzzing')

    # SQL injection arguments
    parser.add_argument('--sqli-scanner', choices=['sqlmap', 'ghauri'], default='sqlmap', help='SQLi scanner to use (default: sqlmap)')
    parser.add_argument('--sqli-full-scan', action='store_true', help='Run full SQLi scan including automated scanning')
    parser.add_argument('--sqli-manual-blind', action='store_true', help='Run manual blind SQLi test (time-based) - DEFAULT MODE')
    parser.add_argument('--sqli-header-test', action='store_true', help='Run header-based blind SQLi test')
    parser.add_argument('--sqli-xor-test', action='store_true', help='Run XOR blind SQLi test')

    # Logging arguments
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose (DEBUG level) logging')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress console output except for warnings/errors')
    parser.add_argument('--timestamp-format', default='%H:%M:%S', help='Timestamp format for console output (default: %%H:%%M:%%S)')

    # Help arguments
    parser.add_argument('-h', '--help', action='store_true', help='Show minimal help')
    parser.add_argument('-hh', action='store_true', help='Show short help with options')
    parser.add_argument('-hhh', action='store_true', help='Show extended help with examples and customization guide')

    args = parser.parse_args()

    # Handle help requests
    if args.hhh:
        from src.common.help_ui import show_help_extended
        show_help_extended()
        return

    if args.hh:
        from src.common.help_ui import show_help
        show_help()
        return

    if args.help:
        from src.common.help_ui import show_help_minimal
        show_help_minimal()
        return

    # Handle regular help
    if len(args.commands) == 1 and args.commands[0] in ['help', '--help', '-h']:
        from src.common.help_ui import show_help_minimal
        show_help_minimal()
        return

    # Handle command-specific help
    if len(args.commands) == 2 and args.commands[0] == 'help':
        from src.common.help_ui import show_command_help
        show_command_help(args.commands[1])
        return
    
    # Setup logger with timestamp format
    logger = Logger(log_dir=args.output, verbose=args.verbose, quiet=args.quiet, timestamp_format=args.timestamp_format)
    
    # Load configuration
    config = load_config(args.env)
    
    # Apply CLI overrides
    if args.command_timeout:
        logger.info(f"Overriding command timeout to {args.command_timeout} seconds")
        config['timeouts']['command'] = args.command_timeout
    
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
        config['proxy']['enabled'] = True
        config['proxy']['url'] = args.proxy
        config['proxy']['auth'] = args.proxy_auth
        config['proxy']['no_proxy'] = args.no_proxy
        config['proxy']['timeout'] = args.proxy_timeout
        config['proxy']['verify_ssl'] = args.proxy_verify_ssl
        
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
    if not check_tools(logger, config):
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
                    config=config,
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
