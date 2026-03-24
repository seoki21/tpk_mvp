# 관리자 웹 개발 지침

> 루트 [CLAUDE.md](../CLAUDE.md)의 공통 제약사항을 반드시 준수할 것

## 기술 스택

- **Framework**: Vue.js 3 (Composition API)
- **빌드**: Vite
- **상태 관리**: Pinia
- **라우팅**: Vue Router 4
- **스타일**: Tailwind CSS
- **다국어**: vue-i18n (한국어 고정, 구조만 유지)

## 디렉토리 구조

```
admin-web/
├── src/
│   ├── main.js           # 앱 진입점 (Vue, Pinia, Router, i18n 초기화)
│   ├── App.vue           # 루트 컴포넌트
│   ├── router/           # Vue Router 라우트 정의
│   │   └── index.js
│   ├── stores/           # Pinia 스토어 (도메인별 분리)
│   ├── views/            # 페이지 단위 컴포넌트
│   ├── components/       # 재사용 가능한 공통 컴포넌트
│   ├── composables/      # Vue 컴포저블 (재사용 로직)
│   ├── api/              # API 호출 모듈
│   └── locales/          # i18n 번역 리소스
│       ├── ko.json       # 한국어 (기본)
│       ├── en.json       # English
│       └── ja.json       # 日本語
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── CLAUDE.md
```

## 개발 서버 실행

```bash
cd admin-web
npm install
npm run dev
```

## 코딩 규칙

### Vue 컴포넌트

- **Composition API + `<script setup>`** 문법을 사용한다.
- 컴포넌트 파일 상단에 한글 주석으로 컴포넌트의 역할을 설명한다.
- 단일 파일 컴포넌트(SFC) 순서: `<script setup>` → `<template>` → `<style>`

### 관리자 전용 규칙

- 모든 관리자 페이지는 인증 가드(navigation guard)를 통해 접근 제어한다.
- 목록 페이지는 테이블 형태로 구성하며, 페이징/검색/정렬을 지원한다.
- 등록/수정 폼은 입력 검증 후 API를 호출한다.
- 삭제 작업은 반드시 확인 다이얼로그를 표시한 후 실행한다.
- 날짜/시간 표시 포맷: `YYYY-MM-DD HH24:MI:SS` (예: 2026-03-17 15:20:04)
- 조회 테이블 상단 바: 좌측에 `조회목록(총 N건)` 표시, 우측에 페이지당 행 수 선택 selectbox (10개, 20개, 50개, 기본 20개).
- 삭제여부(del_yn) 컬럼 표시 규칙: `N` → 공백, `Y` → 빨간색 폰트로 '삭제' 표시.
- 테이블 컬럼 헤더 클릭 시 오름차순/내림차순 정렬 (클라이언트 사이드). `sortable: false`로 특정 컬럼 정렬 비활성화 가능.
- API 에러 발생 시 서버 응답의 `detail` 메시지를 alert 팝업으로 표시한다 (예: "이미 존재하는 그룹코드입니다."). 공통 Axios 인터셉터(`api/index.js`)에서 `error.detail`로 추출.

### 공통 화면 Layout

* 전체 레이아웃: 헤더(상단) + 사이드바(좌측, 다크 테마) + 콘텐츠(우측)
  * 사이드바: 접기/펼치기 토글 지원 (헤더 ☰ 버튼). 접힘 시 아이콘만, 펼침 시 아이콘+텍스트.
* 공통 조회 레이아웃 : TPK_MVP/admin-web/layout_image/common_search_layout.png
  * 서브 타이틀, 조회 조건(SearchBar), 테이블 리스트(DataTable), 페이징 바(Pagination)로 구성
  * SearchBar에 `hide-register` prop으로 등록 버튼 숨김 가능 (조회 전용 화면에서 사용)
* 공통 팝업 레이아웃 : TPK_MVP/admin-web/layout_image/common_popup_layout.png

노트 : 화면의 정의되어 있지 않는 경우 그룹코드 레이아웃과 유사항 패턴으로 생성한다.

### 화면

- 사용자 관리
  - 사용자 목록과 사용자 이력으로 구분된 형태
    ![1774348670909](image/CLAUDE/1774348670909.png)
  - 사용자 목록 : 현재 구현된 부분을 그대로 적용(생성시간 컬럼은 visiable=false)
  - 사용자 이력 : <일단 비워둘 것>
