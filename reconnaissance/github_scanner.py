import json
import subprocess
import os
import shutil
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import quote
from datetime import datetime
import time

from common.logger import Logger
from common.utils import ensure_dir

class GitHubRecon:
    """A class to handle all GitHub reconnaissance operations for a target."""

    def __init__(self, target: str, output_dir: Path, logger: Logger, config: Dict):
        self.target = target
        self.output_dir = output_dir / "github"
        ensure_dir(self.output_dir)
        self.logger = logger
        self.config = config
        self.api_base = "https://api.github.com"
        self.token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'MJSRecon/1.0'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        
        self.temp_clone_dir = self.output_dir / "temp_clones"
        ensure_dir(self.temp_clone_dir)

    def _make_request(self, url: str) -> Optional[Dict | List]:
        """Makes a rate-limit-aware request to the GitHub API."""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                remaining = int(response.headers['X-RateLimit-Remaining'])
                if remaining == 0:
                    reset_time = datetime.fromtimestamp(int(response.headers['X-RateLimit-Reset']))
                    wait_seconds = (reset_time - datetime.now()).total_seconds() + 1
                    if wait_seconds > 0:
                        self.logger.warning(f"GitHub rate limit hit. Waiting for {int(wait_seconds)} seconds...")
                        time.sleep(wait_seconds)
                        return self._make_request(url)
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GitHub API request failed for {url}: {e}")
            return None

    def search_repositories(self) -> List[Dict]:
        """Searches GitHub for repositories related to the target."""
        self.logger.info(f"[{self.target}] Searching for repositories...")
        query = quote(f'"{self.target}" in:name,description,readme')
        url = f"{self.api_base}/search/repositories?q={query}&sort=stars&order=desc&per_page=50"
        
        results = self._make_request(url)
        if results and 'items' in results:
            self.logger.success(f"[{self.target}] Found {len(results['items'])} potential repositories.")
            return results['items']
        return []

    def clone_and_scan_repo(self, repo_info: Dict) -> Dict:
        """Clones a single repository and scans it for secrets."""
        repo_name = repo_info.get('full_name')
        clone_url = repo_info.get('clone_url')
        if not repo_name or not clone_url:
            return {}

        repo_clone_path = self.temp_clone_dir / repo_name.replace('/', '_')
        scan_results = {'repo_name': repo_name, 'secrets': []}

        try:
            # Shallow clone for efficiency
            cmd = ['git', 'clone', '--depth', '1', clone_url, str(repo_clone_path)]
            subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)

            if repo_clone_path.exists():
                self.logger.info(f"[{self.target}] Scanning {repo_name}...")
                
                # Scan with trufflehog
                trufflehog_cmd = ["trufflehog", "filesystem", str(repo_clone_path), "--json"]
                result = subprocess.run(trufflehog_cmd, capture_output=True, text=True, timeout=300, check=False)
                
                if result.stdout:
                    try:
                        for line in result.stdout.strip().split('\n'):
                            if line:
                                secret_data = json.loads(line)
                                scan_results['secrets'].append({
                                    'tool': 'trufflehog',
                                    'file': secret_data.get('Path', 'N/A'),
                                    'rule': secret_data.get('DetectorName', 'N/A'),
                                    'raw': secret_data.get('Raw', 'N/A')
                                })
                    except json.JSONDecodeError:
                         self.logger.warning(f"Could not parse trufflehog output for {repo_name}")
        
        finally:
            if repo_clone_path.exists():
                shutil.rmtree(repo_clone_path, ignore_errors=True)
        
        return scan_results

    def run_recon(self) -> Dict:
        """Main execution method for GitHub reconnaissance."""
        repositories = self.search_repositories()
        
        all_secrets = []
        # Limit to top 10 repos by stars to avoid excessive scanning
        top_repos = sorted(repositories, key=lambda r: r.get('stargazers_count', 0), reverse=True)[:10]

        for repo in top_repos:
            results = self.clone_and_scan_repo(repo)
            if results and results.get('secrets'):
                all_secrets.extend(results['secrets'])
        
        results_file = self.output_dir / f"{self.target}_github_secrets.json"
        with results_file.open('w') as f:
            json.dump(all_secrets, f, indent=2)
            
        self.logger.success(f"[{self.target}] GitHub scan complete. Found {len(all_secrets)} secrets.")
        
        return {
            "repos_found": len(repositories),
            "repos_scanned": len(top_repos),
            "secrets_found": len(all_secrets)
        }

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """Entry point for the reconnaissance module."""
    target = workflow_data['target']
    output_dir = workflow_data['target_output_dir']
    
    if not shutil.which('git') or not shutil.which('trufflehog'):
        logger.warning("`git` and/or `trufflehog` not found in PATH. Skipping GitHub reconnaissance.")
        return {"github_summary": {"status": "skipped"}}
        
    recon = GitHubRecon(target, output_dir, logger, config)
    summary = recon.run_recon()
    
    return {"github_summary": summary}
