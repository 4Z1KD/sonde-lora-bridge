import json
import os


class ConfigLoader:
    """Loads configuration from config.dev.json or config.public.json."""

    @staticmethod
    def load_config():
        """
        Load configuration, preferring config.dev.json over config.public.json.
        Paths are relative to the script directory.

        Returns:
            dict: Configuration dictionary
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        dev_config = os.path.join(script_dir, "config.dev.json")
        public_config = os.path.join(script_dir, "config.public.json")
        
        config_path = dev_config if os.path.exists(dev_config) else public_config
        
        with open(config_path, "r") as f:
            return json.load(f)
