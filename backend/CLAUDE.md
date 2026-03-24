# API 서버 개발 지침

> 루트 [CLAUDE.md](../CLAUDE.md)의 공통 제약사항을 반드시 준수할 것

## 기술 스택

- **Framework**: Python FastAPI
- **DB 드라이버**: psycopg v3 (ORM 미사용, SQL 직접 작성)
- **인증**: python-jose (JWT)
- **입력 검증**: Pydantic v2

## 디렉토리 구조

```
backend/
├── app/
│   ├── main.py          # FastAPI 앱 진입점, 미들웨어/라우터 등록
│   ├── config.py         # 환경변수 로드 및 설정값 관리
│   ├── database.py       # psycopg DB 커넥션 관리
│   ├── routers/          # API 라우터 (도메인별 분리)
│   ├── services/         # 비즈니스 로직 (라우터에서 호출)
│   ├── models/           # Pydantic 요청/응답 스키마
│   └── utils/            # 공통 유틸리티 (인증, 페이징 등)
├── requirements.txt
├── .env                  # 환경변수 (git 미추적)
└── CLAUDE.md
```

## 개발 서버 실행

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 코딩 규칙

### SQL 작성

- **파라미터 바인딩 필수**: `%s` 플레이스홀더 + 튜플 파라미터 사용. f-string이나 문자열 포맷으로 SQL에 값을 삽입하지 않는다.
- 쿼리가 길 경우 여러 줄 문자열(`"""`)로 작성하고, 각 절(SELECT, FROM, WHERE 등)을 줄바꿈한다.
- SQL 쿼리 위에 한글 주석으로 쿼리의 목적을 설명한다.
- CUD(INSERT/UPDATE/DELETE) 후 RETURNING 대신 get 함수로 재조회하여 TO_CHAR 포맷 포함된 결과를 반환한다.

```python
# 사용자 ID로 학습 이력 조회 (최근 순 정렬)
cursor.execute(
    """
    SELECT history_id, exam_id, score, completed_at
      FROM user_history
     WHERE user_id = %s
     ORDER BY completed_at DESC
     LIMIT %s OFFSET %s
    """,
    (user_id, limit, offset),
)
```

### API 응답 형식

- 성공 응답: `{ "data": ..., "message": "..." }`
- 목록 응답: `{ "data": [...], "total": 100, "page": 1, "size": 20 }` (size: 10/20/50 지원)
- 에러 응답: `{ "detail": "에러 메시지" }` (FastAPI HTTPException 사용)
- 날짜/시간 필드 포맷: `YYYY-MM-DD HH24:MI:SS` (예: 2026-03-17 15:20:04)

### 라우터 구성

- 도메인별로 라우터 파일 분리 (예: `routers/users.py`, `routers/exams.py`)
- URL 접두사: `/api/v1/{도메인}`
- 라우터 함수에 한글 docstring 작성

### 에러 처리

- DB 에러는 try/except로 잡아서 적절한 HTTP 상태 코드로 변환
- 400: 잘못된 요청 / 401: 인증 실패 / 403: 권한 없음 / 404: 리소스 없음 / 500: 서버 내부 오류

## 환경변수

| 변수명                 | 설명                   | 예시                        |
| ---------------------- | ---------------------- | --------------------------- |
| `DB_HOST`            | DB 서버 호스트         | `59.19.146.192`           |
| `DB_PORT`            | DB 서버 포트           | `5432`                    |
| `DB_NAME`            | 데이터베이스명         | `tpk_db`                  |
| `DB_USER`            | DB 사용자              | `tpk`                     |
| `DB_PASSWORD`        | DB 비밀번호            | (비밀번호)                  |
| `DB_SCHEMA`          | DB 스키마              | `public`                  |
| `JWT_SECRET_KEY`     | JWT 서명 비밀키        | (임의 문자열)               |
| `JWT_EXPIRE_MINUTES` | JWT 만료 시간(분)      | `60`                      |

> `config.py`에서 개별 환경변수를 조합하여 `DATABASE_URL`을 생성한다.
