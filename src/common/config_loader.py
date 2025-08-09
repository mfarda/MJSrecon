"""
Configuration Loader for MJSRecon
Handles loading and merging configuration from YAML files
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from .logger import Logger


class ConfigLoader:
    """Loads and manages configuration from YAML files"""
    
    def __init__(self, config_dir: str = "config", logger: Optional[Logger] = None):
        self.config_dir = Path(config_dir)
        # Do not instantiate Logger here; use only if provided by caller
        self.logger = logger
        self._config_cache = {}
    
    def load_config(self, environment: str = "development") -> Dict[str, Any]:
        """
        Load and merge configuration files
        
        Args:
            environment: Environment to load (development, production, testing)
            
        Returns:
            Merged configuration dictionary
        """
        config = {}
        
        # Load default configuration
        config.update(self._load_yaml_file("defaults.yaml"))
        
        # Load environment-specific overrides
        env_config = self._load_yaml_file("environments.yaml")
        if environment in env_config:
            config = self._deep_merge(config, env_config[environment])
        
        # Load scanner-specific configurations
        scanners = ["github_scanner", "gitlab_scanner", "bitbucket_scanner", "gitea_scanner"]
        for scanner in scanners:
            scanner_config = self._load_yaml_file(f"{scanner}.yaml")
            if scanner_config:
                config[scanner] = scanner_config
        
        # Load patterns
        patterns = self._load_yaml_file("patterns.yaml")
        if patterns:
            config["patterns"] = patterns
        
        # Load secrets (if exists)
        secrets = self._load_secrets()
        if secrets:
            config = self._deep_merge(config, secrets)
        
        # Update tool paths to be absolute
        config = self._update_tool_paths(config)
        
        return config
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            if self.logger:
                self.logger.warning(f"Configuration file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if self.logger:
                    self.logger.info(f"Loaded configuration: {filename}")
                return content or {}
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading configuration file {filename}: {e}")
            return {}
    
    def _load_secrets(self) -> Optional[Dict[str, Any]]:
        """Load secrets configuration file"""
        secrets_file = self.config_dir / "secrets.yaml"
        
        if not secrets_file.exists():
            if self.logger:
                self.logger.info("No secrets.yaml file found, using environment variables")
            return None
        
        try:
            with open(secrets_file, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                if self.logger:
                    self.logger.info("Loaded secrets configuration")
                return self._resolve_environment_variables(content or {})
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading secrets file: {e}")
            return None
    
    def _resolve_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve environment variable placeholders in configuration"""
        resolved = {}
        
        for key, value in config.items():
            if isinstance(value, dict):
                resolved[key] = self._resolve_environment_variables(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved[key] = os.getenv(env_var, value)
            else:
                resolved[key] = value
        
        return resolved
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _update_tool_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update tool paths to be absolute"""
        if "tools" in config and "python_tools" in config["tools"]:
            base_dir = Path(__file__).resolve().parent.parent.parent
            for tool_name, tool_path in config["tools"]["python_tools"].items():
                if isinstance(tool_path, str) and not Path(tool_path).is_absolute():
                    config["tools"]["python_tools"][tool_name] = str(base_dir / tool_path)
        
        return config
    
    def get_scanner_config(self, scanner_name: str) -> Dict[str, Any]:
        """Get configuration for a specific scanner"""
        config = self.load_config()
        return config.get(f"{scanner_name}_scanner", {})
    
    def get_patterns(self) -> Dict[str, Any]:
        """Get secret detection patterns"""
        config = self.load_config()
        return config.get("patterns", {})
    
    def reload_config(self) -> Dict[str, Any]:
        """Reload configuration (clear cache)"""
        self._config_cache.clear()
        return self.load_config()


# Global configuration loader instance
config_loader = ConfigLoader()


def load_config(environment: str = "development") -> Dict[str, Any]:
    """Load configuration for the specified environment"""
    return config_loader.load_config(environment)


def get_scanner_config(scanner_name: str) -> Dict[str, Any]:
    """Get configuration for a specific scanner"""
    return config_loader.get_scanner_config(scanner_name)


def get_patterns() -> Dict[str, Any]:
    """Get secret detection patterns"""
    return config_loader.get_patterns() 