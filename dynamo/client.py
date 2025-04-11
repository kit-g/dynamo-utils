from typing import Optional

import boto3
from botocore.client import BaseClient

_db: Optional[BaseClient] = None


def db() -> BaseClient:
    """
    Singleton database instance.

    :return: instance of boto3's DynamoDB client
    """
    global _db

    if _db is not None:
        return _db

    _db = boto3.client('dynamodb')

    return _db
