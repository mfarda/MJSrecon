#!/usr/bin/env python3
"""
Gitea Module for MJSRecon
Scans Gitea for secrets related to the target
"""

import os
import json
import time
import subprocess
import tempfile
import shutil
import hashlib
import pickle
from pathlib import Path
from urllib.parse import urlparse, quote
from typing import List, Dict, Set, Optional, Tuple, Any
import re
from datetime import datetime, timedelta
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64

from common.logger import Logger
from common.utils import ensure_dir

class GiteaRecon:
    def __init__(self, target: str, output_dir: Path, logger: Logger, config: Dict):
        self.target = target
        self.output_dir = output_dir / "gitea"
        ensure_dir(self.output_dir)
        
        # Add cache directory initialization
        self.cache_dir = self.output_dir / "cache"
        ensure_dir(self.cache_dir)
        
        self.logger = logger
        self.config = config
        
        # Gitea API configuration
        gitea_config = config.get('gitea_scanner', {})
        self.gitea_token = os.getenv(gitea_config.get('api_token_env', 'GITEA_TOKEN'))
        self.gitea_url = os.getenv(gitea_config.get('gitea_url_env', 'GITEA_URL'), 'https://gitea.com')
        self.gitea_api_base = f"{self.gitea_url}/api/v1"
        
        # Rate limiting
        self.rate_limit_remaining = 1000
        self.rate_limit_reset = 0
        self.rate_limit_wait = gitea_config.get('rate_limit_wait', 60)
        
        # Results storage
        self.repositories = []
        self.secrets_found = []
        self.useful_data = []
        self.organizations = []
        self.users = []
        
        # Tools configuration from config
        enabled_tools = gitea_config.get('enabled_tools', {})
        
        self.tools = {}
        for tool_name, enabled in enabled_tools.items():
            if enabled:
                self.tools[tool_name] = True
        
        # Search configuration
        self.max_repos_to_scan = gitea_config.get('max_repos_to_scan', 4)
        self.max_file_size_mb = gitea_config.get('max_file_size_mb', 10)
        self.search_per_page = gitea_config.get('search_per_page', 100)
        self.max_search_results = gitea_config.get('max_search_results', 1000)
        
        # Search queries for Gitea
        self.search_queries = [
            f'"{target}"',
            f'org:{target}',
            f'user:{target}',
            f'{target}',
            f'"{target}" language:javascript',
            f'"{target}" language:python',
            f'"{target}" language:go',
            f'"{target}" language:java',
        ]

    def search_gitea(self, query: str, page: int = 1) -> Dict:
        """Search Gitea repositories"""
        if not self.gitea_token:
            self.logger.warning("No Gitea token provided. Skipping Gitea search.")
            return {}
        
        headers = {
            'Authorization': f'token {self.gitea_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'q': query,
            'page': page,
            'limit': self.search_per_page
        }
        
        try:
            response = requests.get(
                f"{self.gitea_api_base}/repos/search",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                self.logger.warning("Rate limited by Gitea API. Waiting...")
                time.sleep(self.rate_limit_wait)
                return {}
            else:
                self.logger.error(f"Gitea API error: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error searching Gitea: {e}")
            return {}

    def get_repository_details(self, owner: str, repo_name: str) -> Dict:
        """Get detailed information about a Gitea repository"""
        if not self.gitea_token:
            return {}
        
        headers = {
            'Authorization': f'token {self.gitea_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                f"{self.gitea_api_base}/repos/{owner}/{repo_name}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting repository details: {e}")
            return {}

    def clone_repository(self, repo_url: str, repo_name: str) -> Optional[Path]:
        """Clone a Gitea repository"""
        try:
            clone_dir = self.cache_dir / repo_name
            if clone_dir.exists():
                shutil.rmtree(clone_dir)
            
            # Clone with depth 1 for faster cloning
            cmd = ['git', 'clone', '--depth', '1', repo_url, str(clone_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.debug(f"Successfully cloned {repo_name}")
                return clone_dir
            else:
                self.logger.error(f"Failed to clone {repo_name}: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error cloning {repo_name}: {e}")
            return None

    def scan_repository(self, repo_path: Path, repo_name: str) -> List[Dict]:
        """Scan a repository for secrets"""
        secrets = []
        
        try:
            # Use configured tools for scanning
            if self.tools.get('trufflehog', False):
                truffle_secrets = self.run_trufflehog(repo_path, repo_name)
                secrets.extend(truffle_secrets)
            
            if self.tools.get('gitleaks', False):
                gitleaks_secrets = self.run_gitleaks(repo_path, repo_name)
                secrets.extend(gitleaks_secrets)
            
            if self.tools.get('custom_patterns', False):
                custom_secrets = self.run_custom_patterns(repo_path, repo_name)
                secrets.extend(custom_secrets)
            
        except Exception as e:
            self.logger.error(f"Error scanning {repo_name}: {e}")
        
        return secrets

    def run_trufflehog(self, repo_path: Path, repo_name: str) -> List[Dict]:
        """Run TruffleHog on repository"""
        secrets = []
        
        try:
            cmd = ['trufflehog', '--json', str(repo_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            data = json.loads(line)
                            secrets.append({
                                'tool': 'trufflehog',
                                'repository': repo_name,
                                'file': data.get('path', ''),
                                'line': data.get('line', ''),
                                'secret': data.get('raw', ''),
                                'type': data.get('detectorName', ''),
                                'confidence': 'high'
                            })
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            self.logger.error(f"Error running TruffleHog on {repo_name}: {e}")
        
        return secrets

    def run_gitleaks(self, repo_path: Path, repo_name: str) -> List[Dict]:
        """Run Gitleaks on repository"""
        secrets = []
        
        try:
            cmd = ['gitleaks', 'detect', '--source', str(repo_path), '--format', 'json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and result.stdout:
                try:
                    data = json.loads(result.stdout)
                    for finding in data:
                        secrets.append({
                            'tool': 'gitleaks',
                            'repository': repo_name,
                            'file': finding.get('File', ''),
                            'line': finding.get('Line', ''),
                            'secret': finding.get('Secret', ''),
                            'type': finding.get('RuleID', ''),
                            'confidence': 'high'
                        })
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error running Gitleaks on {repo_name}: {e}")
        
        return secrets

    def run_custom_patterns(self, repo_path: Path, repo_name: str) -> List[Dict]:
        """Run custom pattern matching"""
        secrets = []
        
        try:
            # Get custom patterns from config
            patterns = self.config.get('gitea_scanner', {}).get('secret_patterns', {})
            
            for pattern_name, pattern_list in patterns.items():
                for pattern in pattern_list:
                    # Search for patterns in files
                    cmd = ['grep', '-r', '-n', pattern, str(repo_path)]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.stdout:
                        for line in result.stdout.strip().split('\n'):
                            if line:
                                parts = line.split(':', 2)
                                if len(parts) >= 3:
                                    file_path, line_num, content = parts[0], parts[1], parts[2]
                                    secrets.append({
                                        'tool': 'custom_patterns',
                                        'repository': repo_name,
                                        'file': file_path,
                                        'line': line_num,
                                        'secret': content.strip(),
                                        'type': pattern_name,
                                        'confidence': 'medium'
                                    })
                                    
        except Exception as e:
            self.logger.error(f"Error running custom patterns on {repo_name}: {e}")
        
        return secrets

    def save_results(self):
        """Save all results to files"""
        # Save repositories
        if self.repositories:
            repos_file = self.output_dir / "repositories.json"
            with open(repos_file, 'w') as f:
                json.dump(self.repositories, f, indent=2)
            self.logger.info(f"Saved {len(self.repositories)} repositories to {repos_file}")
        
        # Save secrets
        if self.secrets_found:
            secrets_file = self.output_dir / "secrets.json"
            with open(secrets_file, 'w') as f:
                json.dump(self.secrets_found, f, indent=2)
            self.logger.info(f"Saved {len(self.secrets_found)} secrets to {secrets_file}")
        
        # Save useful data
        if self.useful_data:
            data_file = self.output_dir / "useful_data.json"
            with open(data_file, 'w') as f:
                json.dump(self.useful_data, f, indent=2)
            self.logger.info(f"Saved {len(self.useful_data)} useful data items to {data_file}")

    def run(self):
        """Main execution method"""
        self.logger.info(f"Starting Gitea reconnaissance for target: {self.target}")
        
        # Search for repositories
        all_repos = []
        
        for query in self.search_queries:
            self.logger.info(f"Searching Gitea with query: {query}")
            
            page = 1
            while page <= (self.max_search_results // self.search_per_page):
                results = self.search_gitea(query, page)
                
                if not results or 'data' not in results:
                    break
                
                for repo in results['data']:
                    owner = repo.get('owner', {}).get('username', '')
                    repo_name = repo.get('name', '')
                    
                    if owner and repo_name:
                        repo_details = self.get_repository_details(owner, repo_name)
                        if repo_details:
                            all_repos.append(repo_details)
                
                page += 1
                
                # Rate limiting
                time.sleep(1)
        
        # Remove duplicates
        unique_repos = []
        seen_keys = set()
        for repo in all_repos:
            repo_key = f"{repo.get('owner', {}).get('username', '')}/{repo.get('name', '')}"
            if repo_key and repo_key not in seen_keys:
                unique_repos.append(repo)
                seen_keys.add(repo_key)
        
        self.logger.info(f"Found {len(unique_repos)} unique Gitea repositories")
        
        # Limit the number of repositories to scan
        repos_to_scan = unique_repos[:self.max_repos_to_scan]
        
        # Scan repositories
        for repo in repos_to_scan:
            repo_name = repo.get('name', 'unknown')
            repo_url = repo.get('clone_url', '')
            
            if not repo_url:
                continue
            
            self.logger.info(f"Scanning repository: {repo_name}")
            
            # Clone repository
            repo_path = self.clone_repository(repo_url, repo_name)
            if not repo_path:
                continue
            
            # Scan for secrets
            secrets = self.scan_repository(repo_path, repo_name)
            self.secrets_found.extend(secrets)
            
            # Clean up
            shutil.rmtree(repo_path)
        
        # Save results
        self.save_results()
        
        self.logger.success(f"Gitea reconnaissance complete. Found {len(self.secrets_found)} secrets in {len(repos_to_scan)} repositories.")
        
        return {
            'repositories': self.repositories,
            'secrets_found': self.secrets_found,
            'useful_data': self.useful_data
        }

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """Main entry point for Gitea reconnaissance module"""
    target = workflow_data['target']
    target_output_dir = workflow_data['target_output_dir']
    
    gitea_recon = GiteaRecon(target, target_output_dir, logger, config)
    return gitea_recon.run() 