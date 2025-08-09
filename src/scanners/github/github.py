#!/usr/bin/env python3
"""
GitHub Module for MJSRecon
Scans GitHub for secrets related to the target
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

from src.common.logger import Logger
from src.common.utils import ensure_dir

class GitHubRecon:
    def __init__(self, target: str, output_dir: Path, logger: Logger, config: Dict):
        self.target = target
        self.output_dir = output_dir / "github"
        ensure_dir(self.output_dir)
        
        # Add cache directory initialization
        self.cache_dir = self.output_dir / "cache"
        ensure_dir(self.cache_dir)
        
        self.logger = logger
        self.config = config
        
        # GitHub API configuration
        github_config = config.get('github_scanner', {})
        self.github_token = os.getenv(github_config.get('api_token_env', 'GITHUB_TOKEN'))
        self.github_api_base = "https://api.github.com"
        self.github_search_base = "https://api.github.com/search"
        
        # Rate limiting
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
        self.rate_limit_wait = github_config.get('rate_limit_wait', 60)
        
        # Results storage
        self.repositories = []
        self.secrets_found = []
        self.useful_data = []
        self.organizations = []
        self.users = []
        
        # Tools configuration from config
        enabled_tools = github_config.get('enabled_tools', {})
        
        self.tools = {}
        for tool_name, enabled in enabled_tools.items():
            if enabled:
                if tool_name == 'trufflehog_github_org':
                    # This is a feature flag that depends on trufflehog being available
                    trufflehog_available = self._check_tool('trufflehog')
                    self.tools[tool_name] = trufflehog_available
                    self.logger.debug(f'[{self.target}] Tool {tool_name}: enabled={enabled}, available={trufflehog_available} (depends on trufflehog)')
                else:
                    tool_available = self._check_tool(tool_name)
                    self.tools[tool_name] = tool_available
                    self.logger.debug(f'[{self.target}] Tool {tool_name}: enabled={enabled}, available={tool_available}')
            else:
                self.tools[tool_name] = False
                self.logger.debug(f'[{self.target}] Tool {tool_name}: enabled={enabled}, available=False')
        
        # Scanning configuration from config
        self.max_repos_to_scan = github_config.get('max_repos_to_scan', 10)
        self.max_file_size_mb = github_config.get('max_file_size_mb', 10)
        self.clone_timeout = github_config.get('clone_timeout', 300)
        self.scan_timeout = github_config.get('scan_timeout', 600)
        
        # Search configuration from config
        self.search_per_page = github_config.get('search_per_page', 100)
        self.max_search_results = github_config.get('max_search_results', 1000)
        
        # Search queries from config
        self.search_queries = github_config.get('search_queries', [])
        
        # Output configuration from config
        self.save_repositories = github_config.get('save_repositories', True)
        self.save_secrets = github_config.get('save_secrets', True)
        self.save_useful_data = github_config.get('save_useful_data', True)
        self.save_organizations = github_config.get('save_organizations', True)
        self.save_users = github_config.get('save_users', True)
        self.generate_report = github_config.get('generate_report', True)
        
        # Secret patterns from config
        self.secret_patterns = github_config.get('secret_patterns', {})
        
        # Performance configuration from config
        self.max_concurrent_repos = github_config.get('max_concurrent_repos', 3)
        self.max_concurrent_scans = github_config.get('max_concurrent_scans', 4)
        self.cache_enabled = github_config.get('cache_enabled', True)
        self.cache_ttl = github_config.get('cache_ttl', 3600)

    def _check_tool(self, tool_name: str) -> bool:
        """Check if a tool is available in PATH"""
        try:
            subprocess.run([tool_name, '--version'], 
                         capture_output=True, check=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _get_cached_response(self, url: str) -> Optional[Dict]:
        """Get cached API response if available and not expired"""
        cache_file = self.cache_dir / f"{hashlib.md5(url.encode()).hexdigest()}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    # Check if cache is less than 1 hour old
                    if time.time() - cached_data['timestamp'] < 3600:
                        return cached_data['data']
            except Exception:
                pass
        return None
    
    def _cache_response(self, url: str, data: Dict):
        """Cache API response"""
        cache_file = self.cache_dir / f"{hashlib.md5(url.encode()).hexdigest()}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({'data': data, 'timestamp': time.time()}, f)
        except Exception:
            pass

    def _make_github_request(self, url: str, headers: Dict = None) -> Dict:
        """Make a GitHub API request with caching"""
        # Check cache first
        cached_data = self._get_cached_response(url)
        if cached_data:
            return cached_data
        
        if headers is None:
            headers = {}
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        headers['Accept'] = 'application/vnd.github.v3+json'
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                self.rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
                self.rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
                
                if self.rate_limit_remaining == 0:
                    reset_time = datetime.fromtimestamp(self.rate_limit_reset)
                    wait_time = (reset_time - datetime.now()).total_seconds()
                    if wait_time > 0:
                        self.logger.warning(f'Rate limit exceeded. Waiting {wait_time:.0f} seconds...')
                        time.sleep(wait_time)
                        return self._make_github_request(url, headers)
            
            response.raise_for_status()
            json_data = response.json()
            
            # Cache successful responses
            if response.status_code == 200:
                self._cache_response(url, json_data)
            
            return json_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f'GitHub API request failed: {e}')
            return {}

    def search_repositories(self) -> List[Dict]:
        """Search for repositories related to the target"""
        self.logger.info(f'[{self.target}] Searching for repositories...')
        self.logger.debug(f'[{self.target}] Search limits: {self.search_per_page} per page, max {self.max_search_results} total results')
        
        repositories = []
        
        for query_template in self.search_queries:
            try:
                # Replace {target} placeholder with actual target
                org_name = self.target.split('.')[0] if '.' in self.target else self.target
                
                query = query_template.replace('{target}', org_name)
                self.logger.debug(f'[{self.target}] Searching with query: {query}')
                
                # Build URL manually to avoid encoding colons and other special characters
                # that GitHub search API expects to remain unencoded
                base_url = f"{self.github_search_base}/repositories"
                params = {
                    'q': query,
                    'sort': 'updated',
                    'order': 'desc',
                    'per_page': str(self.search_per_page)
                }
                
                # Construct URL manually to avoid encoding issues
                param_strings = []
                for key, value in params.items():
                    if key == 'q':
                        # Don't encode the query parameter - GitHub expects it as-is
                        param_strings.append(f"{key}={value}")
                    else:
                        param_strings.append(f"{key}={quote(str(value))}")
                
                url = f"{base_url}?{'&'.join(param_strings)}"
                results = self._make_github_request(url)
                
                if 'items' in results:
                    for repo in results['items']:
                        repo_info = {
                            'name': repo['full_name'],
                            'description': repo.get('description', ''),
                            'url': repo['html_url'],
                            'clone_url': repo['clone_url'],
                            'ssh_url': repo['ssh_url'],
                            'language': repo.get('language', ''),
                            'stars': repo['stargazers_count'],
                            'forks': repo['forks_count'],
                            'updated_at': repo['updated_at'],
                            'created_at': repo['created_at'],
                            'size': repo['size'],
                            'default_branch': repo['default_branch'],
                            'topics': repo.get('topics', []),
                            'search_query': query
                        }
                        repositories.append(repo_info)
                        
                        # Check if we've reached the maximum search results limit
                        if len(repositories) >= self.max_search_results:
                            self.logger.info(f'[{self.target}] Reached maximum search results limit ({self.max_search_results})')
                            break
                        
                # Respect rate limits
                time.sleep(1)
                
                # Break if we've reached the limit
                if len(repositories) >= self.max_search_results:
                    break
                
            except Exception as e:
                self.logger.error(f'[{self.target}] Error searching repositories with query "{query}": {e}')
                continue
        
        # Remove duplicates
        seen = set()
        unique_repos = []
        for repo in repositories:
            if repo['name'] not in seen:
                seen.add(repo['name'])
                unique_repos.append(repo)
        
        self.logger.success(f'[{self.target}] Found {len(unique_repos)} unique repositories (from {len(repositories)} total results)')
        return unique_repos

    def get_organization_info(self, org_name: str) -> Dict:
        """Get detailed information about an organization"""
        self.logger.info(f'[{self.target}] Getting organization info for: {org_name}')
        
        url = f"{self.github_api_base}/orgs/{org_name}"
        org_info = self._make_github_request(url)
        
        if org_info:
            # Get organization repositories
            repos_url = f"{self.github_api_base}/orgs/{org_name}/repos?per_page=100"
            repos = self._make_github_request(repos_url)
            
            # Get organization members
            members_url = f"{self.github_api_base}/orgs/{org_name}/members?per_page=100"
            members = self._make_github_request(members_url)
            
            org_data = {
                'name': org_info.get('login', org_name),
                'description': org_info.get('description', ''),
                'url': org_info.get('html_url', ''),
                'avatar_url': org_info.get('avatar_url', ''),
                'public_repos': org_info.get('public_repos', 0),
                'total_private_repos': org_info.get('total_private_repos', 0),
                'followers': org_info.get('followers', 0),
                'following': org_info.get('following', 0),
                'created_at': org_info.get('created_at', ''),
                'updated_at': org_info.get('updated_at', ''),
                'location': org_info.get('location', ''),
                'email': org_info.get('email', ''),
                'blog': org_info.get('blog', ''),
                'twitter_username': org_info.get('twitter_username', ''),
                'repositories': repos if isinstance(repos, list) else [],
                'members': members if isinstance(members, list) else []
            }
            
            return org_data
        
        return {}

    def get_user_info(self, username: str) -> Dict:
        """Get detailed information about a user"""
        self.logger.info(f'[{self.target}] Getting user info for: {username}')
        
        url = f"{self.github_api_base}/users/{username}"
        user_info = self._make_github_request(url)
        
        if user_info:
            # Get user repositories
            repos_url = f"{self.github_api_base}/users/{username}/repos?per_page=100"
            repos = self._make_github_request(repos_url)
            
            # Get user organizations
            orgs_url = f"{self.github_api_base}/users/{username}/orgs?per_page=100"
            orgs = self._make_github_request(orgs_url)
            
            user_data = {
                'username': user_info.get('login', username),
                'name': user_info.get('name', ''),
                'email': user_info.get('email', ''),
                'bio': user_info.get('bio', ''),
                'url': user_info.get('html_url', ''),
                'avatar_url': user_info.get('avatar_url', ''),
                'public_repos': user_info.get('public_repos', 0),
                'public_gists': user_info.get('public_gists', 0),
                'followers': user_info.get('followers', 0),
                'following': user_info.get('following', 0),
                'created_at': user_info.get('created_at', ''),
                'updated_at': user_info.get('updated_at', ''),
                'location': user_info.get('location', ''),
                'blog': user_info.get('blog', ''),
                'twitter_username': user_info.get('twitter_username', ''),
                'company': user_info.get('company', ''),
                'repositories': repos if isinstance(repos, list) else [],
                'organizations': orgs if isinstance(orgs, list) else []
            }
            
            return user_data
        
        return {}

    def clone_repository(self, repo_url: str, repo_name: str) -> Optional[Path]:
        """Clone a repository for analysis"""
        try:
            clone_dir = self.output_dir / "cloned_repos" / repo_name.replace('/', '_')
            ensure_dir(clone_dir)
            
            if clone_dir.exists() and any(clone_dir.iterdir()):
                self.logger.debug(f'[{self.target}] Repository {repo_name} already cloned, skipping...')
                return clone_dir
            
            self.logger.info(f'[{self.target}] Cloning repository: {repo_name}')
            
            # Use shallow clone for faster download
            cmd = ['git', 'clone', '--depth', '1', repo_url, str(clone_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.clone_timeout)
            
            if result.returncode == 0:
                self.logger.success(f'[{self.target}] Successfully cloned {repo_name}')
                return clone_dir
            else:
                self.logger.error(f'[{self.target}] Failed to clone {repo_name}: {result.stderr}')
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f'[{self.target}] Timeout cloning repository: {repo_name}')
            return None
        except Exception as e:
            self.logger.error(f'[{self.target}] Error cloning repository {repo_name}: {e}')
            return None

    def scan_with_trufflehog(self, repo_path: Path) -> List[Dict]:
        """Scan repository with TruffleHog"""
        secrets = []
        
        if not self.tools['trufflehog']:
            self.logger.warning(f'[{self.target}] TruffleHog not found, skipping TruffleHog scan')
            return secrets
        
        try:
            self.logger.debug(f'[{self.target}] Scanning {repo_path.name} with TruffleHog')
            
            cmd = ['trufflehog', '--json', str(repo_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.scan_timeout)
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            secret_data = json.loads(line)
                            secrets.append({
                                'tool': 'trufflehog',
                                'file': secret_data.get('path', ''),
                                'line': secret_data.get('line', ''),
                                'commit': secret_data.get('commit', ''),
                                'secret': secret_data.get('raw', ''),
                                'reason': secret_data.get('reason', ''),
                                'repo': repo_path.name
                            })
                        except json.JSONDecodeError:
                            continue
            
            self.logger.success(f'[{self.target}] TruffleHog found {len(secrets)} secrets in {repo_path.name}')
            
        except subprocess.TimeoutExpired:
            self.logger.error(f'[{self.target}] TruffleHog scan timeout for {repo_path.name}')
        except Exception as e:
            self.logger.error(f'[{self.target}] Error running TruffleHog on {repo_path.name}: {e}')
        
        return secrets

    def scan_with_gitleaks(self, repo_path: Path) -> List[Dict]:
        """Scan repository with GitLeaks"""
        secrets = []
        
        if not self.tools['gitleaks']:
            self.logger.warning(f'[{self.target}] GitLeaks not found, skipping GitLeaks scan')
            return secrets
        
        try:
            self.logger.debug(f'[{self.target}] Scanning {repo_path.name} with GitLeaks')
            
            cmd = ['gitleaks', 'detect', '--source', str(repo_path), '--report-format', 'json', '--report-path', '/dev/stdout']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.scan_timeout)
            
            if result.returncode == 0 and result.stdout:
                try:
                    leaks_data = json.loads(result.stdout)
                    for leak in leaks_data:
                        secrets.append({
                            'tool': 'gitleaks',
                            'file': leak.get('File', ''),
                            'line': leak.get('Line', ''),
                            'commit': leak.get('Commit', ''),
                            'secret': leak.get('Secret', ''),
                            'rule': leak.get('Rule', ''),
                            'repo': repo_path.name
                        })
                except json.JSONDecodeError:
                    pass
            
            self.logger.success(f'[{self.target}] GitLeaks found {len(secrets)} secrets in {repo_path.name}')
            
        except subprocess.TimeoutExpired:
            self.logger.error(f'[{self.target}] GitLeaks scan timeout for {repo_path.name}')
        except Exception as e:
            self.logger.error(f'[{self.target}] Error running GitLeaks on {repo_path.name}: {e}')
        
        return secrets

    def scan_with_custom_patterns(self, repo_path: Path) -> List[Dict]:
        """Scan repository with custom secret patterns"""
        secrets = []
        
        try:
            self.logger.debug(f'[{self.target}] Scanning {repo_path.name} with custom patterns')
            
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and file_path.stat().st_size < self.max_file_size_mb * 1024 * 1024:  # Skip files > 10MB
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        for pattern_type, patterns in self.secret_patterns.items():
                            for pattern in patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                                for match in matches:
                                    line_num = content[:match.start()].count('\n') + 1
                                    line_content = content.split('\n')[line_num - 1] if line_num <= len(content.split('\n')) else ''
                                    
                                    secrets.append({
                                        'tool': 'custom_patterns',
                                        'pattern_type': pattern_type,
                                        'file': str(file_path.relative_to(repo_path)),
                                        'line': line_num,
                                        'line_content': line_content.strip(),
                                        'secret': match.group(0),
                                        'repo': repo_path.name
                                    })
                    except Exception as e:
                        continue
            
            self.logger.success(f'[{self.target}] Custom patterns found {len(secrets)} secrets in {repo_path.name}')
            
        except Exception as e:
            self.logger.error(f'[{self.target}] Error scanning {repo_path.name} with custom patterns: {e}')
        
        return secrets

    def analyze_repository_content(self, repo_path: Path) -> Dict:
        """Analyze repository content for useful data"""
        analysis = {
            'config_files': [],
            'dependency_files': [],
            'documentation': [],
            'scripts': [],
            'interesting_files': [],
            'file_types': {},
            'total_files': 0,
            'total_size': 0
        }
        
        try:
            for file_path in repo_path.rglob('*'):
                if file_path.is_file():
                    analysis['total_files'] += 1
                    analysis['total_size'] += file_path.stat().st_size
                    
                    file_ext = file_path.suffix.lower()
                    analysis['file_types'][file_ext] = analysis['file_types'].get(file_ext, 0) + 1
                    
                    relative_path = str(file_path.relative_to(repo_path))
                    
                    # Categorize files
                    if any(config in relative_path.lower() for config in ['config', 'conf', '.env', 'settings']):
                        analysis['config_files'].append(relative_path)
                    elif any(dep in relative_path.lower() for dep in ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle', 'go.mod']):
                        analysis['dependency_files'].append(relative_path)
                    elif any(doc in relative_path.lower() for doc in ['readme', 'docs', 'documentation', '.md']):
                        analysis['documentation'].append(relative_path)
                    elif any(script in relative_path.lower() for script in ['.sh', '.py', '.js', '.php', '.rb']):
                        analysis['scripts'].append(relative_path)
                    elif any(interesting in relative_path.lower() for interesting in ['backup', 'dump', 'test', 'example', 'sample']):
                        analysis['interesting_files'].append(relative_path)
            
        except Exception as e:
            self.logger.error(f'[{self.target}] Error analyzing repository content: {e}')
        
        return analysis

    def get_commit_history(self, repo_path: Path, max_commits: int = 100) -> List[Dict]:
        """Get recent commit history"""
        commits = []
        
        try:
            cmd = ['git', 'log', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=iso', '-n', str(max_commits)]
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '|' in line:
                        parts = line.split('|', 4)
                        if len(parts) == 5:
                            commits.append({
                                'hash': parts[0],
                                'author_name': parts[1],
                                'author_email': parts[2],
                                'date': parts[3],
                                'message': parts[4]
                            })
            
        except Exception as e:
            self.logger.error(f'[{self.target}] Error getting commit history: {e}')
        
        return commits

    def search_issues_and_prs(self, repo_name: str) -> Dict:
        """Search for issues and pull requests"""
        results = {'issues': [], 'pull_requests': []}
        
        try:
            # Search for issues
            issues_url = f"{self.github_search_base}/issues?q=repo:{repo_name}&per_page=100"
            issues = self._make_github_request(issues_url)
            
            if 'items' in issues:
                for issue in issues['items']:
                    if 'pull_request' not in issue:  # It's an issue, not a PR
                        results['issues'].append({
                            'number': issue['number'],
                            'title': issue['title'],
                            'body': issue.get('body', ''),
                            'state': issue['state'],
                            'created_at': issue['created_at'],
                            'updated_at': issue['updated_at'],
                            'user': issue['user']['login'],
                            'labels': [label['name'] for label in issue.get('labels', [])]
                        })
            
            # Search for pull requests
            prs_url = f"{self.github_search_base}/issues?q=repo:{repo_name}+is:pr&per_page=100"
            prs = self._make_github_request(prs_url)
            
            if 'items' in prs:
                for pr in prs['items']:
                    results['pull_requests'].append({
                        'number': pr['number'],
                        'title': pr['title'],
                        'body': pr.get('body', ''),
                        'state': pr['state'],
                        'created_at': pr['created_at'],
                        'updated_at': pr['updated_at'],
                        'user': pr['user']['login'],
                        'labels': [label['name'] for label in pr.get('labels', [])],
                        'merged': pr.get('pull_request', {}).get('merged_at') is not None
                    })
            
        except Exception as e:
            self.logger.error(f'[{self.target}] Error searching issues and PRs for {repo_name}: {e}')
        
        return results

    def scan_with_trufflehog_github_org(self, target: str) -> List[Dict]:
        """Scan GitHub organization directly with TruffleHog using github --org command"""
        secrets = []
        
        if not self.tools['trufflehog']:
            self.logger.warning(f'[{self.target}] TruffleHog not found, skipping GitHub org scan')
            return secrets
        
        if not self.github_token:
            self.logger.warning(f'[{self.target}] GitHub token not found, skipping GitHub org scan')
            return secrets
        
        try:
            # Extract organization name from target (remove TLD)
            org_name = target.split('.')[0] if '.' in target else target
            
            self.logger.info(f'[{self.target}] Scanning GitHub organization: {org_name}')
            self.logger.debug(f'[{self.target}] DEBUG: trufflehog_github_org enabled: {self.tools.get("trufflehog_github_org")}, trufflehog in PATH: {self.tools.get("trufflehog")}, github_token: {self.github_token}')
            
            cmd = ['trufflehog', 'github', '--org', org_name, '--token', self.github_token, '--json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.scan_timeout)
            
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            
                            # Only process lines that contain secret findings (have SourceMetadata and DetectorName)
                            if 'SourceMetadata' in data and 'DetectorName' in data:
                                source_metadata = data.get('SourceMetadata', {})
                                github_data = source_metadata.get('Data', {}).get('Github', {})
                                
                                secrets.append({
                                    'tool': 'trufflehog_github_org',
                                    'file': github_data.get('file', ''),
                                    'line': github_data.get('line', ''),
                                    'commit': github_data.get('commit', ''),
                                    'secret': data.get('Raw', ''),
                                    'reason': data.get('DetectorName', ''),
                                    'repo': github_data.get('repository', ''),
                                    'org': org_name,
                                    'link': github_data.get('link', ''),
                                    'timestamp': github_data.get('timestamp', ''),
                                    'email': github_data.get('email', ''),
                                    'detector_description': data.get('DetectorDescription', ''),
                                    'verified': data.get('Verified', False),
                                    'redacted': data.get('Redacted', '')
                                })
                            
                        except json.JSONDecodeError as e:
                            # Skip log messages and other non-JSON lines
                            if not line.startswith('{"level":'):
                                self.logger.debug(f'[{self.target}] Failed to parse JSON line: {line[:100]}... Error: {e}')
                            continue
            
            self.logger.success(f'[{self.target}] TruffleHog GitHub org scan found {len(secrets)} secrets in {org_name}')
            
        except subprocess.TimeoutExpired:
            self.logger.error(f'[{self.target}] TruffleHog GitHub org scan timeout for {org_name}')
        except Exception as e:
            self.logger.error(f'[{self.target}] Error running TruffleHog GitHub org scan on {org_name}: {e}')
        
        return secrets

    def save_results(self):
        """Save all results to files"""
        try:
            # Debug logging to identify the issue
            self.logger.debug(f'[{self.target}] Debug - repositories type: {type(self.repositories)}, value: {self.repositories}')
            self.logger.debug(f'[{self.target}] Debug - secrets_found type: {type(self.secrets_found)}, value: {self.secrets_found}')
            self.logger.debug(f'[{self.target}] Debug - useful_data type: {type(self.useful_data)}, value: {self.useful_data}')
            self.logger.debug(f'[{self.target}] Debug - organizations type: {type(self.organizations)}, value: {self.organizations}')
            self.logger.debug(f'[{self.target}] Debug - users type: {type(self.users)}, value: {self.users}')
            
            # Ensure all data structures are lists (not None)
            if self.repositories is None:
                self.repositories = []
            if self.secrets_found is None:
                self.secrets_found = []
            if self.useful_data is None:
                self.useful_data = []
            if self.organizations is None:
                self.organizations = []
            if self.users is None:
                self.users = []
            
            # Save repositories
            if self.save_repositories:
                with open(self.output_dir / 'repositories.json', 'w') as f:
                    json.dump(self.repositories, f, indent=2)
            
            # Save secrets
            if self.save_secrets:
                with open(self.output_dir / 'secrets_found.json', 'w') as f:
                    json.dump(self.secrets_found, f, indent=2)
            
            # Save useful data
            if self.save_useful_data:
                with open(self.output_dir / 'useful_data.json', 'w') as f:
                    json.dump(self.useful_data, f, indent=2)
            
            # Save organizations
            if self.save_organizations:
                with open(self.output_dir / 'organizations.json', 'w') as f:
                    json.dump(self.organizations, f, indent=2)
            
            # Save users
            if self.save_users:
                with open(self.output_dir / 'users.json', 'w') as f:
                    json.dump(self.users, f, indent=2)
            
            # Generate summary report
            if self.generate_report:
                self.generate_summary_report()
            
            self.logger.success(f'[{self.target}] All results saved to {self.output_dir}')
            
        except Exception as e:
            self.logger.error(f'[{self.target}] Error saving results: {e}')
            # Log additional debug information
            self.logger.debug(f'[{self.target}] Debug info - repositories: {type(self.repositories)}, secrets: {type(self.secrets_found)}, useful_data: {type(self.useful_data)}, organizations: {type(self.organizations)}, users: {type(self.users)}')

    def generate_summary_report(self):
        """Generate a summary report"""
        try:
            report_path = self.output_dir / 'summary_report.md'
            
            with open(report_path, 'w') as f:
                f.write('# GitHub Reconnaissance Summary Report\n\n')
                f.write(f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
                
                f.write('## Overview\n\n')
                f.write(f'- **Total Repositories Found**: {len(self.repositories) if self.repositories else 0}\n')
                f.write(f'- **Total Secrets Found**: {len(self.secrets_found) if self.secrets_found else 0}\n')
                f.write(f'- **Organizations Analyzed**: {len(self.organizations) if self.organizations else 0}\n')
                f.write(f'- **Users Analyzed**: {len(self.users) if self.users else 0}\n\n')
                
                if self.secrets_found and len(self.secrets_found) > 0:
                    f.write('## Secrets Found\n\n')
                    f.write('| Tool | Repository | File | Line | Secret Type |\n')
                    f.write('|------|------------|------|------|-------------|\n')
                    
                    for secret in self.secrets_found:
                        tool = secret.get('tool', 'N/A') if secret else 'N/A'
                        repo = secret.get('repo', 'N/A') if secret else 'N/A'
                        file_path = secret.get('file', 'N/A') if secret else 'N/A'
                        line = secret.get('line', 'N/A') if secret else 'N/A'
                        secret_type = secret.get('pattern_type', secret.get('reason', 'N/A')) if secret else 'N/A'
                        f.write(f"| {tool} | {repo} | {file_path} | {line} | {secret_type} |\n")
                    f.write('\n')
                
                if self.repositories and len(self.repositories) > 0:
                    f.write('## Top Repositories\n\n')
                    f.write('| Repository | Stars | Forks | Language | Description |\n')
                    f.write('|------------|-------|-------|----------|-------------|\n')
                    
                    # Sort by stars
                    top_repos = sorted(self.repositories, key=lambda x: x.get('stars', 0) if x else 0, reverse=True)[:10]
                    for repo in top_repos:
                        if repo:
                            name = repo.get('name', 'N/A')
                            url = repo.get('url', '#')
                            stars = repo.get('stars', 0)
                            forks = repo.get('forks', 0)
                            language = repo.get('language', 'N/A')
                            description = repo.get('description', 'N/A')[:50] if repo.get('description') else 'N/A'
                            f.write(f"| [{name}]({url}) | {stars} | {forks} | {language} | {description}... |\n")
                    f.write('\n')
                    
        except Exception as e:
            self.logger.error(f'[{self.target}] Error generating summary report: {e}')

    def clone_and_analyze_repo(self, repo: Dict) -> Dict:
        """Clone and analyze a single repository with all scanning tools"""
        repo_name = repo['name']
        clone_url = repo['clone_url']
        
        # Clone repository
        repo_path = self.clone_repository(clone_url, repo_name)
        if not repo_path:
            return {'repo': repo_name, 'status': 'clone_failed'}
        
        results = {
            'repo': repo_name,
            'status': 'completed',
            'secrets': [],
            'content_analysis': {},
            'commit_history': [],
            'issues_and_prs': {'issues': [], 'pull_requests': []}
        }
        
        # Run all scans concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all scanning tasks
            future_trufflehog = executor.submit(self.scan_with_trufflehog, repo_path)
            future_gitleaks = executor.submit(self.scan_with_gitleaks, repo_path)
            future_custom = executor.submit(self.scan_with_custom_patterns, repo_path)
            future_content = executor.submit(self.analyze_repository_content, repo_path)
            future_commits = executor.submit(self.get_commit_history, repo_path)
            future_issues = executor.submit(self.search_issues_and_prs, repo_name)
            
            # Collect results
            try:
                trufflehog_secrets = future_trufflehog.result(timeout=self.scan_timeout)
                if trufflehog_secrets:
                    results['secrets'].extend(trufflehog_secrets)
            except Exception as e:
                self.logger.error(f'[{self.target}] TruffleHog scan failed for {repo_name}: {e}')
            
            try:
                gitleaks_secrets = future_gitleaks.result(timeout=self.scan_timeout)
                if gitleaks_secrets:
                    results['secrets'].extend(gitleaks_secrets)
            except Exception as e:
                self.logger.error(f'[{self.target}] GitLeaks scan failed for {repo_name}: {e}')
            
            try:
                custom_secrets = future_custom.result(timeout=self.scan_timeout)
                if custom_secrets:
                    results['secrets'].extend(custom_secrets)
            except Exception as e:
                self.logger.error(f'[{self.target}] Custom scan failed for {repo_name}: {e}')
            
            try:
                results['content_analysis'] = future_content.result(timeout=60)
            except Exception as e:
                self.logger.error(f'[{self.target}] Content analysis failed for {repo_name}: {e}')
            
            try:
                results['commit_history'] = future_commits.result(timeout=60)
            except Exception as e:
                self.logger.error(f'[{self.target}] Commit history failed for {repo_name}: {e}')
            
            try:
                results['issues_and_prs'] = future_issues.result(timeout=60)
            except Exception as e:
                self.logger.error(f'[{self.target}] Issues/PRs failed for {repo_name}: {e}')
        
        # Clean up cloned repository
        try:
            shutil.rmtree(repo_path)
        except Exception as e:
            self.logger.warning(f'[{self.target}] Could not clean up {repo_path}: {e}')
        
        return results

    def run_recon(self) -> Dict:
        """Main execution method for GitHub reconnaissance."""
        self.logger.info(f'[{self.target}] Starting comprehensive GitHub reconnaissance')
        
        # Search for repositories
        repositories = self.search_repositories()
        if repositories is None:
            repositories = []
        self.repositories.extend(repositories)
        
        # Get organization info if it looks like an org
        if '/' not in self.target and len(self.target) > 0:
            org_name = self.target.split('.')[0] if '.' in self.target else self.target
            org_info = self.get_organization_info(org_name)
            if org_info:
                self.organizations.append(org_info)
        
        # Get user info if it looks like a user
        if '/' not in self.target and len(self.target) > 0:
            username = self.target.split('.')[0] if '.' in self.target else self.target
            user_info = self.get_user_info(username)
            if user_info:
                self.users.append(user_info)
        
        # Scan GitHub organization directly with TruffleHog (if enabled)
        if self.tools.get('trufflehog_github_org', False):
            self.logger.info(f'[{self.target}] Starting TruffleHog GitHub org scan...')
            github_org_secrets = self.scan_with_trufflehog_github_org(self.target)
            if github_org_secrets is None:
                github_org_secrets = []
            self.secrets_found.extend(github_org_secrets)
        
        # Clone and analyze repositories with threading
        top_repos = sorted(repositories, key=lambda x: x.get('stars', 0), reverse=True)[:self.max_repos_to_scan]
        
        if top_repos:
            self.logger.info(f'[{self.target}] Analyzing {len(top_repos)} repositories with threading...')
            
            # Use ThreadPoolExecutor for concurrent repository processing
            max_workers = min(3, len(top_repos))  # Limit concurrent repos to avoid rate limits
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all repository analysis tasks
                future_to_repo = {
                    executor.submit(self.clone_and_analyze_repo, repo): repo['name']
                    for repo in top_repos
                }
                
                # Process results as they complete
                for future in as_completed(future_to_repo):
                    repo_name = future_to_repo[future]
                    try:
                        result = future.result()
                        
                        # Add secrets to global list
                        if result['secrets']:
                            self.secrets_found.extend(result['secrets'])
                        
                        # Add useful data
                        useful_data = {
                            'repository': result['repo'],
                            'content_analysis': result['content_analysis'],
                            'commit_history': result['commit_history'],
                            'issues_and_prs': result['issues_and_prs']
                        }
                        self.useful_data.append(useful_data)
                        
                        self.logger.success(f'[{self.target}] Completed analysis of {repo_name}')
                        
                    except Exception as e:
                        self.logger.error(f'[{self.target}] Analysis failed for {repo_name}: {e}')
        
        # Save all results
        self.save_results()
        
        self.logger.success(f'[{self.target}] GitHub reconnaissance completed successfully')
        
        return {
            "repos_found": len(repositories),
            "repos_scanned": len(top_repos),
            "secrets_found": len(self.secrets_found),
            "organizations_found": len(self.organizations),
            "users_found": len(self.users)
        }

def run(args: Any, config: Dict, logger: Logger, workflow_data: Dict) -> Dict:
    """Entry point for the reconnaissance module."""
    target = workflow_data['target']
    output_dir = workflow_data['target_output_dir']
    
    if not shutil.which('git'):
        logger.warning("`git` not found in PATH. Skipping GitHub reconnaissance.")
        return {"github_summary": {"status": "skipped"}}
        
    recon = GitHubRecon(target, output_dir, logger, config)
    summary = recon.run_recon()
    
    return {"github_summary": summary}
