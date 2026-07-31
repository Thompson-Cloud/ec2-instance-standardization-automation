"""
AWS authentication and client creation.
"""

import sys

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    ProfileNotFound,
)

from logging_config import setup_logging


logger = setup_logging()


def create_aws_clients(config):
    """
    Create authenticated AWS clients.

    Args:
        config (dict): Parsed automation configuration.

    Returns:
        tuple: EC2 client and AWS account ID.

    Raises:
        SystemExit: If AWS authentication fails.
    """

    region = config["aws"]["region"]
    profile = config["aws"]["profile"]

    try:
        session = boto3.Session(
            profile_name=profile,
            region_name=region,
        )

        sts_client = session.client("sts")
        identity = sts_client.get_caller_identity()

        ec2_client = session.client("ec2")

        logger.info(
            "Successfully authenticated with AWS."
        )

        return ec2_client, identity["Account"]

    except ProfileNotFound:
        logger.error(
            "AWS profile '%s' was not found.",
            profile,
        )

        print(
            f"\nERROR: AWS profile "
            f"'{profile}' was not found."
        )
        print(
            "Check your AWS CLI configuration "
            "and try again."
        )

        sys.exit(1)

    except (BotoCoreError, ClientError) as error:
        logger.error(
            "Unable to connect to AWS: %s",
            error,
        )

        print(
            "\nERROR: Unable to connect to AWS:"
            f"\n{error}"
        )

        sys.exit(1)