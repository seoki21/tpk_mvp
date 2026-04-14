"""
Cloudflare R2 Object Storage 서비스 모듈
파일 업로드/다운로드/삭제/복사 등 R2 관련 작업을 처리한다.
boto3 S3 호환 API를 사용한다.
"""
import io
import boto3
from botocore.config import Config
from typing import Optional

from app.config import (
    R2_ENDPOINT_URL,
    R2_BUCKET_NAME,
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
)

# boto3 S3 클라이언트 싱글턴
_s3_client = None


def _get_client():
    """
    R2 S3 호환 클라이언트 싱글턴을 반환한다.
    환경변수가 설정되지 않은 경우 에러를 발생시킨다.
    """
    global _s3_client
    if _s3_client is None:
        if not R2_ENDPOINT_URL or not R2_BUCKET_NAME:
            raise ValueError("R2 환경변수(R2_ENDPOINT_URL, R2_BUCKET_NAME)가 설정되지 않았습니다.")
        _s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            ),
            region_name="auto",
        )
    return _s3_client


def upload_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """
    바이트 데이터를 R2에 업로드한다.

    Args:
        key: R2 오브젝트 키 (예: "exam/14/abc123.pdf")
        data: 업로드할 바이트 데이터
        content_type: MIME 타입

    Returns:
        저장된 오브젝트 키
    """
    client = _get_client()
    client.put_object(
        Bucket=R2_BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key


def download_bytes(key: str) -> bytes:
    """
    R2에서 파일을 바이트로 다운로드한다.

    Args:
        key: R2 오브젝트 키

    Returns:
        파일 바이트 데이터

    Raises:
        FileNotFoundError: 오브젝트가 존재하지 않는 경우
    """
    client = _get_client()
    try:
        response = client.get_object(Bucket=R2_BUCKET_NAME, Key=key)
        return response["Body"].read()
    except client.exceptions.NoSuchKey:
        raise FileNotFoundError(f"R2에서 파일을 찾을 수 없습니다: {key}")


def download_stream(key: str):
    """
    R2에서 파일을 스트리밍 바디로 반환한다.
    StreamingResponse와 함께 사용하기 위한 이터레이터를 반환한다.

    Args:
        key: R2 오브젝트 키

    Returns:
        (body_iterator, content_length, content_type) 튜플

    Raises:
        FileNotFoundError: 오브젝트가 존재하지 않는 경우
    """
    client = _get_client()
    try:
        response = client.get_object(Bucket=R2_BUCKET_NAME, Key=key)
        return (
            response["Body"].iter_chunks(chunk_size=64 * 1024),
            response.get("ContentLength", 0),
            response.get("ContentType", "application/octet-stream"),
        )
    except client.exceptions.NoSuchKey:
        raise FileNotFoundError(f"R2에서 파일을 찾을 수 없습니다: {key}")


def delete_object(key: str) -> bool:
    """
    R2에서 파일을 삭제한다.

    Args:
        key: R2 오브젝트 키

    Returns:
        삭제 성공 여부 (존재하지 않아도 True 반환)
    """
    client = _get_client()
    client.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
    return True


def copy_object(source_key: str, dest_key: str) -> str:
    """
    R2 내에서 파일을 복사한다. (rename 대체용: copy + delete)

    Args:
        source_key: 원본 오브젝트 키
        dest_key: 대상 오브젝트 키

    Returns:
        대상 오브젝트 키
    """
    client = _get_client()
    client.copy_object(
        Bucket=R2_BUCKET_NAME,
        CopySource={"Bucket": R2_BUCKET_NAME, "Key": source_key},
        Key=dest_key,
    )
    return dest_key


def exists(key: str) -> bool:
    """
    R2에 오브젝트가 존재하는지 확인한다.

    Args:
        key: R2 오브젝트 키

    Returns:
        존재 여부
    """
    client = _get_client()
    try:
        client.head_object(Bucket=R2_BUCKET_NAME, Key=key)
        return True
    except Exception:
        return False


def rename_object(old_key: str, new_key: str) -> str:
    """
    R2에서 파일 이름을 변경한다. (copy + delete 방식)

    Args:
        old_key: 기존 오브젝트 키
        new_key: 변경할 오브젝트 키

    Returns:
        변경된 오브젝트 키
    """
    if exists(old_key):
        copy_object(old_key, new_key)
        delete_object(old_key)
    return new_key
