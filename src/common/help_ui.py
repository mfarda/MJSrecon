# NOTE: This file had no logical errors and has been kept as is, with minor formatting adjustments.
# The original file was named 'help-ui.py', renamed to 'help_ui.py' for PEP8 consistency.

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

def show_help_minimal():
    """Displays minimal help message - fits in one screen without colors."""
    console = Console()
    
    console.print("MJSRecon - Modular JavaScript Reconnaissance Tool")
    console.print("=" * 60)
    console.print()
    
    console.print("USAGE:")
    console.print("  python run_workflow.py <commands> -t <target> [options]")
    console.print()
    
    console.print("COMMANDS:")
    console.print("  discovery      - Discover JavaScript URLs")
    console.print("  validation     - Validate discovered URLs")
    console.print("  processing     - Deduplicate URLs by content")
    console.print("  download       - Download JavaScript files")
    console.print("  analysis       - Analyze files for secrets")
    console.print("  fuzzingjs      - Fuzz for additional files")
    console.print("  param-passive  - Extract parameters")
    console.print("  fallparams     - Dynamic parameter discovery")
    console.print("  sqli           - SQL injection reconnaissance")
    console.print("  code host search - GitHub, GitLab, Bitbucket, Gitea scanning")
    console.print("  reporting      - Generate reports")
    console.print()
    
    console.print("OPTIONS:")
    console.print("  -t, --target           Target domain or URL")
    console.print("  --targets-file         File with multiple targets (one per line)")
    console.print("  -o, --output           Output directory (default: ./output)")
    console.print("  --env                  Environment: dev/prod/test (default: dev)")
    console.print("  --independent          Run single module mode")
    console.print("  --input                Input file for independent mode")
    console.print("  --command-timeout      Override command timeout")
    console.print("  --discovery-timeout    Override discovery timeout")
    console.print("  --gather-mode          Tools: g=gau, w=wayback, k=katana (default: gwk)")
    console.print("  -d, --depth            Katana crawl depth (default: 2)")
    console.print("  --uro                  Use uro for URL deduplication")
    console.print("  --proxy                Proxy URL (socks5://127.0.0.1:40000)")
    console.print("  -v, --verbose          Enable verbose logging")
    console.print("  -q, --quiet            Suppress console output")
    console.print()
    
    console.print("EXAMPLES:")
    console.print("  Full workflow: python run_workflow.py discovery validation processing download analysis fuzzingjs param-passive fallparams sqli github reporting -t example.com")
    console.print("  Large target: python run_workflow.py discovery -t large-target.com --proxy socks5://127.0.0.1:40000 --env production --command-timeout 7200")
    console.print("  Independent: python run_workflow.py discovery --independent --input urls.txt --env development")
    console.print()
    
    console.print("HELP LEVELS:")
    console.print("  -h         This minimal help (no colors)")
    console.print("  -hh        Short help with colors and panels")
    console.print("  -hhh       Extended help with examples and customization")
    console.print("  help <cmd> Command-specific help")
    console.print()

