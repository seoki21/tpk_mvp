# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 프로젝트 기획/설계 상세는 [PLAN.md](./PLAN.md) 참조

## 기술 스택

- **Backend**: Python FastAPI
- **Frontend**: Tailwind CSS 기반 Vue.js + Vite + Pinia + Vue Router
- **Database**: PostgreSQL (원격 개발 DB 서버)
- **i18n**: vue-i18n (사용자 웹 전용)

## 핵심 제약사항

- DB 접근은 ORM을 사용하지 않는다. psycopg(v3)로 SQL을 직접 작성한다.
- 시험 문제 본문/선택지는 다국어 번역하지 않는다 (한국어 원문 유지).
- **사용자 웹(user-web)**: UI 텍스트는 반드시 vue-i18n 리소스 파일을 통해 다국어 처리한다. 하드코딩 금지.
- **관리자 웹(admin-web)**: 다국어를 사용하지 않는다. 한국어를 직접 작성한다.
- 코드에 한글 주석을 상세하게 작성한다. (함수 목적/파라미터, SQL 쿼리 의도, 복잡한 로직, Vue 컴포넌트 역할)

## 디렉토리 구조

```
tpk_mvp/
├── backend/          # FastAPI 백엔드 API 서버
├── user-web/         # 사용자 웹 (Vue.js)
├── admin-web/        # 관리자 웹 (Vue.js)
└── db_specs/         # DB 접속정보 및 테이블 명세서
```

> 각 폴더별 상세 지침은 해당 폴더의 CLAUDE.md 참조

## 개발 환경 명령어 (Windows Git Bash)

```bash
# API 서버 (포트 8001 사용)
cd backend
source venv/Scripts/activate
uvicorn app.main:app --reload --port 8001

# 관리자 웹 (pnpm 사용 — corepack 경유)
cd admin-web
corepack pnpm install
corepack pnpm run dev

# 사용자 웹
cd user-web
corepack pnpm install
corepack pnpm run dev
```

## 코드 품질 (ESLint / Prettier)

- ESLint v9 flat config + Prettier가 admin-web에 설정되어 있다.
- Prettier 설정(`.prettierrc`)은 프로젝트 루트에 위치하여 양쪽 프론트엔드에서 공유한다.
- Tailwind CSS 클래스 자동 정렬: `prettier-plugin-tailwindcss`

```bash
cd admin-web
corepack pnpm run lint        # 코드 품질 검사
corepack pnpm run lint:fix    # 자동 수정
corepack pnpm run format      # 코드 포매팅
```

## 환경변수

- API 서버 환경변수 (DB 접속정보, `JWT_SECRET_KEY` 등): `backend/.env`
- 테이블 명세서: `db_specs/tpk_table_spec_<yyyymmdd>.xlsx`

## DB 스크립트

- 테이블 생성: `db_specs/create_tables.py`
- 테이블/컬럼 코멘트 적용: `db_specs/add_comments.py`

## 핵심기능

- 관리자 WEB (`admin-web/`)
  - 사용자 관리
  - 시험관리(기출) — PDF 파일 업로드 포함 (`tb_exam_file`)
  - 기출문제 관리 — 기출문항 변환(JSON) 팝업 포함 (Claude API 연동)
  - 연습문제 관리
  - 문항구조 관리
  - 문항유형 관리
  - 그룹코드 관리
  - 코드 관리
- 사용자 WEB (`user-web/`)
  - 학습 대시보드
  - 시험문제(기출 및 모의)
  - 연습문제

## AI 연동

- **Claude API** (Anthropic): `anthropic` Python SDK 사용 (`AsyncAnthropic` 비동기 클라이언트)
- 기출문항 PDF → JSON 변환: PDF를 Claude API로 분석하여 문제/지시문 JSON 생성
  - SSE(Server-Sent Events) 스트리밍으로 실시간 결과 전달
  - `max_tokens: 64000`, 프론트엔드 타임아웃: 300초
- AI 피드백: 학습 문제에 대한 AI 기반 피드백 생성
- 환경변수: `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (`backend/.env`)
