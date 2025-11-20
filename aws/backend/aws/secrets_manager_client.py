"""
Client for interacting with AWS Secrets Manager.

This module provides a cached function to retrieve secrets, reducing latency and cost.
"""

import json
from functools import lru_cache
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

from ..utils.logger import get_logger

LOGGER = get_logger(__name__)


@lru_cache(maxsize=32)
def get_secret(secret_name: str, region_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a secret from AWS Secrets Manager and parse it as JSON.

    Args:
        secret_name: The name or ARN of the secret.
        region_name: The AWS region where the secret is stored.

    Returns:
        A dictionary containing the secret keys and values, or None if an error occurs.
    """
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    LOGGER.info(f"Attempting to retrieve secret: {secret_name}")

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        LOGGER.error(f"Failed to retrieve secret '{secret_name}': {e}")
        return None

    secret = get_secret_value_response.get("SecretString")
    if not secret:
        LOGGER.warning(f"Secret '{secret_name}' does not have a SecretString.")
        return None

    try:
        return json.loads(secret)
    except json.JSONDecodeError:
        LOGGER.error(f"Failed to decode JSON from secret '{secret_name}'.")
        return None
