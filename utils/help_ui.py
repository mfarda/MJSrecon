#!/usr/bin/env python3
"""
Beautiful Help UI for MJSRecon
Provides a rich, colorful help interface instead of default argparse help
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Try to import rich for beautiful formatting
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    from rich.syntax import Syntax
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Fallback colors for when rich is not available
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_banner():
    """Print the MJSRecon banner"""
    banner = """
███╗   ███╗     ██╗███████╗    ██████╗ ███████╗ ██████╗██╗  ██╗███╗   ██╗
████╗ ████║     ██║██╔════╝    ██╔══██╗██╔════╝██╔════╝██║ ██╔╝████╗  ██║
██╔████╔██║     ██║███████╗    ██████╔╝█████╗  ██║     █████╔╝ ██╔██╗ ██║
██║╚██╔╝██║██   ██║╚════██║    ██╔══██╗██╔══╝  ██║     ██╔═██╗ ██║╚██╗██║
██║ ╚═╝ ██║╚█████╔╝███████║    ██║  ██║███████╗╚██████╗██║  ██╗██║ ╚████║
╚═╝     ╚═╝ ╚════╝ ╚══════╝    ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝
    """
    
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel.fit(
            Text(banner, style="bold cyan"),
            title="[bold yellow]MJSRecon[/bold yellow]",
            subtitle="[italic]Modular JavaScript Reconnaissance Tool[/italic]",
            border_style="cyan"
        ))
    else:
        print(f"{Colors.CYAN}{Colors.BOLD}{banner}{Colors.END}")
        print(f"{Colors.YELLOW}{Colors.BOLD}MJSRecon - Modular JavaScript Reconnaissance Tool{Colors.END}\n")


def print_usage():
    """Print usage information"""
    usage_text = """
[bold cyan]USAGE:[/bold cyan]
    python -m mjsrecon [COMMANDS] [OPTIONS]