- 문항구조 관리
- 문항유형 관리
- 시험문항 관리
  - 검색화면 정의 : 시험유형, 회차
  - | 컬럼명   | UI 컨트롤 | 관련 TABLE                 | 검색조건          |
    | 시험유형 | selectbox | tb_group_code의 group_code='exam_type' |                   |
    | 토픽레벨 | selectbox | tb_group_code의 group_code='tpk_level' |                   |
    | 회차   | text      | tb_exam_list의 round | like %round% |
  - 조회 화면 컬럼 정의 : | 년도 | 시험유형 | 토픽레벨 | 회차 | 삭제여부 | 생성자 | 생성시간 |
  - | 컬럼명   | 관련 TABLE                 |
    | -------- | -------------------------- |
    | 시험유형 | tb_exam_list의 exam_type으로 tb_group_code의 group_code='exam_type'의 group_name |
    | 년도 | tb_exam_list의 exam_year|'년' |
    | 회차 | tb_exam_list의 round |
    | 토픽레벨 | tb_exam_list의 topik_level로 tb_group_code의 group_code='tpk_level'의 group_name |
    | 영역 | tb_exam_list의 section으로 tb_group_code의 group_code='section'의 group_name |

- 연습문항 관리
- 그룹코드 관리
  - 검색화면 정의 : 그룹코드, 코드명
  - | 컬럼명   | UI 컨트롤 | 관련 TABLE                 | 검색조건          |
    | -------- | --------- | -------------------------- | ----------------- |
    | 그룹코드 | selectbox | tb_group_code의 group_code |                   |
    | 코드명   | text      | tb_group_code의 group_name | like %group_name% |
  - 조회 화면 컬럼 정의 : 그룹코드 | 코드명 | 코드설명 | 삭제여부 | 생성자 | 생성시간 |
  - | 컬럼명   | 관련 TABLE                 |
    | -------- | -------------------------- |
    | 그룹코드 | tb_group_code의 group_code |
    | 코드명   | tb_group_code의 group_name |
    | 코드설명 | tb_group_code의 group_desc |
    | 삭제여부 | tb_group_code의 del_yn     |
  - 소팅 순서 : del_yn ASC, group_name ASC
- 코드 관리

  - 조회 화면 컬럼 정의 : 그룹코드 | 그룹코드명 | 코드 | 코드명 | 코드설명 | 소팅순서 | 삭제여부 | 생성자 | 생성시간 |
  - | 컬럼명     | 관련 TABLE                 |
    | ---------- | -------------------------- |
    | 그룹코드   | tb_group_code의 group_code |
    | 그룹코드명 | tb_group_code의 group_name |
    | 코드       | tb_code의 code             |
    | 코드명     | tb_code의 code_name        |
    | 코드설명   | tb_code의 code_desc        |
    | 삭제여부   | tb_code의 del_yn           |
  - 소팅 순서 : del_yn ASC, group_code ASC, sort_order ASC

### 다국어 (i18n)

- **모든 UI 텍스트는 반드시 `t()` 함수를 통해 출력한다.** 템플릿에 한글을 직접 쓰지 않는다.
- i18n 키는 도트 표기법으로 계층 구분: `admin.user.title`, `common.save`
- 새 페이지/컴포넌트 추가 시 ko.json에 키를 추가한다 (관리자 화면은 한국어 고정).

### API 호출

- `src/api/` 디렉토리에 도메인별로 API 호출 함수를 모듈화한다.
- API 베이스 URL은 환경변수(`VITE_API_BASE_URL`)로 관리한다.

### 라우팅

- 페이지 컴포넌트는 `views/` 에 배치한다.
- 라우트 경로에 lazy loading (`() => import(...)`)을 사용한다.
- 관리자 인증이 필요한 라우트에는 `meta: { requiresAuth: true }`를 설정한다.

### 상태 관리

- Pinia 스토어는 도메인별로 분리한다.
- 인증 상태는 `stores/auth.js`에서 관리한다.
- 스토어의 fetchList에서 빈 문자열 검색 파라미터는 필터링 후 API에 전달한다 (FastAPI Optional 타입 파싱 오류 방지).
