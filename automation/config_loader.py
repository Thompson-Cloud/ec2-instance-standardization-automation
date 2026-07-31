"""
Configuration loading and display functions.
"""

import sys
from pathlib import Path

import yaml


def load_config():
    """
    Load the YAML automation configuration.

    Returns:
        dict: Parsed configuration.

    Raises:
        SystemExit: If the configuration cannot be loaded.
    """

    config_path = (
        Path(__file__).parent
        / "config"
        / "config.yaml"
    )

    try:
        with open(
            config_path,
            "r",
            encoding="utf-8",
        ) as file:
            config = yaml.safe_load(file)

    except FileNotFoundError:
        print(
            "\nERROR: Configuration file not found:"
            f"\n{config_path}"
        )
        sys.exit(1)

    except yaml.YAMLError as error:
        print(f"\nERROR: Invalid YAML:\n{error}")
        sys.exit(1)

    if not config:
        print("\nERROR: Configuration file is empty.")
        sys.exit(1)

    return config


def display_configuration(config):
    """
    Display the loaded automation configuration.

    Args:
        config (dict): Parsed configuration.
    """

    print("\nConfiguration Loaded Successfully\n")

    print(
        f"AWS Region           : "
        f"{config['aws']['region']}"
    )
    print(
        f"AWS Profile          : "
        f"{config['aws']['profile']}"
    )

    print(
        f"\nApplication          : "
        f"{config['filters']['Application']}"
    )
    print(
        f"Environment          : "
        f"{config['filters']['Environment']}"
    )

    print(
        f"\nSource Instance Type : "
        f"{config['change']['source_instance_type']}"
    )
    print(
        f"Target Instance Type : "
        f"{config['change']['target_instance_type']}"
    )
    print(
        f"Expected Instances   : "
        f"{config['change']['expected_instance_count']}"
    )

    print(
        f"\nDry Run              : "
        f"{config['execution']['dry_run']}"
    )
    print(
        f"Canary Instance      : "
        f"{config['execution']['canary_instance_name']}"
    )
    print(
        f"Batch Size           : "
        f"{config['execution']['batch_size']}"
    )
    print(
        f"Rollback Enabled     : "
        f"{config['execution']['rollback_on_failure']}"
    )

    print("\nConfiguration validation successful.\n")