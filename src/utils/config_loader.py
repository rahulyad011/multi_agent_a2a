"""Configuration loader for agent framework."""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Agent configuration data class."""
    name: str
    description: str
    version: str
    port: int
    url: str
    capabilities: Dict[str, Any]
    skills: list[Dict[str, Any]]
    agent_config: Dict[str, Any]


class ConfigLoader:
    """Load and manage agent configurations."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize config loader.
        
        Args:
            config_dir: Directory containing config files. Defaults to project_root/config
        """
        if config_dir is None:
            # Default to project root/config
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.agents_dir = self.config_dir / "agents"
        
        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.agents_dir.mkdir(exist_ok=True)
    
    def load_agent_config(self, agent_name: str) -> AgentConfig:
        """Load configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent (filename without .yaml)
            
        Returns:
            AgentConfig object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_path = self.agents_dir / f"{agent_name}.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Substitute environment variables
        config_data = self._substitute_env_vars(config_data)
        
        # Validate and create AgentConfig
        return self._parse_agent_config(config_data)
    
    def load_all_agent_configs(self) -> Dict[str, AgentConfig]:
        """Load all agent configurations.
        
        Returns:
            Dictionary mapping agent names to AgentConfig objects
        """
        configs = {}
        
        if not self.agents_dir.exists():
            return configs
        
        for config_file in self.agents_dir.glob("*.yaml"):
            agent_name = config_file.stem
            try:
                configs[agent_name] = self.load_agent_config(agent_name)
            except Exception as e:
                print(f"[WARNING] Failed to load config for {agent_name}: {e}")
                continue
        
        return configs
    
    def get_orchestrator_config(self) -> Dict[str, Any]:
        """Load orchestrator configuration.
        
        Returns:
            Dictionary with orchestrator configuration (flattened, no 'orchestrator' key)
        """
        config_path = self.config_dir / "orchestrator.yaml"
        
        if not config_path.exists():
            # Return default config
            return {
                "remote_agent_urls": [],
                "model_name": os.getenv("LITELLM_MODEL", "gemini/gemini-2.0-flash-001"),
            }
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Substitute environment variables
        config_data = self._substitute_env_vars(config_data)
        
        # If config has 'orchestrator' key, extract it
        if 'orchestrator' in config_data:
            return config_data['orchestrator']
        
        return config_data
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """Recursively substitute environment variables in config.
        
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        
        Args:
            data: Configuration data (dict, list, or str)
            
        Returns:
            Data with environment variables substituted
        """
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Handle ${VAR_NAME} and ${VAR_NAME:default}
            import re
            pattern = r'\$\{([^}:]+)(?::([^}]+))?\}'
            
            def replace_var(match):
                var_name = match.group(1)
                default = match.group(2) if match.group(2) else None
                return os.getenv(var_name, default) if default else os.getenv(var_name, match.group(0))
            
            return re.sub(pattern, replace_var, data)
        else:
            return data
    
    def _parse_agent_config(self, data: Dict[str, Any]) -> AgentConfig:
        """Parse and validate agent configuration.
        
        Args:
            data: Raw configuration dictionary
            
        Returns:
            AgentConfig object
            
        Raises:
            ValueError: If required fields are missing
        """
        agent_data = data.get("agent", {})
        
        # Required fields
        required_fields = ["name", "description", "version", "port", "url"]
        for field in required_fields:
            if field not in agent_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Default values
        capabilities = agent_data.get("capabilities", {})
        skills = agent_data.get("skills", [])
        agent_config = agent_data.get("agent_config", {})
        
        return AgentConfig(
            name=agent_data["name"],
            description=agent_data["description"],
            version=agent_data["version"],
            port=int(agent_data["port"]),
            url=agent_data["url"],
            capabilities=capabilities,
            skills=skills,
            agent_config=agent_config,
        )

