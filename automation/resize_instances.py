"""
EC2 Infrastructure Standardization Automation

This script discovers production EC2 instances and performs a controlled
instance type upgrade using a canary-first deployment strategy.

Author: Thompson
"""

from datetime import datetime

from aws_clients import create_aws_clients
from config_loader import (
    display_configuration,
    load_config,
)
from discovery import (
    discover_instances,
    display_discovered_instances,
)
from operations import run_resize_workflow
from reporting import (
    generate_run_id,
    write_reports,
)
from validation import (
    enforce_dry_run,
    validate_discovered_instances,
)


def display_banner():
    """Display the application banner."""

    print("=" * 60)
    print(
        " EC2 Infrastructure "
        "Standardization Automation"
    )
    print("=" * 60)


def create_run_metadata(config):
    """
    Create metadata for the automation run.

    Args:
        config (dict): Parsed configuration.

    Returns:
        dict: Initial run metadata.
    """

    return {
        "run_id": generate_run_id(),
        "started_at": datetime.now(),
        "completed_at": None,
        "account_id": "",
        "region": config["aws"]["region"],
        "application": config["filters"]["Application"],
        "environment": config["filters"]["Environment"],
        "execution_mode": (
            "Dry Run"
            if config["execution"]["dry_run"]
            else "Live"
        ),
        "source_instance_type": (
            config["change"]["source_instance_type"]
        ),
        "target_instance_type": (
            config["change"]["target_instance_type"]
        ),
        "overall_status": "started",
    }


def attach_run_id(results, run_id):
    """
    Add the run ID to every instance result.

    Args:
        results (list[dict]): Per-instance results.
        run_id (str): Automation run identifier.
    """

    for result in results:
        result["run_id"] = run_id


def generate_reports(
    instance_results,
    run_metadata,
):
    """
    Generate and display report file locations.

    Args:
        instance_results (list[dict]): Instance results.
        run_metadata (dict): Overall run metadata.
    """

    attach_run_id(
        instance_results,
        run_metadata["run_id"],
    )

    csv_path, json_path, markdown_path = write_reports(
        instance_results,
        run_metadata,
    )

    print("\nReports Generated")
    print("-" * 76)
    print(f"CSV Report            : {csv_path}")
    print(f"JSON Report           : {json_path}")
    print(f"Markdown Report       : {markdown_path}")
    print("-" * 76)


def main():
    """Run the EC2 standardization automation."""

    display_banner()

    config = load_config()
    run_metadata = create_run_metadata(config)
    instance_results = []

    display_configuration(config)

    print("Connecting securely to AWS...")

    ec2_client, account_id = create_aws_clients(
        config
    )

    run_metadata["account_id"] = account_id

    print("AWS connection successful.")
    print(f"AWS Account ID        : {account_id}")
    print(
        f"EC2 Region            : "
        f"{config['aws']['region']}"
    )

    print(
        "\nDiscovering EC2 instances "
        "using configured tags..."
    )

    instances = discover_instances(
        ec2_client,
        config,
    )

    expected_count = (
        config["change"]["expected_instance_count"]
    )

    display_discovered_instances(
        instances,
        expected_count,
    )

    validation_passed, validation_errors = (
        validate_discovered_instances(
            instances,
            config,
        )
    )

    if not validation_passed:
        run_metadata["completed_at"] = datetime.now()
        run_metadata["overall_status"] = (
            "validation-failed"
        )
        run_metadata["validation_errors"] = (
            validation_errors
        )

        generate_reports(
            instance_results,
            run_metadata,
        )

        return

    if not enforce_dry_run(config):
        run_metadata["completed_at"] = datetime.now()
        run_metadata["overall_status"] = (
            "dry-run-complete"
        )

        generate_reports(
            instance_results,
            run_metadata,
        )

        return

    overall_status, instance_results = (
        run_resize_workflow(
            ec2_client,
            instances,
            config,
        )
    )

    run_metadata["completed_at"] = datetime.now()
    run_metadata["overall_status"] = (
        overall_status
    )

    generate_reports(
        instance_results,
        run_metadata,
    )


if __name__ == "__main__":
    main()