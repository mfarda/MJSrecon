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
    usage.add_row("[bold cyan]Usage:", "python -m MJSrecon <commands> -t <target> [options]")
    console.print(usage)

    # Commands
    cmd_table = Table(title="[bold yellow]Workflow Commands[/bold yellow]", box=box.ROUNDED)
    cmd_table.add_column("Command", style="cyan", no_wrap=True)
    cmd_table.add_column("Description")
    commands = {
        'discovery': 'Gathers JS URLs from various sources (gau, wayback, katana).',
        'validation': 'Verifies that discovered URLs are live and accessible.',
        'processing': 'Deduplicates live URLs based on content hash.',
        'download': 'Downloads unique JS files.',
        'analysis': 'Analyzes downloaded files for secrets and endpoints.',
        'fuzzingjs': 'Fuzzes directories for more JS files.',
        'param-passive': 'Extracts parameters and important file types.',
        'fallparams': 'Performs dynamic parameter discovery on key URLs.',
        'sqli': 'Performs SQL injection reconnaissance and testing on discovered URLs.',
        'github': 'Scans GitHub for repositories, secrets, and useful data.',
        'gitlab': 'Scans GitLab for repositories, secrets, and useful data.',
        'bitbucket': 'Scans Bitbucket for repositories, secrets, and useful data.',
        'gitea': 'Scans Gitea for repositories, secrets, and useful data.',
        'reporting': 'Generates comprehensive reports from all module results.'
    }
    for cmd, desc in commands.items():
        cmd_table.add_row(cmd, desc)
    console.print(cmd_table)

    # Options
    opt_table = Table(title="[bold blue]Options[/bold blue]", box=box.SIMPLE)
    opt_table.add_column("Option", style="cyan", no_wrap=True)
    opt_table.add_column("Description")
    options = {
        '-t, --target': 'Target domain or URL to scan.',
        '-o, --output': 'Base output directory (default: ./output).',
        '--targets-file': 'File with multiple targets.',
        '--uro': 'Use uro to deduplicate/shorten URLs after discovery and use its output for all subsequent modules.',
        '--gather-mode': 'Tools to use for discovery (g=gau, w=wayback, k=katana).',
        '-d, --depth': 'Katana crawl depth (default: 2).',
        '--fuzz-mode': 'Fuzzing mode (wordlist, permutation, both, off).',
        '--fuzz-wordlist': 'Custom wordlist for fuzzing.',
        '--sqli-scanner': 'SQLi scanner to use (sqlmap or ghauri).',
        '--sqli-full-scan': 'Run full SQLi scan including automated scanning.',
        '--sqli-manual-blind': 'Run manual blind SQLi test (time-based) - DEFAULT MODE.',
        '--sqli-header-test': 'Run header-based blind SQLi test.',
        '--sqli-xor-test': 'Run XOR blind SQLi test.',
        '-v, --verbose': 'Enable verbose (DEBUG level) logging.',
        '-q, --quiet': 'Suppress console output except for warnings/errors.',
        '--independent': 'Run a single module independently.',
        '--input': 'Input file for independent mode.'
    }
    for opt, desc in options.items():
        opt_table.add_row(opt, desc)
    console.print(opt_table)

    # Example Workflows
    example_panel = Panel("""
[bold]Full Recon:[/bold]
discovery validation processing download analysis fuzzingjs reporting -t example.com

[bold]Quick Scan (No Fuzzing):[/bold]
discovery validation download analysis -t example.com

[bold]Parameter Discovery:[/bold]
discovery validation param-passive fallparams -t example.com

[bold]Code Hosting Reconnaissance:[/bold]
github gitlab bitbucket gitea -t example.com

[bold]With URL Deduplication (uro):[/bold]
discovery validation processing download analysis --uro -t example.com

[bold]Custom Discovery Tools:[/bold]
discovery validation --gather-mode gw -d 3 -t example.com

[bold]Fuzzing with Custom Wordlist:[/bold]
discovery validation fuzzingjs --fuzz-mode wordlist --fuzz-wordlist ./custom.txt -t example.com

[bold]SQL Injection Reconnaissance:[/bold]
discovery validation sqli --sqli-full-scan --sqli-scanner sqlmap -t example.com

[bold]SQLi with Manual Testing:[/bold]
discovery validation sqli --sqli-manual-blind --sqli-header-test --sqli-xor-test -t example.com

[bold]SQLi with Google Dorking:[/bold]
discovery validation sqli --sqli-dorking --sqli-full-scan -t example.com

[bold]Complete Workflow with uro:[/bold]
discovery validation processing download analysis fuzzingjs sqli --uro --sqli-full-scan -t example.com

[bold]With HTTP Proxy:[/bold]
discovery validation processing -t example.com --proxy http://proxy:8080 --proxy-auth user:pass

[bold]With SOCKS5 Proxy (WARP):[/bold]
discovery validation processing -t example.com --proxy socks5://127.0.0.1:1080

[bold]With SOCKS5 Proxy and Auth:[/bold]
discovery validation processing -t example.com --proxy socks5://user:pass@proxy:1080

[bold]Bypass Proxy for Local Hosts:[/bold]
discovery validation processing -t example.com --proxy socks5://127.0.0.1:1080 --no-proxy localhost,127.0.0.1
    """, title="[bold magenta]Example Workflows[/bold magenta]", border_style="magenta")
    console.print(example_panel)

def show_command_help(command: str):
    # This can be expanded with detailed help for each command
    console = Console()
    console.print(f"[bold cyan]Help for '{command}':[/bold cyan]")
    console.print("This feature is under development. Please refer to the main help for now.")
