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

def show_help():
    """Displays the main help message for the tool."""
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
        '--command-timeout': 'Override command timeout in seconds (default: from config).'
    }
    for opt, desc in core_options.items():
        core_table.add_row(opt, desc)
    console.print(core_table)

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
        '--fuzz-wordlist': 'Custom wordlist for fuzzing.'
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

    # Configuration Info
    config_panel = Panel("""
[bold]Configuration System:[/bold]
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

    # Customization Info
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
    
    console.print(config_panel)
    console.print(customization_panel)

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
            'output': 'validated_urls.txt',
            'options': {
                '--proxy': 'Use proxy for validation requests',
                '--timeout': 'Request timeout in seconds'
            }
        },
        'processing': {
            'description': 'Deduplicates URLs based on content hash to remove duplicates.',
            'output': 'unique_urls.txt',
            'options': {
                '--proxy': 'Use proxy for content downloads',
                '--hash-algorithm': 'Hash algorithm to use (default: md5)'
            }
        },
        'download': {
            'description': 'Downloads JavaScript files asynchronously with multi-extension support.',
            'output': 'downloaded_files/ (with extension subdirectories)',
            'configurable': 'File extensions in config/download.allowed_extensions',
            'options': {
                '--proxy': 'Use proxy for downloads',
                '--concurrent': 'Number of concurrent downloads'
            }
        },
        'analysis': {
            'description': 'Analyzes downloaded JavaScript files for secrets and endpoints.',
            'output': 'analysis_results.json',
            'tools': ['linkfinder', 'secretfinder', 'custom patterns'],
            'options': {
                '--patterns': 'Custom regex patterns file',
                '--output-format': 'Output format (json, txt)'
            }
        },
        'fuzzingjs': {
            'description': 'Performs directory and file fuzzing with configurable patterns.',
            'output': 'fuzzed_urls.txt',
            'configurable': 'Patterns in config/enumeration (prefixes, suffixes, separators)',
            'options': {
                '--fuzz-mode': 'Fuzzing mode (wordlist, permutation, both, off)',
                '--fuzz-wordlist': 'Custom wordlist for fuzzing'
            }
        },
        'param-passive': {
            'description': 'Extracts parameters and important file types from discovered URLs.',
            'output': 'parameters.txt',
            'configurable': 'Important extensions in config/param_passive.important_extensions',
            'options': {
                '--extensions': 'File extensions to extract parameters from'
            }
        },
        'fallparams': {
            'description': 'Performs dynamic parameter discovery on key URLs.',
            'output': 'dynamic_parameters.txt',
            'options': {
                '--wordlist': 'Parameter wordlist to use'
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
                '--sqli-manual-blind': 'Run manual blind tests'
            }
        },
        'github': {
            'description': 'Scans GitHub for repositories, secrets, and useful data.',
            'output': 'github_results/',
            'tools': ['trufflehog', 'gitleaks', 'gitrob'],
            'options': {
                '--api-token': 'GitHub API token',
                '--org-scan': 'Scan organization repositories'
            }
        },
        'gitlab': {
            'description': 'Scans GitLab for repositories, secrets, and useful data.',
            'output': 'gitlab_results/',
            'options': {
                '--api-token': 'GitLab API token',
                '--instance': 'GitLab instance URL'
            }
        },
        'bitbucket': {
            'description': 'Scans Bitbucket for repositories, secrets, and useful data.',
            'output': 'bitbucket_results/',
            'options': {
                '--api-token': 'Bitbucket API token',
                '--workspace': 'Bitbucket workspace'
            }
        },
        'gitea': {
            'description': 'Scans Gitea for repositories, secrets, and useful data.',
            'output': 'gitea_results/',
            'options': {
                '--api-token': 'Gitea API token',
                '--instance': 'Gitea instance URL'
            }
        },
        'reporting': {
            'description': 'Generates comprehensive reports from all module results.',
            'output': 'reports/',
            'options': {
                '--format': 'Report format (html, json, txt)',
                '--template': 'Custom report template'
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
