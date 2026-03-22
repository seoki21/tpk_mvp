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

## 개발 환경 명령어 (Windows Git Bash)

```bash
# Backend
cd backend
source venv/Scripts/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 환경변수

- 개발 DB서버 접속정보: `/db_specs/.env`
- 테이블 명세서: `/db_specs/<project_name>_table_spec_<yyyymmdd>.xlsx`
- Backend 앱 환경변수 (`DATABASE_URL`, `JWT_SECRET_KEY` 등)는 Backend `.env` 파일에 설정

## 디렉토리 구조

> 추후 확정 예정

## API 엔드포인트 설계

> 추후 기능 확정 후 작성 예정