def show_help():
    """Displays the short help message with colors and panels."""
    if not RICH_AVAILABLE:
        print("Rich library not found. Please install it for a better UI: pip install rich")
        # Basic fallback help can be added here if needed
        return

    console = Console()
    console.print(Panel("[bold green]MJSRecon[/bold green] - Modular JavaScript Reconnaissance Tool", expand=False))

    usage = Table.grid(padding=1)
    usage.add_row("[bold cyan]Usage:", "python run_workflow.py <commands> -t <target> [options]")
    console.print(usage)

    # Commands
    cmd_table = Table(title="[bold yellow]Workflow Commands[/bold yellow]", box=box.ROUNDED)
    cmd_table.add_column("Command", style="cyan", no_wrap=True)
    cmd_table.add_column("Description")
    commands = {
        'discovery': 'Discovers JavaScript URLs from various sources (gau, waybackurls, katana).',
        'validation': 'Validates discovered URLs are live and accessible.',
        'processing': 'Deduplicates URLs based on content hash.',
        'download': 'Downloads JavaScript files asynchronously (supports multiple extensions).',
        'analysis': 'Analyzes downloaded files for secrets and endpoints.',
        'fuzzingjs': 'Performs directory and file fuzzing with configurable patterns.',
        'param-passive': 'Extracts parameters and important file types.',
        'fallparams': 'Performs dynamic parameter discovery on key URLs.',
        'sqli': 'Performs SQL injection reconnaissance with configurable detection patterns.',
        'github': 'Scans GitHub for repositories, secrets, and useful data.',
        'gitlab': 'Scans GitLab for repositories, secrets, and useful data.',
        'bitbucket': 'Scans Bitbucket for repositories, secrets, and useful data.',
        'gitea': 'Scans Gitea for repositories, secrets, and useful data.',
        'reporting': 'Generates comprehensive reports from all module results.'
    }
    for cmd, desc in commands.items():
        cmd_table.add_row(cmd, desc)
    console.print(cmd_table)

    # Core Options
    core_table = Table(title="[bold blue]Core Options[/bold blue]", box=box.SIMPLE)
    core_table.add_column("Option", style="cyan", no_wrap=True)
    core_table.add_column("Description")
    core_options = {
        '-t, --target': 'Target domain or URL to scan.',
        '--targets-file': 'File with multiple targets (one per line).',
        '-o, --output': 'Base output directory (default: ./output).',
        '--env': 'Configuration environment: development, production, testing (default: development).',
        '--independent': 'Run a single module independently (requires --input).',
        '--input': 'Input file for independent mode.',
        '--command-timeout': 'Override command timeout in seconds (default: from config).',
        '--discovery-timeout': 'Override discovery timeout in seconds (default: from config).'
    }
    for opt, desc in core_options.items():
        core_table.add_row(opt, desc)
    console.print(core_table)

    # Environment Options
    env_table = Table(title="[bold green]Environment Options[/bold green]", box=box.SIMPLE)
    env_table.add_column("Environment", style="cyan", no_wrap=True)
    env_table.add_column("Description")
    env_options = {
        'development': 'Fast scans, minimal timeouts, debug logging. Best for testing and development.',
        'production': 'Optimized for real-world scanning, extended timeouts, high concurrency.',
        'testing': 'Minimal resource usage, quick validation, reduced timeouts for testing.'
    }
    for env, desc in env_options.items():
        env_table.add_row(env, desc)
    console.print(env_table)

    # Discovery Options
    discovery_table = Table(title="[bold green]Discovery Options[/bold green]", box=box.SIMPLE)
    discovery_table.add_column("Option", style="cyan", no_wrap=True)
    discovery_table.add_column("Description")
    discovery_options = {
        '--gather-mode': 'Tools to use for discovery: g=gau, w=waybackurls, k=katana (default: gwk).',
        '-d, --depth': 'Katana crawl depth (default: 2).',
        '--uro': 'Use uro to deduplicate/shorten URLs after discovery.'
    }
    for opt, desc in discovery_options.items():
        discovery_table.add_row(opt, desc)
    console.print(discovery_table)

    # Proxy Options
    proxy_table = Table(title="[bold magenta]Proxy Options[/bold magenta]", box=box.SIMPLE)
    proxy_table.add_column("Option", style="cyan", no_wrap=True)
    proxy_table.add_column("Description")
    proxy_options = {
        '--proxy': 'Proxy URL (e.g., socks5://127.0.0.1:40000, http://proxy:8080).',
        '--proxy-auth': 'Proxy authentication (username:password).',
        '--no-proxy': 'Comma-separated list of hosts to bypass proxy.',
        '--proxy-timeout': 'Proxy connection timeout in seconds (default: 30).',
        '--proxy-verify-ssl': 'Verify SSL certificates when using proxy.'
    }
    for opt, desc in proxy_options.items():
        proxy_table.add_row(opt, desc)
    console.print(proxy_table)

    # Fuzzing Options
    fuzzing_table = Table(title="[bold yellow]Fuzzing Options[/bold yellow]", box=box.SIMPLE)
    fuzzing_table.add_column("Option", style="cyan", no_wrap=True)
    fuzzing_table.add_column("Description")
    fuzzing_options = {
        '--fuzz-mode': 'Fuzzing mode: wordlist, permutation, both, off (default: off).',
        '--fuzz-wordlist': 'Custom wordlist for fuzzing.',
        '--fuzz-js-only': 'Only fuzz paths from JavaScript files (default: true).',
        '--fuzz-all-paths': 'Fuzz paths from all discovered URLs (overrides --fuzz-js-only).',
        '--fuzz-max-paths': 'Maximum number of paths to fuzz (default: 50).',
        '--fuzz-rank-paths': 'Rank paths by JS file count (default: true).',
        '--no-fuzz-rank-paths': 'Disable path ranking (simple selection).',
        '--fuzz-min-js-files': 'Minimum JS files required per path (default: 1).'
    }
    for opt, desc in fuzzing_options.items():
        fuzzing_table.add_row(opt, desc)
    console.print(fuzzing_table)

    # SQLi Options
    sqli_table = Table(title="[bold red]SQL Injection Options[/bold red]", box=box.SIMPLE)
    sqli_table.add_column("Option", style="cyan", no_wrap=True)
    sqli_table.add_column("Description")
    sqli_options = {
        '--sqli-scanner': 'SQLi scanner to use: sqlmap, ghauri (default: sqlmap).',
        '--sqli-full-scan': 'Run full SQLi scan including automated scanning.',
        '--sqli-manual-blind': 'Run manual blind SQLi test (time-based) - DEFAULT MODE.',
        '--sqli-header-test': 'Run header-based blind SQLi test.',
        '--sqli-xor-test': 'Run XOR blind SQLi test.'
    }
    for opt, desc in sqli_options.items():
        sqli_table.add_row(opt, desc)
    console.print(sqli_table)

    # Logging Options
    logging_table = Table(title="[bold cyan]Logging Options[/bold cyan]", box=box.SIMPLE)
    logging_table.add_column("Option", style="cyan", no_wrap=True)
    logging_table.add_column("Description")
    logging_options = {
        '-v, --verbose': 'Enable verbose (DEBUG level) logging.',
        '-q, --quiet': 'Suppress console output except for warnings/errors.',
        '--timestamp-format': 'Timestamp format for console output (default: %H:%M:%S).'
    }
    for opt, desc in logging_options.items():
        logging_table.add_row(opt, desc)
    console.print(logging_table)

    # Quick Examples Panel
    quick_examples_panel = Panel("""
[bold]Quick Examples:[/bold]

[bold]1. Full Workflow (All Modules):[/bold]
[cyan]python run_workflow.py discovery validation processing download analysis fuzzingjs param-passive fallparams sqli github reporting -t example.com[/cyan]

[bold]2. Large Target with Proxy & Production:[/bold]
[cyan]python run_workflow.py discovery -t large-target.com --proxy socks5://127.0.0.1:40000 --env production --command-timeout 7200[/cyan]

[bold]3. Custom Discovery & Fuzzing:[/bold]
[cyan]python run_workflow.py discovery validation processing fuzzingjs -t example.com --gather-mode gk --depth 3 --fuzz-mode both --fuzz-wordlist custom_words.txt[/cyan]

[bold]4. SQL Injection & Independent Mode:[/bold]
[cyan]python run_workflow.py sqli --independent --input urls.txt --sqli-scanner ghauri --sqli-full-scan --env development[/cyan]

[bold]5. Verbose Debug & Multiple Targets:[/bold]
[cyan]python run_workflow.py discovery validation --targets-file targets.txt -v --timestamp-format "%Y-%m-%d %H:%M:%S" --uro[/cyan]
    """, title="[bold green]Quick Examples[/bold green]", border_style="green")
    console.print(quick_examples_panel)

    # Extended Help Notice
    extended_notice = Panel(
        "[bold yellow]For detailed examples, customization guide, and advanced usage:[/bold yellow]\n"
        "[bold cyan]python run_workflow.py -hhh[/bold cyan]\n\n"
        "[bold]For command-specific help:[/bold]\n"
        "[bold cyan]python run_workflow.py help <command>[/bold cyan]",
        title="[bold magenta]Extended Help[/bold magenta]",
        border_style="magenta"
    )
    console.print(extended_notice)

