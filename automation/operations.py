"""
EC2 resize, rollback, canary, and batch operations.
"""

from datetime import datetime

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    WaiterError,
)

from logging_config import setup_logging


logger = setup_logging()


def build_result(
    instance,
    target_type,
    result,
    final_state="unknown",
    rollback_result="not-required",
    error="",
    started_at=None,
    completed_at=None,
):
    """
    Build a standardized per-instance result.

    Args:
        instance (dict): Original instance information.
        target_type (str): Requested target instance type.
        result (str): Operation result.
        final_state (str): Final observed EC2 state.
        rollback_result (str): Rollback outcome.
        error (str): Error description.
        started_at (datetime): Operation start time.
        completed_at (datetime): Operation completion time.

    Returns:
        dict: Standardized result record.
    """

    return {
        "run_id": "",
        "instance_name": instance["name"],
        "instance_id": instance["instance_id"],
        "role": instance.get("role", "unknown"),
        "availability_zone": instance.get(
            "availability_zone",
            "unknown",
        ),
        "original_type": instance["instance_type"],
        "target_type": target_type,
        "original_state": instance["state"],
        "final_state": final_state,
        "result": result,
        "rollback_result": rollback_result,
        "error": error,
        "started_at": started_at or datetime.now(),
        "completed_at": completed_at or datetime.now(),
    }


def resize_instance(
    ec2_client,
    instance,
    config,
):
    """
    Resize one EC2 instance and validate the result.

    Args:
        ec2_client: Authenticated EC2 client.
        instance (dict): Instance information.
        config (dict): Parsed configuration.

    Returns:
        dict: Standardized resize result.

    Raises:
        RuntimeError: If resizing fails.
    """

    started_at = datetime.now()

    instance_id = instance["instance_id"]
    instance_name = instance["name"]
    original_type = instance["instance_type"]
    original_state = instance["state"]

    target_type = config["change"]["target_instance_type"]

    stop_wait = config["timeouts"]["stop_wait"]
    start_wait = config["timeouts"]["start_wait"]
    status_wait = config["timeouts"]["status_wait"]

    print(f"\nProcessing instance: {instance_name}")
    print(f"Instance ID         : {instance_id}")
    print(f"Original Type       : {original_type}")
    print(f"Target Type         : {target_type}")

    try:
        if original_state != "stopped":
            print("Stopping instance...")

            ec2_client.stop_instances(
                InstanceIds=[instance_id],
            )

            ec2_client.get_waiter(
                "instance_stopped"
            ).wait(
                InstanceIds=[instance_id],
                WaiterConfig={
                    "Delay": 10,
                    "MaxAttempts": max(
                        1,
                        stop_wait // 10,
                    ),
                },
            )

            print("Instance stopped.")

        print(
            f"Changing instance type to "
            f"{target_type}..."
        )

        ec2_client.modify_instance_attribute(
            InstanceId=instance_id,
            InstanceType={
                "Value": target_type,
            },
        )

        print("Starting instance...")

        ec2_client.start_instances(
            InstanceIds=[instance_id],
        )

        ec2_client.get_waiter(
            "instance_running"
        ).wait(
            InstanceIds=[instance_id],
            WaiterConfig={
                "Delay": 10,
                "MaxAttempts": max(
                    1,
                    start_wait // 10,
                ),
            },
        )

        print("Instance is running.")
        print("Waiting for AWS status checks...")

        ec2_client.get_waiter(
            "instance_status_ok"
        ).wait(
            InstanceIds=[instance_id],
            WaiterConfig={
                "Delay": 15,
                "MaxAttempts": max(
                    1,
                    status_wait // 15,
                ),
            },
        )

        response = ec2_client.describe_instances(
            InstanceIds=[instance_id],
        )

        updated_instance = (
            response["Reservations"][0]["Instances"][0]
        )

        updated_type = updated_instance["InstanceType"]
        updated_state = updated_instance["State"]["Name"]

        if updated_type != target_type:
            raise RuntimeError(
                f"Expected instance type {target_type}, "
                f"but found {updated_type}."
            )

        if updated_state != "running":
            raise RuntimeError(
                f"Expected running state, "
                f"but found {updated_state}."
            )

        completed_at = datetime.now()

        print(f"Resize successful: {instance_name}")

        logger.info(
            "Resize successful for %s: %s to %s",
            instance_name,
            original_type,
            target_type,
        )

        return build_result(
            instance=instance,
            target_type=target_type,
            result="success",
            final_state=updated_state,
            rollback_result="not-required",
            started_at=started_at,
            completed_at=completed_at,
        )

    except (
        BotoCoreError,
        ClientError,
        WaiterError,
        RuntimeError,
    ) as error:
        logger.error(
            "Resize failed for %s: %s",
            instance_name,
            error,
        )

        raise RuntimeError(str(error)) from error


