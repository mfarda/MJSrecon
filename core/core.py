import argparse
import sys
from pathlib import Path
from ..common.config import CONFIG
from ..common.logger import Logger
from ..common.help_ui import show_help, show_command_help
from ..discovery.crawler import run as discovery_run
from ..validation.validator import run as validation_run
from ..processing.deduplicator import run as processing_run
from ..download.downloader import run as download_run
from ..analysis.analyzer import run as analysis_run
from ..enumeration.enumerator import run as enumeration_run
from ..common.validator import check_tools
from ..reporting.reporter import run as reporting_run
from ..reconnaissance.github_scanner import run as reconnaissance_run
from ..passive_data.passive_data import run as passive_param_run
from ..fallparam.fallparam import run as fallparam_run


def main():
    # Check for help requests first
    if len(sys.argv) == 1 or '-h' in sys.argv or '--help' in sys.argv:
        if '--help-command' in sys.argv:
            # Find the command after --help-command
            try:
                cmd_index = sys.argv.index('--help-command') + 1
                if cmd_index < len(sys.argv):
                    show_command_help(sys.argv[cmd_index])
                else:
                    show_help()
            except (ValueError, IndexError):
                show_help()
        else:
            show_help()
        return

    parser = argparse.ArgumentParser(description="Modular JS Recon Tool", add_help=False)
    parser.add_argument('commands', nargs='*', choices=['discovery', 'validation', 'processing', 'download', 'analysis', 'enumeration', 'reporting', 'reconnaissance', 'passive-param', 'fallparam'], help='Commands to run in sequence')
    parser.add_argument('-t', '--targets', help='Target domains (comma-separated) - required unless using --input')
    parser.add_argument('-o', '--output', default='./output', help='Output directory')
    parser.add_argument('-d', '--depth', type=int, default=5, help='Katana crawl depth (for discovery)')
    parser.add_argument('--input', help='Input file for the current command (overrides default)')
    parser.add_argument('--independent', action='store_true', help='Run modules independently with custom input files')
    
    # Logging options
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging (debug level)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress info messages (warning level only)')
    
    # Enumeration (fuzzing) specific arguments
    parser.add_argument('--fuzz-mode', choices=['wordlist', 'permutation', 'both', 'off'], default='off', 
                       help='Fuzzing mode: wordlist only, permutation only, both, or off (default: off)')
    parser.add_argument('--fuzz-wordlist', help='Custom wordlist file for fuzzing (required if fuzz-mode is wordlist or both)')
    parser.add_argument('--fuzz-extensions', default='js', help='File extensions to fuzz (default: js)')
    parser.add_argument('--fuzz-status-codes', default='200,403,401', help='HTTP status codes to consider valid (default: 200,403,401)')
    parser.add_argument('--fuzz-threads', type=int, default=40, help='Number of concurrent fuzzing threads (default: 10)')
    parser.add_argument('--fuzz-timeout', type=int, default=10, help='Timeout for each fuzzing request in seconds (default: 30)')
    parser.add_argument('--fuzz-no-timeout', action='store_true', help='Disable timeout for ffuf (useful for large wordlists)')
    
    # Discovery specific arguments
    parser.add_argument('--gather-mode', choices=['g', 'w', 'k', 'gw', 'gk', 'wk', 'gwk'], default='gwk',
                       help='Discovery mode: g=gau, w=wayback, k=katana, gw=gau+wayback, gk=gau+katana, wk=wayback+katana, gwk=all (default: gwk)')
    
    # Reconnaissance (GitHub) specific arguments
    parser.add_argument('--github-token', help='GitHub API token for higher rate limits')
    parser.add_argument('--github-max-repos', type=int, default=10, help='Maximum number of repositories to analyze per target (default: 10)')
    parser.add_argument('--github-scan-tools', choices=['trufflehog', 'gitleaks', 'custom', 'all'], default='all', 
                       help='Secret scanning tools to use (default: all)')
    parser.add_argument('--github-skip-clone', action='store_true', help='Skip cloning repositories (only use API data)')
    
    # Help argument
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')
    parser.add_argument('--help-command', help='Show help for a specific command')
    
    try:
        args = parser.parse_args()
    except SystemExit:
        # If argparse fails, show our custom help
        show_help()
        return

    # Handle help requests
    if args.help or len(args.commands) == 0:
        if args.help_command:
            show_command_help(args.help_command)
        else:
            show_help()
        return

    # Validate arguments
    if not args.independent and not args.targets:
        print("Error: --targets is required unless using --independent mode")
        print("Use -h or --help for more information")
        return
    
    if args.independent and not args.input:
        print("Error: --input is required when using --independent mode")
        print("Use -h or --help for more information")
        return
    
    # Validate enumeration (fuzzing) arguments
    if 'enumeration' in args.commands:
        if args.fuzz_mode in ['wordlist', 'both'] and not args.fuzz_wordlist:
            print("Error: --fuzz-wordlist is required when using fuzz-mode wordlist or both")
            print("Use -h or --help for more information")
            return
        if args.fuzz_wordlist and not Path(args.fuzz_wordlist).exists():
            print(f"Error: Fuzzing wordlist file not found: {args.fuzz_wordlist}")
            return

    # Parse targets (only if provided)
    if args.targets:
        targets = [t.strip() for t in args.targets.split(',')]
        args.targets = targets
    else:
        args.targets = []

    # Setup logger with verbosity options
    log_file = Path(args.output) / "js_recon.log"
    logger = Logger(log_file, verbose=args.verbose, quiet=args.quiet)

    # Check tools only if not in independent mode
    if not args.independent:
        check_tools(logger)

    for command in args.commands:
        if command == 'discovery':
            discovery_run(args, CONFIG, logger)
        elif command == 'validation':
            validation_run(args, CONFIG, logger)
        elif command == 'processing':
            processing_run(args, CONFIG, logger)
        elif command == 'download':
            import asyncio
            asyncio.run(download_run(args, CONFIG, logger))
        elif command == 'analysis':
            analysis_run(args, CONFIG, logger)
        elif command == 'enumeration':
            enumeration_run(args, CONFIG, logger)
        elif command == 'reporting':
            reporting_run(args, CONFIG, logger)
        elif command == 'reconnaissance':
            reconnaissance_run(args, CONFIG, logger)
        elif command == 'passive-param':
            passive_param_run(args, CONFIG, logger)
        elif command == 'fallparam':
            fallparam_run(args, CONFIG, logger)

if __name__ == "__main__":
    main()