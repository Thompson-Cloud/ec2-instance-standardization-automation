"""
EC2 fleet validation and dry-run controls.
"""

import sys


def validate_discovered_instances(
    instances,
    config,
):
    """
    Validate the discovered EC2 fleet.

    Returns:
        tuple[bool, list[str]]:
            Validation status and validation errors.
    """

    errors = []

    expected_count = (
        config["change"]["expected_instance_count"]
    )

    canary_name = (
        config["execution"]["canary_instance_name"]
    )

    if len(instances) != expected_count:
        errors.append(
            f"Expected {expected_count} instances, "
            f"but discovered {len(instances)}."
        )

    discovered_names = {
        instance["name"]
        for instance in instances
    }

    if canary_name not in discovered_names:
        errors.append(
            f"Configured canary instance "
            f"'{canary_name}' was not discovered."
        )

    print("\nFleet Validation")
    print("-" * 76)

    if errors:
        print("Validation Status     : FAILED")
        print("\nThe automation cannot continue:")

        for error in errors:
            print(f"  - {error}")

        print("\nNo EC2 changes were performed.")
        print("-" * 76)

        return False, errors

    print("Validation Status     : PASSED")
    print("-" * 76)

    return True, []

def enforce_dry_run(config):
    """
    Stop before changes when dry-run is enabled.

    Args:
        config (dict): Parsed configuration.

    Returns:
        bool: True when live execution may continue.
    """

    if config["execution"]["dry_run"]:
        print("\nDry Run Complete")
        print("-" * 76)
        print(
            "The configuration, AWS connection, "
            "discovery, and validation"
        )
        print(
            "steps completed without making "
            "any EC2 changes."
        )
        print("-" * 76)

        return False

    return True