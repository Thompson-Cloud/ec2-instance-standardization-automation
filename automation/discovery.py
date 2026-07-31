"""
EC2 instance discovery and inventory display.
"""

import sys

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
)

from logging_config import setup_logging


logger = setup_logging()


def discover_instances(ec2_client, config):
    """
    Discover EC2 instances using configured tags.

    Args:
        ec2_client: Authenticated Boto3 EC2 client.
        config (dict): Parsed automation configuration.

    Returns:
        list[dict]: Matching EC2 instances.

    Raises:
        SystemExit: If discovery fails.
    """

    filters = [
        {
            "Name": f"tag:{tag_name}",
            "Values": [tag_value],
        }
        for tag_name, tag_value
        in config["filters"].items()
    ]

    filters.append(
        {
            "Name": "instance-state-name",
            "Values": [
                "pending",
                "running",
                "stopping",
                "stopped",
            ],
        }
    )

    discovered_instances = []

    try:
        paginator = ec2_client.get_paginator(
            "describe_instances"
        )

        for page in paginator.paginate(
            Filters=filters
        ):
            for reservation in page["Reservations"]:
                for instance in reservation["Instances"]:
                    tags = {
                        tag["Key"]: tag["Value"]
                        for tag
                        in instance.get("Tags", [])
                    }

                    discovered_instances.append(
                        {
                            "instance_id": (
                                instance["InstanceId"]
                            ),
                            "name": tags.get(
                                "Name",
                                "unnamed",
                            ),
                            "role": tags.get(
                                "ApplicationRole",
                                "unknown",
                            ),
                            "instance_type": (
                                instance["InstanceType"]
                            ),
                            "state": (
                                instance["State"]["Name"]
                            ),
                            "availability_zone": (
                                instance["Placement"][
                                    "AvailabilityZone"
                                ]
                            ),
                        }
                    )

        discovered_instances = sorted(
            discovered_instances,
            key=lambda item: item["name"],
        )

        logger.info(
            "Discovered %s matching EC2 instances.",
            len(discovered_instances),
        )

        return discovered_instances

    except (BotoCoreError, ClientError) as error:
        logger.error(
            "Unable to discover EC2 instances: %s",
            error,
        )

        print(
            "\nERROR: Unable to discover "
            f"EC2 instances:\n{error}"
        )

        sys.exit(1)


def display_discovered_instances(
    instances,
    expected_count,
):
    """
    Display the discovered EC2 fleet.

    Args:
        instances (list[dict]): Discovered instances.
        expected_count (int): Expected fleet size.
    """

    actual_count = len(instances)

    print("\nDiscovery Summary")
    print("-" * 76)
    print(
        f"Expected Instances    : "
        f"{expected_count}"
    )
    print(
        f"Discovered Instances  : "
        f"{actual_count}"
    )

    status = (
        "PASS"
        if actual_count == expected_count
        else "FAILED"
    )

    print(f"Discovery Status      : {status}")
    print("-" * 76)

    if instances:
        print(
            f"{'Name':<24}"
            f"{'Role':<12}"
            f"{'Type':<12}"
            f"{'State':<12}"
            f"{'Availability Zone'}"
        )

        print("-" * 76)

        for instance in instances:
            print(
                f"{instance['name']:<24}"
                f"{instance['role']:<12}"
                f"{instance['instance_type']:<12}"
                f"{instance['state']:<12}"
                f"{instance['availability_zone']}"
            )

    print("-" * 76)