def rollback_instance(
    ec2_client,
    instance,
    config,
):
    """
    Restore an EC2 instance to its original type and state.

    Args:
        ec2_client: Authenticated EC2 client.
        instance (dict): Original instance information.
        config (dict): Parsed configuration.

    Returns:
        str: Either success or failed.
    """

    instance_id = instance["instance_id"]
    instance_name = instance["name"]
    original_type = instance["instance_type"]
    original_state = instance["state"]

    stop_wait = config["timeouts"]["stop_wait"]
    start_wait = config["timeouts"]["start_wait"]
    status_wait = config["timeouts"]["status_wait"]

    print(f"\nRolling back {instance_name}...")

    try:
        response = ec2_client.describe_instances(
            InstanceIds=[instance_id],
        )

        current_instance = (
            response["Reservations"][0]["Instances"][0]
        )

        current_state = current_instance["State"]["Name"]

        if current_state != "stopped":
            ec2_client.stop_instances(
                InstanceIds=[instance_id],
            )

            ec2_client.get_waiter(
                "instance_stopped"
            ).wait(
                InstanceIds=[instance_id],
                WaiterConfig={
                    "Delay": 10,
                    "MaxAttempts": max(
                        1,
                        stop_wait // 10,
                    ),
                },
            )

        ec2_client.modify_instance_attribute(
            InstanceId=instance_id,
            InstanceType={
                "Value": original_type,
            },
        )

        if original_state == "running":
            ec2_client.start_instances(
                InstanceIds=[instance_id],
            )

            ec2_client.get_waiter(
                "instance_running"
            ).wait(
                InstanceIds=[instance_id],
                WaiterConfig={
                    "Delay": 10,
                    "MaxAttempts": max(
                        1,
                        start_wait // 10,
                    ),
                },
            )

            ec2_client.get_waiter(
                "instance_status_ok"
            ).wait(
                InstanceIds=[instance_id],
                WaiterConfig={
                    "Delay": 15,
                    "MaxAttempts": max(
                        1,
                        status_wait // 15,
                    ),
                },
            )

        print(f"Rollback successful: {instance_name}")

        logger.info(
            "Rollback successful for %s.",
            instance_name,
        )

        return "success"

    except (
        BotoCoreError,
        ClientError,
        WaiterError,
    ) as error:
        logger.error(
            "Rollback failed for %s: %s",
            instance_name,
            error,
        )

        print(
            f"Rollback failed for "
            f"{instance_name}: {error}"
        )

        return "failed"


def run_resize_workflow(
    ec2_client,
    instances,
    config,
):
    """
    Run the canary-first batch resize workflow.

    Args:
        ec2_client: Authenticated EC2 client.
        instances (list[dict]): Validated EC2 fleet.
        config (dict): Parsed configuration.

    Returns:
        tuple: Overall status and per-instance results.
    """

    target_type = config["change"]["target_instance_type"]
    canary_name = config["execution"]["canary_instance_name"]
    batch_size = config["execution"]["batch_size"]

    rollback_enabled = (
        config["execution"]["rollback_on_failure"]
    )

    instance_results = []

    canary = next(
        instance
        for instance in instances
        if instance["name"] == canary_name
    )

    remaining_instances = [
        instance
        for instance in instances
        if instance["name"] != canary_name
    ]

    print("\nStarting canary resize...")
    print("-" * 76)

    canary_started_at = datetime.now()

    try:
        canary_result = resize_instance(
            ec2_client,
            canary,
            config,
        )

        instance_results.append(canary_result)

    except RuntimeError as error:
        rollback_result = "not-attempted"

        print(f"\nCanary resize failed: {error}")

        if rollback_enabled:
            rollback_result = rollback_instance(
                ec2_client,
                canary,
                config,
            )

        instance_results.append(
            build_result(
                instance=canary,
                target_type=target_type,
                result="failed",
                rollback_result=rollback_result,
                error=str(error),
                started_at=canary_started_at,
                completed_at=datetime.now(),
            )
        )

        print(
            "\nAutomation stopped. "
            "No batches were started."
        )

        return "failed", instance_results

    print("\nCanary completed successfully.")
    print(f"Proceeding with batches of {batch_size}.")

    for start_index in range(
        0,
        len(remaining_instances),
        batch_size,
    ):
        batch = remaining_instances[
            start_index:start_index + batch_size
        ]

        batch_number = (
            start_index // batch_size
        ) + 1

        completed_results = []

        print(f"\nStarting Batch {batch_number}")
        print("-" * 76)

        for instance in batch:
            instance_started_at = datetime.now()

            try:
                result = resize_instance(
                    ec2_client,
                    instance,
                    config,
                )

                completed_results.append(
                    {
                        "instance": instance,
                        "result": result,
                    }
                )

                instance_results.append(result)

            except RuntimeError as error:
                print(
                    f"\nBatch {batch_number} failed while "
                    f"processing {instance['name']}: {error}"
                )

                rollback_result = "not-attempted"

                if rollback_enabled:
                    print(
                        f"Rolling back "
                        f"Batch {batch_number}..."
                    )

                    failed_rollback = rollback_instance(
                        ec2_client,
                        instance,
                        config,
                    )

                    rollback_result = failed_rollback

                    for completed_item in reversed(
                        completed_results
                    ):
                        completed_instance = (
                            completed_item["instance"]
                        )
                        completed_result = (
                            completed_item["result"]
                        )

                        completed_rollback = rollback_instance(
                            ec2_client,
                            completed_instance,
                            config,
                        )

                        completed_result[
                            "rollback_result"
                        ] = completed_rollback

                        completed_result["final_state"] = (
                            completed_instance["state"]
                        )

                instance_results.append(
                    build_result(
                        instance=instance,
                        target_type=target_type,
                        result="failed",
                        rollback_result=rollback_result,
                        error=str(error),
                        started_at=instance_started_at,
                        completed_at=datetime.now(),
                    )
                )

                print(
                    "\nAutomation stopped. "
                    "No additional batches "
                    "were processed."
                )

                return "failed", instance_results

        print(
            f"Batch {batch_number} "
            "completed successfully."
        )

    print("\n" + "=" * 76)
    print(
        "EC2 resize automation "
        "completed successfully."
    )
    print(f"Canary processed       : {canary_name}")
    print(
        f"Remaining processed    : "
        f"{len(remaining_instances)}"
    )
    print(f"Final instance type    : {target_type}")
    print("=" * 76)

    return "success", instance_results