def show_help_extended():
    """Displays extended help with examples, customization guide, and key features."""
    if not RICH_AVAILABLE:
        print("Rich library not found. Please install it for a better UI: pip install rich")
        return

    console = Console()
    console.print(Panel("[bold green]MJSRecon[/bold green] - Extended Help & Examples", expand=False))

    # Key Features
    features_panel = Panel("""
[bold]Key Features:[/bold]
• Environment-specific configs: development, production, testing
• YAML-based configuration in config/ directory
• CLI overrides for timeouts and proxy settings
• External tool paths and settings

[bold]Configurable Features:[/bold]
• Download file extensions (.js, .jsx, .ts, .tsx, .vue, .json)
• Fuzzing patterns (prefixes, suffixes, separators)
• SQL injection detection patterns
• All module timeouts and settings

[bold]Proxy Support:[/bold]
• SOCKS5 proxy (WARP, etc.)
• HTTP/HTTPS proxy
• Authentication support
• Environment variable integration
• Tool-specific proxy behavior

[bold]Performance Features:[/bold]
• Asynchronous downloads
• Concurrent processing
• Configurable timeouts
• Progress tracking
• Partial output preservation on timeout
    """, title="[bold blue]Key Features[/bold blue]", border_style="blue")
    console.print(features_panel)

    # Commands (from -hh)
    cmd_table = Table(title="[bold yellow]Workflow Commands[/bold yellow]", box=box.ROUNDED)
    cmd_table.add_column("Command", style="cyan", no_wrap=True)
    cmd_table.add_column("Description")
    commands = {
        'discovery': 'Discovers JavaScript URLs from various sources (gau, waybackurls, katana).',
        'validation': 'Validates discovered URLs are live and accessible.',
        'processing': 'Deduplicates URLs based on content hash.',
        'download': 'Downloads JavaScript files asynchronously (supports multiple extensions).',
        'analysis': 'Analyzes downloaded files for secrets and endpoints.',
        'fuzzingjs': 'Performs directory and file fuzzing with configurable patterns.',
        'param-passive': 'Extracts parameters and important file types.',
        'fallparams': 'Performs dynamic parameter discovery on key URLs.',
        'sqli': 'Performs SQL injection reconnaissance with configurable detection patterns.',
        'github': 'Scans GitHub for repositories, secrets, and useful data.',
        'gitlab': 'Scans GitLab for repositories, secrets, and useful data.',
        'bitbucket': 'Scans Bitbucket for repositories, secrets, and useful data.',
        'gitea': 'Scans Gitea for repositories, secrets, and useful data.',
        'reporting': 'Generates comprehensive reports from all module results.'
    }
    for cmd, desc in commands.items():
        cmd_table.add_row(cmd, desc)
    console.print(cmd_table)

    # Core Options (from -hh)
    core_table = Table(title="[bold blue]Core Options[/bold blue]", box=box.SIMPLE)
    core_table.add_column("Option", style="cyan", no_wrap=True)
    core_table.add_column("Description")
    core_options = {
        '-t, --target': 'Target domain or URL to scan.',
        '--targets-file': 'File with multiple targets (one per line).',
        '-o, --output': 'Base output directory (default: ./output).',
        '--env': 'Configuration environment: development, production, testing (default: development).',
        '--independent': 'Run a single module independently (requires --input).',
        '--input': 'Input file for independent mode.',
        '--command-timeout': 'Override command timeout in seconds (default: from config).',
        '--discovery-timeout': 'Override discovery timeout in seconds (default: from config).'
    }
    for opt, desc in core_options.items():
        core_table.add_row(opt, desc)
    console.print(core_table)

    # Environment Options (from -hh)
    env_table = Table(title="[bold green]Environment Options[/bold green]", box=box.SIMPLE)
    env_table.add_column("Environment", style="cyan", no_wrap=True)
    env_table.add_column("Description")
    env_options = {
        'development': 'Fast scans, minimal timeouts, debug logging. Best for testing and development.',
        'production': 'Optimized for real-world scanning, extended timeouts, high concurrency.',
        'testing': 'Minimal resource usage, quick validation, reduced timeouts for testing.'
    }
    for env, desc in env_options.items():
        env_table.add_row(env, desc)
    console.print(env_table)

    # Discovery Options (from -hh)
    discovery_table = Table(title="[bold green]Discovery Options[/bold green]", box=box.SIMPLE)
    discovery_table.add_column("Option", style="cyan", no_wrap=True)
    discovery_table.add_column("Description")
    discovery_options = {
        '--gather-mode': 'Tools to use for discovery: g=gau, w=waybackurls, k=katana (default: gwk).',
        '-d, --depth': 'Katana crawl depth (default: 2).',
        '--uro': 'Use uro to deduplicate/shorten URLs after discovery.'
    }
    for opt, desc in discovery_options.items():
        discovery_table.add_row(opt, desc)
    console.print(discovery_table)

    # Proxy Options (from -hh)
    proxy_table = Table(title="[bold magenta]Proxy Options[/bold magenta]", box=box.SIMPLE)
    proxy_table.add_column("Option", style="cyan", no_wrap=True)
    proxy_table.add_column("Description")
    proxy_options = {
        '--proxy': 'Proxy URL (e.g., socks5://127.0.0.1:40000, http://proxy:8080).',
        '--proxy-auth': 'Proxy authentication (username:password).',
        '--no-proxy': 'Comma-separated list of hosts to bypass proxy.',
        '--proxy-timeout': 'Proxy connection timeout in seconds (default: 30).',
        '--proxy-verify-ssl': 'Verify SSL certificates when using proxy.'
    }
    for opt, desc in proxy_options.items():
        proxy_table.add_row(opt, desc)
    console.print(proxy_table)

    # Fuzzing Options (from -hh)
    fuzzing_table = Table(title="[bold yellow]Fuzzing Options[/bold yellow]", box=box.SIMPLE)
    fuzzing_table.add_column("Option", style="cyan", no_wrap=True)
    fuzzing_table.add_column("Description")
    fuzzing_options = {
        '--fuzz-mode': 'Fuzzing mode: wordlist, permutation, both, off (default: off).',
        '--fuzz-wordlist': 'Custom wordlist for fuzzing.',
        '--fuzz-js-only': 'Only fuzz paths from JavaScript files (default: true).',
        '--fuzz-all-paths': 'Fuzz paths from all discovered URLs (overrides --fuzz-js-only).',
        '--fuzz-max-paths': 'Maximum number of paths to fuzz (default: 50).',
        '--fuzz-rank-paths': 'Rank paths by JS file count (default: true).',
        '--no-fuzz-rank-paths': 'Disable path ranking (simple selection).',
        '--fuzz-min-js-files': 'Minimum JS files required per path (default: 1).'
    }
    for opt, desc in fuzzing_options.items():
        fuzzing_table.add_row(opt, desc)
    console.print(fuzzing_table)

    # SQLi Options (from -hh)
    sqli_table = Table(title="[bold red]SQL Injection Options[/bold red]", box=box.SIMPLE)
    sqli_table.add_column("Option", style="cyan", no_wrap=True)
    sqli_table.add_column("Description")
    sqli_options = {
        '--sqli-scanner': 'SQLi scanner to use: sqlmap, ghauri (default: sqlmap).',
        '--sqli-full-scan': 'Run full SQLi scan including automated scanning.',
        '--sqli-manual-blind': 'Run manual blind SQLi test (time-based) - DEFAULT MODE.',
        '--sqli-header-test': 'Run header-based blind SQLi test.',
        '--sqli-xor-test': 'Run XOR blind SQLi test.'
    }
    for opt, desc in sqli_options.items():
        sqli_table.add_row(opt, desc)
    console.print(sqli_table)

    # Logging Options (from -hh)
    logging_table = Table(title="[bold cyan]Logging Options[/bold cyan]", box=box.SIMPLE)
    logging_table.add_column("Option", style="cyan", no_wrap=True)
    logging_table.add_column("Description")
    logging_options = {
        '-v, --verbose': 'Enable verbose (DEBUG level) logging.',
        '-q, --quiet': 'Suppress console output except for warnings/errors.',
        '--timestamp-format': 'Timestamp format for console output (default: %H:%M:%S).'
    }
    for opt, desc in logging_options.items():
        logging_table.add_row(opt, desc)
    console.print(logging_table)

    # Environment Configuration
    env_panel = Panel("""
[bold]Environment Configuration System:[/bold]

[bold]Development Environment (--env development):[/bold]
• Fast scans with minimal timeouts (300s command timeout)
• Debug logging enabled by default
• Reduced concurrency (5-10 concurrent operations)
• Katana depth: 1
• Proxy disabled by default
• Best for: Testing, development, quick validation

[bold]Production Environment (--env production):[/bold]
• Extended timeouts (3600s command timeout)
• Optimized for real-world scanning
• High concurrency (20-50 concurrent operations)
• Katana depth: 3
• Proxy enabled by default
• Best for: Large targets, real-world reconnaissance

[bold]Testing Environment (--env testing):[/bold]
• Minimal resource usage
• Quick validation with reduced timeouts (300s)
• Low concurrency (2-5 concurrent operations)
• Katana depth: 1
• Proxy disabled
• Best for: CI/CD, automated testing, resource-constrained systems

[bold]Configuration Loading Order:[/bold]
1. config/defaults.yaml (base configuration)
2. config/environments.yaml (environment-specific overrides)
3. CLI arguments (command line overrides)

[bold]Environment-Specific Settings:[/bold]
• Timeouts: command, download, analysis, validation
• Concurrency: max_workers, max_concurrent_downloads
• Proxy settings: enabled/disabled, timeouts
• Discovery depth: katana crawl depth
• Logging levels: debug, info, warning, error
    """, title="[bold yellow]Environment Configuration[/bold yellow]", border_style="yellow")
    console.print(env_panel)

    # Example Workflows
    example_panel = Panel("""
[bold]Basic Discovery Scan:[/bold]
python run_workflow.py discovery -t example.com

[bold]Full Workflow with Multiple Commands:[/bold]
python run_workflow.py discovery validation processing download analysis -t example.com -o ./results

[bold]Using Proxy for Stealth:[/bold]
python run_workflow.py discovery validation -t example.com --proxy socks5://127.0.0.1:40000 --env production

[bold]Large Target with Extended Timeout:[/bold]
python run_workflow.py discovery -t large-target.com --command-timeout 7200 --env production

[bold]Multiple Targets from File:[/bold]
python run_workflow.py discovery validation processing --targets-file targets.txt --output ./multi_target_results

[bold]Independent Mode - Single Module:[/bold]
python run_workflow.py discovery --independent --input discovered_urls.txt -o ./independent_results

[bold]Custom Discovery Tools:[/bold]
python run_workflow.py discovery -t example.com --gather-mode gk --depth 3

[bold]Advanced Workflow with Fuzzing and SQLi:[/bold]
python run_workflow.py discovery validation processing fuzzingjs sqli -t example.com --fuzz-mode both --fuzz-wordlist custom_words.txt --sqli-full-scan

[bold]GitHub Secrets Scanning:[/bold]
python run_workflow.py github -t example.com --env development

[bold]Verbose Debug Mode:[/bold]
python run_workflow.py discovery validation processing download analysis -t example.com -v --timestamp-format "%Y-%m-%d %H:%M:%S" -o ./debug_results

[bold]URL Deduplication with uro:[/bold]
python run_workflow.py discovery validation processing -t example.com --uro

[bold]Testing Environment:[/bold]
python run_workflow.py discovery -t test.com --env testing --command-timeout 1800

[bold]Parameter Enumeration:[/bold]
python run_workflow.py param-passive fallparams -t example.com --independent --input validated_urls.txt

[bold]Report Generation:[/bold]
python run_workflow.py reporting --independent --input analysis_results.json -o ./reports
    """, title="[bold magenta]Example Workflows[/bold magenta]", border_style="magenta")
    console.print(example_panel)

    # Customization Guide
    customization_panel = Panel("""
[bold]Customization Examples:[/bold]

[bold]Add New File Extensions:[/bold]
Edit config/defaults.yaml:
download:
  allowed_extensions:
    - ".js"
    - ".jsx"
    - ".ts"
    - ".tsx"
    - ".vue"
    - ".json"
    - ".map"  # Add source maps

[bold]Custom Fuzzing Patterns:[/bold]
Edit config/defaults.yaml:
enumeration:
  prefixes:
    - "app"
    - "lib"
    - "custom"  # Add your prefix
  suffixes:
    - "bundle"
    - "min"
    - "custom"  # Add your suffix

[bold]Custom SQL Injection Patterns:[/bold]
Edit config/defaults.yaml:
sqli:
  vulnerable_extensions:
    - ".php"
    - ".asp"
    - ".custom"  # Add your extension
    """, title="[bold green]Customization Guide[/bold green]", border_style="green")
    console.print(customization_panel)

    # Configuration System
    config_panel = Panel("""
[bold]Configuration System:[/bold]

[bold]Environment Profiles:[/bold]
• development: Fast scans, minimal timeouts, debug logging
• production: Optimized for real-world scanning, extended timeouts
• testing: Minimal resource usage, quick validation

[bold]Configuration Files:[/bold]
• config/defaults.yaml - Base configuration with all module settings
• config/environments.yaml - Environment-specific overrides
• config/*_scanner.yaml - Scanner-specific configurations
• config/patterns.yaml - Regex patterns for secret detection
• config/secrets.yaml - API tokens and secrets

[bold]CLI Overrides:[/bold]
• --env: Select environment profile
• --command-timeout: Override command timeout
• --proxy: Override proxy settings
• All module-specific options override config values

[bold]Configuration Loading Order:[/bold]
1. config/defaults.yaml (base configuration)
2. config/environments.yaml (environment overrides)
3. config/*_scanner.yaml (scanner-specific)
4. config/patterns.yaml (regex patterns)
5. config/secrets.yaml (API tokens)
6. CLI arguments (command line overrides)
    """, title="[bold yellow]Configuration System[/bold yellow]", border_style="yellow")
    console.print(config_panel)

    # Troubleshooting
    troubleshooting_panel = Panel("""
[bold]Common Issues & Solutions:[/bold]

[bold]Command Timeouts:[/bold]
• Increase timeout: --command-timeout 7200
• Use production environment: --env production
• Check network connectivity

[bold]Proxy Issues:[/bold]
• Verify proxy is running: curl --socks5 127.0.0.1:40000 http://ipinfo.io
• Install SOCKS support: pip install requests[socks] PySocks
• Check proxy authentication

[bold]Missing Tools:[/bold]
• Run tool check: python run_workflow.py --help
• Install missing tools (see installation guide)
• Verify PATH environment variable

[bold]Configuration Issues:[/bold]
• Check config/defaults.yaml for missing settings
• Verify environment-specific overrides in config/environments.yaml
• Ensure all required configuration keys are present

[bold]Debug Mode:[/bold]
Enable verbose logging for troubleshooting:
python run_workflow.py discovery -t example.com -v
    """, title="[bold red]Troubleshooting[/bold red]", border_style="red")
    console.print(troubleshooting_panel)