[bold cyan]EXAMPLES:[/bold cyan]
    python -m mjsrecon gather -t example.com -o ./output
    python -m mjsrecon passive-data fallparam -t example.com -o ./output
    python -m mjsrecon gather verify analyze -t example.com -o ./output
    """
    
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel(usage_text, title="[bold green]Usage[/bold green]", border_style="green"))
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}USAGE:{Colors.END}")
        print("    python -m mjsrecon [COMMANDS] [OPTIONS]\n")
        print(f"{Colors.GREEN}{Colors.BOLD}EXAMPLES:{Colors.END}")
        print("    python -m mjsrecon gather -t example.com -o ./output")
        print("    python -m mjsrecon passive-data fallparam -t example.com -o ./output")
        print("    python -m mjsrecon gather verify analyze -t example.com -o ./output\n")


def print_commands():
    """Print available commands with descriptions"""
    commands = {
        'gather': 'Collect URLs using waybackurls, gau, and katana',
        'verify': 'Verify collected URLs are live',
        'deduplicate': 'Remove duplicate URLs from collected data',
        'download': 'Download JavaScript files from verified URLs',
        'analyze': 'Analyze downloaded JS files for secrets and endpoints',
        'fuzz': 'Fuzz discovered endpoints for new URLs',
        'report': 'Generate comprehensive reconnaissance report',
        'github': 'Perform GitHub reconnaissance for secrets',
        'passive-data': 'Extract important files and parameters from gathered data',
        'fallparam': 'Discover dynamic parameters using fallparams'
    }
    
    if RICH_AVAILABLE:
        console = Console()
        table = Table(title="[bold yellow]Available Commands[/bold yellow]", box=box.ROUNDED)
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        
        for cmd, desc in commands.items():
            table.add_row(f"[bold]{cmd}[/bold]", desc)
        
        console.print(table)
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}Available Commands:{Colors.END}")
        for cmd, desc in commands.items():
            print(f"  {Colors.CYAN}{Colors.BOLD}{cmd:<15}{Colors.END} {desc}")


def print_options():
    """Print command line options"""
    options = {
        'Basic Options': [
            ('-t, --targets', 'Target domains (comma-separated)'),
            ('-o, --output', 'Output directory (default: ./output)'),
            ('-d, --depth', 'Katana crawl depth (default: 5)'),
            ('--input', 'Input file for independent mode'),
            ('--independent', 'Run modules independently with custom input')
        ],
        'Logging Options': [
            ('-v, --verbose', 'Enable verbose logging (debug level)'),
            ('-q, --quiet', 'Suppress info messages (warning level only)')
        ],
        'Fuzzing Options': [
            ('--fuzz-mode', 'Fuzzing mode: wordlist/permutation/both/off'),
            ('--fuzz-wordlist', 'Custom wordlist file for fuzzing'),
            ('--fuzz-extensions', 'File extensions to fuzz (default: js)'),
            ('--fuzz-status-codes', 'HTTP status codes to consider valid'),
            ('--fuzz-threads', 'Number of concurrent fuzzing threads'),
            ('--fuzz-timeout', 'Timeout for each fuzzing request')
        ],
        'Gather Options': [
            ('--gather-mode', 'Gather mode: g/w/k/gw/gk/wk/gwk (default: gwk)')
        ],
        'GitHub Options': [
            ('--github-token', 'GitHub API token for higher rate limits'),
            ('--github-max-repos', 'Maximum repositories to analyze per target'),
            ('--github-scan-tools', 'Secret scanning tools: trufflehog/gitleaks/custom/all'),
            ('--github-skip-clone', 'Skip cloning repositories (only use API data)')
        ]
    }
    
    if RICH_AVAILABLE:
        console = Console()
        for section, opts in options.items():
            table = Table(title=f"[bold blue]{section}[/bold blue]", box=box.SIMPLE)
            table.add_column("Option", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            
            for opt, desc in opts:
                table.add_row(opt, desc)
            
            console.print(table)
            console.print()  # Add spacing between sections
    else:
        for section, opts in options.items():
            print(f"{Colors.BLUE}{Colors.BOLD}{section}:{Colors.END}")
            for opt, desc in opts:
                print(f"  {Colors.CYAN}{opt:<25}{Colors.END} {desc}")
            print()


def print_workflows():
    """Print common workflow examples"""
    workflows = {
        'Basic Reconnaissance': 'gather verify deduplicate download analyze report',
        'Quick Scan': 'gather verify analyze',
        'Parameter Discovery': 'passive-data fallparam',
        'Full Reconnaissance': 'gather verify deduplicate download analyze fuzz report',
        'GitHub Reconnaissance': 'github',
        'Complete Workflow': 'gather verify deduplicate download analyze fuzz passive-data fallparam report'
    }
    
    if RICH_AVAILABLE:
        console = Console()
        table = Table(title="[bold magenta]Common Workflows[/bold magenta]", box=box.ROUNDED)
        table.add_column("Workflow", style="magenta", no_wrap=True)
        table.add_column("Commands", style="white")
        
        for workflow, commands in workflows.items():
            table.add_row(workflow, f"python -m mjsrecon {commands} -t example.com -o ./output")
        
        console.print(table)
    else:
        print(f"{Colors.RED}{Colors.BOLD}Common Workflows:{Colors.END}")
        for workflow, commands in workflows.items():
            print(f"  {Colors.RED}{Colors.BOLD}{workflow}:{Colors.END}")
            print(f"    python -m mjsrecon {commands} -t example.com -o ./output")
        print()


def print_tools():
    """Print required and optional tools"""
    tools = {
        'Required Tools': [
            'waybackurls', 'gau', 'katana', 'httpx', 'unfurl', 'fallparams'
        ],
        'Optional Tools': [
            'jsluice', 'python3', 'trufflehog', 'gitleaks'
        ]
    }
    
    if RICH_AVAILABLE:
        console = Console()
        for category, tool_list in tools.items():
            table = Table(title=f"[bold green]{category}[/bold green]", box=box.SIMPLE)
            table.add_column("Tool", style="green")
            
            for tool in tool_list:
                table.add_row(tool)
            
            console.print(table)
            console.print()
    else:
        for category, tool_list in tools.items():
            print(f"{Colors.GREEN}{Colors.BOLD}{category}:{Colors.END}")
            for tool in tool_list:
                print(f"  {Colors.GREEN}• {tool}{Colors.END}")
            print()


def print_footer():
    """Print footer information"""
    footer = """
