"""
Lightweight S3 helper utilities used by the recognition service.

Functions:
 - get_s3_client(): returns a boto3 S3 client using standard env/role credentials
 - list_student_objects(bucket, prefix): list keys under prefix
 - download_student_folder(bucket, prefix, dst_dir): download all objects under prefix into dst_dir

Usage:
 from services.s3_utils import download_student_folder
 download_student_folder('fras-data', 'dataset/09123123/', '/tmp/09123123')

This module intentionally keeps behavior simple:
 - Uses boto3 client (credentials come from environment, ~/.aws/credentials, or attached IAM role)
 - Creates destination folders as needed
 - Skips existing files by default (safe to re-run)
 - Raises exceptions for AWS errors so callers can decide retry/backoff
"""
from __future__ import annotations

import os
import logging
from typing import List

import boto3
from botocore.exceptions import BotoCoreError, ClientError

LOG = logging.getLogger(__name__)


def get_s3_client(region_name: str | None = None):
    """Return a boto3 S3 client. Credentials are resolved by boto3 automatically.

    - region_name: optional AWS region override
    """
    return boto3.client('s3', region_name=region_name) if region_name else boto3.client('s3')


def list_student_objects(bucket: str, prefix: str, s3_client=None) -> List[str]:
    """Return a list of object keys under the given prefix.

    Example: list_student_objects('fras-data', 'dataset/09123123/')
    """
    client = s3_client or get_s3_client()
    paginator = client.get_paginator('list_objects_v2')
    keys: List[str] = []
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                keys.append(obj['Key'])
    except (BotoCoreError, ClientError) as e:
        LOG.exception('failed to list objects for %s/%s', bucket, prefix)
        raise
    return keys


def download_student_folder(bucket: str, prefix: str, dst_dir: str, s3_client=None, skip_existing: bool = True) -> List[str]:
    """Download all objects under `prefix` into `dst_dir`.

    - Returns list of local file paths downloaded.
    - If skip_existing is True, existing local files are not re-downloaded.
    """
    client = s3_client or get_s3_client()
    keys = list_student_objects(bucket, prefix, s3_client=client)
    os.makedirs(dst_dir, exist_ok=True)
    downloaded: List[str] = []
    for key in keys:
        if key.endswith('/'):
            continue
        rel_path = os.path.relpath(key, prefix)
        local_path = os.path.join(dst_dir, rel_path)
        local_dir = os.path.dirname(local_path)
        os.makedirs(local_dir, exist_ok=True)
        if skip_existing and os.path.exists(local_path):
            LOG.debug('skip existing %s', local_path)
            downloaded.append(local_path)
            continue
        try:
            LOG.debug('downloading s3://%s/%s -> %s', bucket, key, local_path)
            client.download_file(bucket, key, local_path)
            downloaded.append(local_path)
        except (BotoCoreError, ClientError) as e:
            LOG.exception('failed to download %s/%s', bucket, key)
            raise
    return downloaded
