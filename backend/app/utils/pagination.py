"""
페이지네이션 유틸리티 모듈
페이지 번호와 페이지 크기로부터 SQL LIMIT/OFFSET 값을 계산한다.
"""


def get_limit_offset(page: int = 1, size: int = 20) -> tuple[int, int]:
    """
    페이지 번호와 크기로부터 LIMIT, OFFSET 값을 계산한다.

    Args:
        page: 현재 페이지 번호 (1부터 시작)
        size: 페이지당 항목 수

    Returns:
        (limit, offset) 튜플
    """
    # 페이지 번호는 최소 1 이상
    if page < 1:
        page = 1
    # 페이지 크기는 최소 1, 최대 100
    if size < 1:
        size = 1
    elif size > 100:
        size = 100

    limit = size
    offset = (page - 1) * size
    return limit, offset
