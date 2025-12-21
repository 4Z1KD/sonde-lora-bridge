import json
import os


class ConfigLoader:
    """Loads configuration from config.dev.json or config.public.json."""

    @staticmethod
    def load_config():
        """
        Load configuration, preferring config.dev.json over config.public.json.

        Returns:
            dict: Configuration dictionary
        """
        config_path = (
            "config.dev.json"
            if os.path.exists("config.dev.json")
            else "config.public.json"
        )
        with open(config_path, "r") as f:
            return json.load(f)
