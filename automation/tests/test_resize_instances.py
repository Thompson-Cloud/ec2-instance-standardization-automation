import sys
from pathlib import Path

import yaml


def load_config():
    """
    Load the YAML configuration file.

    Returns:
        dict: Parsed configuration.

    Raises:
        SystemExit: If the file cannot be found or parsed.
    """

    config_path = Path(__file__).parent / "config" / "config.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)

    except yaml.YAMLError as error:
        print(f"ERROR: Invalid YAML: {error}")
        sys.exit(1)


def main():
    config = load_config()

    print("\nConfiguration loaded successfully.\n")

    print(config)


if __name__ == "__main__":
    main()