[bold yellow]For more information:[/bold yellow]
    • GitHub: https://github.com/your-repo/mjsrecon
    • Documentation: https://mjsrecon.readthedocs.io
    • Issues: https://github.com/your-repo/mjsrecon/issues

[bold cyan]Happy Reconnaissance! 🕵️‍♂️[/bold cyan]
    """
    
    if RICH_AVAILABLE:
        console = Console()
        console.print(Panel(footer, border_style="yellow"))
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}For more information:{Colors.END}")
        print("    • GitHub: https://github.com/your-repo/mjsrecon")
        print("    • Documentation: https://mjsrecon.readthedocs.io")
        print("    • Issues: https://github.com/your-repo/mjsrecon/issues")
        print(f"\n{Colors.CYAN}{Colors.BOLD}Happy Reconnaissance! 🕵️‍♂️{Colors.END}")


def show_help():
    """Display the complete help interface"""
    print_banner()
    print_usage()
    print_commands()
    print_options()
    print_workflows()
    print_tools()
    print_footer()


def show_command_help(command: str):
    """Show help for a specific command"""
    print_banner()
    
    command_helps = {
        'gather': """
[bold cyan]GATHER MODULE[/bold cyan]
Collects URLs from various sources using waybackurls, gau, and katana.

[bold yellow]Usage:[/bold yellow]
    python -m mjsrecon gather -t example.com -o ./output

[bold yellow]Options:[/bold yellow]
    --gather-mode    Choose tools: g/w/k/gw/gk/wk/gwk (default: gwk)
    -d, --depth      Katana crawl depth (default: 5)

[bold yellow]Output:[/bold yellow]
    • js_urls_wayback_raw.txt
    • js_urls_gau_raw.txt  
    • js_urls_katana.txt
    • all_js_urls.txt
        """,
        
        'passive-data': """
[bold cyan]PASSIVE DATA MODULE[/bold cyan]
Extracts important files and parameters from gathered data using unfurl.

[bold yellow]Usage:[/bold yellow]
    python -m mjsrecon passive-data -t example.com -o ./output

[bold yellow]Workflow:[/bold yellow]
    1. Runs gather module
    2. Merges and deduplicates raw files
    3. Uses unfurl to extract parameters
    4. Finds URLs with important extensions (.php, .asp, .aspx, etc.)
    5. Verifies important URLs

[bold yellow]Output:[/bold yellow]
    • merged_raw_urls.txt
    • important_file_urls.txt
    • live_important_urls.txt
    • parameters/all_parameters.txt
        """,
        
        'fallparam': """
[bold cyan]FALLPARAM MODULE[/bold cyan]
Discovers dynamic parameters using fallparams tool.

[bold yellow]Usage:[/bold yellow]
    python -m mjsrecon fallparam -t example.com -o ./output

[bold yellow]Requirements:[/bold yellow]
    • Requires passive-data output (live_important_urls.txt)
    • fallparams tool must be installed

[bold yellow]Features:[/bold yellow]
    • Automatic parameter discovery (no wordlist needed)
    • Headless browser crawling
    • Configurable crawl depth

[bold yellow]Output:[/bold yellow]
    • fallparams_results/detailed_parameter_results.json
    • fallparams_results/parameter_summary.txt
        """
    }
    
    if command in command_helps:
        if RICH_AVAILABLE:
            console = Console()
            console.print(Panel(command_helps[command], title=f"[bold cyan]{command.upper()} HELP[/bold cyan]", border_style="cyan"))
        else:
            print(command_helps[command])
    else:
        print(f"Help not available for command: {command}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show_command_help(sys.argv[1])
    else:
        show_help() 