def show_command_help(command: str):
    """Shows detailed help for a specific command."""
    if not RICH_AVAILABLE:
        print(f"Help for '{command}': This feature requires Rich library.")
        return

    console = Console()
    
    command_help = {
        'discovery': {
            'description': 'Discovers JavaScript URLs from various sources using external tools.',
            'tools': ['gau', 'waybackurls', 'katana'],
            'output': 'discovered_urls.txt',
            'options': {
                '--gather-mode': 'Select which tools to use (g=gau, w=waybackurls, k=katana)',
                '-d, --depth': 'Set katana crawl depth (default: 2)',
                '--uro': 'Use uro for URL deduplication after discovery'
            }
        },
        'validation': {
            'description': 'Validates discovered URLs to ensure they are live and accessible.',
            'output': 'live_js_urls.txt',
            'options': {
                '--proxy': 'Use proxy for validation requests',
                '--env': 'Environment affects concurrency and timeouts'
            }
        },
        'processing': {
            'description': 'Deduplicates URLs based on content hash to remove duplicates.',
            'output': 'deduplicated_js_urls.txt',
            'options': {
                '--proxy': 'Use proxy for content downloads',
                '--env': 'Environment affects download timeouts and concurrency'
            }
        },
        'download': {
            'description': 'Downloads JavaScript files asynchronously with multi-extension support.',
            'output': 'downloaded_files/ (with extension subdirectories)',
            'configurable': 'File extensions in config/download.allowed_extensions',
            'options': {
                '--proxy': 'Use proxy for downloads',
                '--env': 'Environment affects concurrency and timeouts'
            }
        },
        'analysis': {
            'description': 'Analyzes downloaded JavaScript files for secrets and endpoints.',
            'output': 'results/ (with tool-specific subdirectories)',
            'tools': ['linkfinder', 'secretfinder', 'jsluice', 'trufflehog'],
            'options': {
                '--env': 'Environment affects max workers and timeouts'
            }
        },
        'fuzzingjs': {
            'description': 'Performs directory and file fuzzing with configurable patterns.',
            'output': 'fuzzing_all_urls.txt, fuzzing_new_urls.txt',
            'configurable': 'Patterns in config/enumeration (prefixes, suffixes, separators)',
            'options': {
                '--fuzz-mode': 'Fuzzing mode (wordlist, permutation, both, off)',
                '--fuzz-wordlist': 'Custom wordlist for fuzzing (required for wordlist/both)',
                '--fuzz-js-only': 'Only fuzz paths from JavaScript files (default: true).',
                '--fuzz-all-paths': 'Fuzz paths from all discovered URLs (overrides --fuzz-js-only).',
                '--fuzz-max-paths': 'Maximum number of paths to fuzz (default: 50).',
                '--fuzz-rank-paths': 'Rank paths by JS file count (default: true).',
                '--no-fuzz-rank-paths': 'Disable path ranking (simple selection).',
                '--fuzz-min-js-files': 'Minimum JS files required per path (default: 1).',
                '--env': 'Environment affects threads and timeouts'
            }
        },
        'param-passive': {
            'description': 'Extracts parameters and important file types from discovered URLs.',
            'output': 'param_passive/important_file_urls.txt, parameters.txt',
            'configurable': 'Important extensions in config/param_passive.important_extensions',
            'options': {
                '--env': 'Environment affects processing timeouts'
            }
        },
        'fallparams': {
            'description': 'Performs dynamic parameter discovery on key URLs.',
            'output': 'fallparams_results/',
            'options': {
                '--env': 'Environment affects processing timeouts'
            }
        },
        'sqli': {
            'description': 'Performs SQL injection reconnaissance with configurable detection patterns.',
            'output': 'sqli_results/',
            'tools': ['sqlmap', 'ghauri', 'gf'],
            'configurable': 'Patterns in config/sqli (vulnerable_extensions, vulnerable_files, sql_indicators)',
            'options': {
                '--sqli-scanner': 'Scanner to use (sqlmap, ghauri)',
                '--sqli-full-scan': 'Run full automated scan',
                '--sqli-manual-blind': 'Run manual blind tests',
                '--sqli-header-test': 'Run header-based tests',
                '--sqli-xor-test': 'Run XOR-based tests',
                '--env': 'Environment affects timeouts and scanning depth'
            }
        },
        'github': {
            'description': 'Scans GitHub for repositories, secrets, and useful data.',
            'output': 'github_results/',
            'tools': ['trufflehog', 'gitleaks', 'gitrob'],
            'options': {
                '--env': 'Environment affects scanning depth and timeouts'
            }
        },
        'gitlab': {
            'description': 'Scans GitLab for repositories, secrets, and useful data.',
            'output': 'gitlab_results/',
            'options': {
                '--env': 'Environment affects scanning depth and timeouts'
            }
        },
        'bitbucket': {
            'description': 'Scans Bitbucket for repositories, secrets, and useful data.',
            'output': 'bitbucket_results/',
            'options': {
                '--env': 'Environment affects scanning depth and timeouts'
            }
        },
        'gitea': {
            'description': 'Scans Gitea for repositories, secrets, and useful data.',
            'output': 'gitea_results/',
            'options': {
                '--env': 'Environment affects scanning depth and timeouts'
            }
        },
        'reporting': {
            'description': 'Generates comprehensive reports from all module results.',
            'output': 'reports/',
            'options': {
                '--env': 'Environment affects report generation options'
            }
        }
    }

    if command not in command_help:
        console.print(f"[red]Unknown command: {command}[/red]")
        return

    help_info = command_help[command]
    
    console.print(Panel(f"[bold green]{command.upper()}[/bold green] - {help_info['description']}", expand=False))
    
    if 'tools' in help_info:
        tools_str = ', '.join(help_info['tools'])
        console.print(f"[bold]Tools:[/bold] {tools_str}")
    
    console.print(f"[bold]Output:[/bold] {help_info['output']}")
    
    if 'configurable' in help_info:
        console.print(f"[bold]Configurable:[/bold] {help_info['configurable']}")
    
    if 'options' in help_info:
        opt_table = Table(title="[bold]Command Options[/bold]", box=box.SIMPLE)
        opt_table.add_column("Option", style="cyan", no_wrap=True)
        opt_table.add_column("Description")
        for opt, desc in help_info['options'].items():
            opt_table.add_row(opt, desc)
        console.print(opt_table)
