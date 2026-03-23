# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 프로젝트 기획/설계 상세는 [PLAN.md](./PLAN.md) 참조

## 기술 스택

- **Backend**: Python FastAPI
- **Frontend**: Tailwind CSS 기반 Vue.js + Vite + Pinia + Vue Router
- **Database**: PostgreSQL (원격 개발 DB 서버)
- **i18n**: vue-i18n

## 핵심 제약사항

- DB 접근은 ORM을 사용하지 않는다. psycopg2로 SQL을 직접 작성한다.
- 시험 문제 본문/선택지는 다국어 번역하지 않는다 (한국어 원문 유지).
- UI 텍스트는 반드시 vue-i18n 리소스 파일을 통해 다국어 처리한다. 하드코딩 금지.
- 코드에 한글 주석을 상세하게 작성한다. (함수 목적/파라미터, SQL 쿼리 의도, 복잡한 로직, Vue 컴포넌트 역할)

## 디렉토리 구조

```
tpk_mvp/
├── api/              # FastAPI 백엔드 API 서버
├── user-web/         # 사용자 웹 (Vue.js)
├── admin-web/        # 관리자 웹 (Vue.js)
└── db_specs/         # DB 접속정보 및 테이블 명세서
```

> 각 폴더별 상세 지침은 해당 폴더의 CLAUDE.md 참조

## 개발 환경 명령어 (Windows Git Bash)

```bash
# API 서버
cd api
source venv/Scripts/activate
uvicorn app.main:app --reload

# 사용자 웹
cd user-web
npm install
npm run dev

# 관리자 웹
cd admin-web
npm install
npm run dev
```

## 환경변수

- API 서버 환경변수 (DB 접속정보, `JWT_SECRET_KEY` 등): `api/.env`
- 테이블 명세서: `db_specs/tpk_table_spec_<yyyymmdd>.xlsx`

## DB 스크립트

- 테이블 생성: `db_specs/create_tables.py`
- 테이블/컬럼 코멘트 적용: `db_specs/add_comments.py`

## 핵심기능

- 관리자 WEB (`admin-web/`)
  - 사용자 관리
  - 사용자 학습 이력
  - 문항구조 관리
  - 문항유형 관리
  - 시험문항 관리
  - 연습문항 관리
  - 그룹코드 관리
  - 코드 관리
- 사용자 WEB (`user-web/`)
  - 학습 대시보드
  - 시험문제(기출 및 모의)
  - 연습문제
