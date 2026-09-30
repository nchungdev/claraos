import os
import yaml
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = os.getenv("AETHER_CONFIG_FILE", "/config/config.yaml")
FALLBACK_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.example.yaml"


class ConfigManager:
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """Loads configuration from yaml file, with environment variable overrides."""
        # 1. Load from file or fallback to example template
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        elif FALLBACK_CONFIG_PATH.exists():
            with open(FALLBACK_CONFIG_PATH, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        else:
            self.data = {"system": {}, "modules": {}}

        # 2. Apply environment variable overrides
        # e.g., AETHER_MODULE_DEBRID_ENABLED=true -> modules.debrid.enabled = True
        self._apply_env_overrides()
        return self.data

    def _apply_env_overrides(self):
        for key, value in os.environ.items():
            if not key.startswith("AETHER_"):
                continue
            parts = key[7:].lower().split("_")
            if len(parts) >= 2 and parts[0] == "module":
                mod_name = parts[1]
                field = "_".join(parts[2:]) if len(parts) > 2 else "enabled"
                if "modules" not in self.data:
                    self.data["modules"] = {}
                if mod_name not in self.data["modules"]:
                    self.data["modules"][mod_name] = {}
                
                # Convert bool/int/str
                if value.lower() in ("true", "1", "yes"):
                    parsed_val = True
                elif value.lower() in ("false", "0", "no"):
                    parsed_val = False
                elif value.isdigit():
                    parsed_val = int(value)
                else:
                    parsed_val = value

                self.data["modules"][mod_name][field] = parsed_val

    def get(self, *keys: str, default: Any = None) -> Any:
        """Helper to get nested config key, e.g. config.get('modules', 'sync', 'enabled')"""
        curr = self.data
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return default
        return curr

    def set(self, *keys: str, value: Any):
        """Sets a nested value in configuration."""
        curr = self.data
        for k in keys[:-1]:
            if k not in curr or not isinstance(curr[k], dict):
                curr[k] = {}
            curr = curr[k]
        curr[keys[-1]] = value

    def save(self):
        """Saves current config data back to yaml file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.data, f, default_flow_style=False, sort_keys=False)


# Global singleton instance
config = ConfigManager()
