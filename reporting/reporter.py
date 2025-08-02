import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from common.logger import Logger
from common.utils import ensure_dir
from common.config import CONFIG

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """
    Generates a final summary report from the in-memory workflow data.
    """
    target = workflow_data['target']
    output_dir = workflow_data['target_output_dir']
        ensure_dir(output_dir)

    logger.info(f"[{target}] Generating final report...")

    report_content = generate_report_text(target, workflow_data, config)

    report_file_txt = output_dir / f"{target}_recon_report.txt"
    report_file_txt.write_text(report_content)

    report_file_json = output_dir / f"{target}_recon_report.json"
    with report_file_json.open('w') as f:
        def json_serializer(obj):
            if isinstance(obj, set):
                return sorted(list(obj))
            if isinstance(obj, Path):
                return str(obj)
            return str(obj)
        json.dump(workflow_data, f, indent=2, default=json_serializer)

    logger.success(f"[{target}] Comprehensive report saved to {report_file_txt} and {report_file_json}")
    print(f"\nReport for {target} is ready. You can view the summary at: {report_file_txt}")

    return {}

def generate_report_text(target: str, data: Dict, config: Dict) -> str:
    """Constructs the human-readable text report."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = [
        "╔" + "═" * 78 + "╗",
        f"║ {'MJSRecon Summary Report':^78} ║",
        f"║ {'Target: ' + target:<78} ║",
        f"║ {'Generated: ' + timestamp:<78} ║",
        "╚" + "═" * 78 + "╝",
        "\n"
    ]
    
    report.append("--- Reconnaissance Funnel ---\n")
    urls_total = len(data.get('all_urls', set()))
    urls_live = len(data.get('live_urls', set()))
    urls_dedup = len(data.get('deduplicated_urls', []))
    files_downloaded = len(data.get('downloaded_files', []))
    
    report.append(f"  • URLs Discovered  : {urls_total}")
    report.append(f"  • Live URLs        : {urls_live}")
    report.append(f"  • Unique Files     : {urls_dedup}")
    report.append(f"  • Files Downloaded : {files_downloaded}\n")
    
    if 'fuzzing_summary' in data and data['fuzzing_summary'].get('status') != 'skipped':
        summary = data['fuzzing_summary']
        report.append("--- Fuzzing Summary ---\n")
        report.append(f"  • Total URLs Found : {summary.get('total_found', 'N/A')}")
        report.append(f"  • New URLs Found   : {summary.get('new_found', 'N/A')}\n")

    if 'param_passive_summary' in data:
        summary = data['param_passive_summary']
        report.append("--- Parameter Extraction Summary ---\n")
        report.append(f"  • Important files found: {summary.get('important_files', 0)}\n")
        report.append(f"  • Unique parameters found: {summary.get('unique_parameters', 0)}\n\n")

    if 'fallparams_summary' in data:
        summary = data['fallparams_summary']
        report.append("--- Dynamic Parameter Summary ---\n")
        report.append(f"  • URLs with new params found: {summary.get('urls_with_params', 'N/A')}\n")

    if 'github_summary' in data and data['github_summary'].get('status') != 'skipped':
        summary = data['github_summary']
        report.append("--- GitHub Recon Summary ---\n")
        report.append(f"  • Repositories Found : {summary.get('repos_found', 'N/A')}")
        report.append(f"  • Repositories Scanned: {summary.get('repos_scanned', 'N/A')}")
        report.append(f"  • Secrets Found      : {summary.get('secrets_found', 'N/A')}\n")

    report.append("--- Key Output Files ---\n")
    output_dir = data['target_output_dir']
    report.append(f"  • Live JS URLs      : {output_dir / config['files']['live_js']}")
    report.append(f"  • Analysis Results  : {output_dir / config['dirs']['results']}")
    if 'fuzzing_summary' in data and data['fuzzing_summary'].get('status') != 'skipped':
        report.append(f"  • New Fuzzed URLs   : {output_dir / config['files']['fuzzing_new']}")
    if 'github_summary' in data and data['github_summary'].get('status') != 'skipped':
        report.append(f"  • GitHub Secrets    : {output_dir / 'github' / f'{target}_github_secrets.json'}")
    report.append(f"  • Full JSON Report  : {output_dir / f'{target}_recon_report.json'}\n")

    return "\n".join(report)
