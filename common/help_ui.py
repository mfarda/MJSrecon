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
        'enumeration': 'Fuzzes directories for more JS files.',
        'passive-data': 'Extracts parameters and important file types.',
        'fallparams': 'Performs dynamic parameter discovery on key URLs.',
        'reconnaissance': 'Scans GitHub for secrets related to the target.',
        'reporting': 'Generates a final summary report of all findings.',
    }
    for cmd, desc in commands.items():
        cmd_table.add_row(cmd, desc)
    console.print(cmd_table)

    # Options
    opt_table = Table(title="[bold blue]Options[/bold blue]", box=box.SIMPLE)
    opt_table.add_column("Option", style="cyan", no_wrap=True)
    opt_table.add_column("Description")
    options = {
        '-t, --target': 'A single target domain (e.g., example.com).',
        '--targets-file': 'A file with a list of target domains.',
        '-o, --output': 'Base output directory (default: ./output).',
        '-v, --verbose': 'Enable verbose (DEBUG level) logging.',
        '-q, --quiet': 'Suppress console output except for warnings/errors.',
        '--independent': 'Run a single command independently (requires --input).',
        '--input': 'Input file for a module in independent mode.',
        '--help-command <cmd>': 'Show detailed help for a specific command.',
        '-h, --help': 'Show this help message.'
    }
    for opt, desc in options.items():
        opt_table.add_row(opt, desc)
    console.print(opt_table)

    # Example Workflows
    example_panel = Panel("""
[bold]Full Recon:[/bold]
discovery validation processing download analysis enumeration reporting -t example.com

[bold]Quick Scan (No Fuzzing):[/bold]
discovery validation download analysis -t example.com

[bold]Parameter Discovery:[/bold]
discovery validation passive-data fallparams -t example.com
    """, title="[bold magenta]Example Workflows[/bold magenta]", border_style="magenta")
    console.print(example_panel)

def show_command_help(command: str):
    # This can be expanded with detailed help for each command
    console = Console()
    console.print(f"[bold cyan]Help for '{command}':[/bold cyan]")
    console.print("This feature is under development. Please refer to the main help for now.")
