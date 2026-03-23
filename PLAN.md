# TOPIK MVP - 프로젝트 계획서

## 프로젝트 개요

TOPIK(한국어능력시험) 기출문제 및 모의문제를 제공하고, 사용자의 풀이 과정에 대해 피드백을 제공하는 다국어 지원 웹 애플리케이션.

## 기술 스택

| 구분         | 기술                           |
| ------------ | ------------------------------ |
| Backend      | Python FastAPI                 |
| Frontend     | Tailwind CSS, Vue.js (Web UI)  |
| Database     | PostgreSQL (원격 개발 DB 서버) |
| DB 접근      | SQL 직접 작성 (ORM 미사용)     |
| API 문서     | Swagger UI (FastAPI 내장)      |
| 다국어(i18n) | vue-i18n                       |

## 다국어 지원 (i18n)

### 기본 방침

- UI 텍스트(메뉴, 버튼, 안내 문구 등)는 모두 다국어 리소스 파일로 관리
- vue-i18n을 사용하여 런타임 언어 전환 지원
- 언어 리소스 파일은 JSON 형식으로 `frontend/src/locales/` 하위에 언어별 분리
- 사용자가 선택한 언어는 localStorage에 저장하여 재방문 시 유지
- UI 화면 상단에 다국어 변경 버튼이 필요함(selectbox, '한국어/영어/일본어')

### MVP 지원 언어

| 코드   | 언어    | 비고      |
| ------ | ------- | --------- |
| `ko` | 한국어  | 기본 언어 |
| `en` | English |           |
| `ja` | 日本語  |           |

### 다국어 대상 구분

구분다국어 적용비고UI 텍스트 (메뉴, 버튼, 라벨, 안내 문구)Ovue-i18n 리소스 파일시험 문제 본문 / 선택지X한국어 원문 그대로 제공 (TOPIK 시험 특성)문제 해설 / 피드백O사용자 언어에 따라 적용

## 데이터 모델

- 개발 DB서버 접속정보는 /db_specs/.env 파일
- 테이블명세서는 /db_specs/<project_name>_table_spec_ `<yyyymmdd>`.xlsx 임

## 핵심 기능

본 프로그램은 **사용자 웹**과 **관리자 웹**으로 구분된다.

## 구현 순서

> ### Phase 1 — 프로젝트 셋업 (1~2일)
>
> * [ ] Vite + Vue.js 3 프로젝트 초기화 (user-web, admin-web)
> * [ ] Tailwind CSS 설정
> * [ ] 라우터 설정 (Vue Router 4)
> * [ ] 폴더 구조 확정 (`/views`, `/components`, `/stores`, `/composables`, `/api`, `/locales`)
> * [ ] ESLint / Prettier 설정
> * [ ] GitHub 저장소 생성 및 초기 커밋
> * [ ] 개발환경 DB 접속하여 Table 생성
>
> ### Phase 2 — 문제 데이터 구조 설계 (1일)
>
> * [ ] 문제 JSON 스키마 정의
>
> ```
>   { id, level(1~6), section(어휘/문법/읽기/듣기/쓰기),
>     question, options[], answer, explanation, source }
> ```
>
> * [ ] 샘플 문제 10~20개 직접 입력 (정식 데이터 전 임시)
> * [ ] 로컬 JSON 파일로 관리
>
> ### Phase 3 — 다국어(i18n) 기반 구축 (1일)
>
> * [ ] `vue-i18n` 설치 및 설정
> * [ ] 지원 언어 1차: 한국어(ko), 영어(en), 일본어(ja)
> * [ ] UI 문자열 번역 파일(`src/locales/`) 작성
> * [ ] 언어 전환 컴포넌트 구현
>
> ### Phase 4 — 핵심 UI 페이지 구현 (2~3일)
>
> * [ ] 관리자 WEB
>   * 사용자 관리, 사용자 학습 이력, 문항구조 관리, 문항유형 관리, 시험문항 관리, 연습문항 관리, 그룹코드 관리, 코드 관리
> * [ ] 사용자 WEB
>   * 시험문제(기출 및 모의), 연습문제
>
> ### Phase 5 — 배포 (1일)
>
> * [ ] Vercel 또는 Netlify 배포
> * [ ] 환경변수 설정 (API Key 등)
> * [ ] 기본 SEO 메타태그 추가
>
> **결과물** : 동작하는 웹앱, 3개 언어 지원, AI 피드백, 배포 완료환경 설정

> 개발 환경 명령어 및 환경변수는 [CLAUDE.md](./CLAUDE.md) 참조
