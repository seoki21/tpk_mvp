# 관리자 웹 개발 지침

> 루트 [CLAUDE.md](../CLAUDE.md)의 공통 제약사항을 반드시 준수할 것

## 기술 스택

- **Framework**: Vue.js 3 (Composition API)
- **빌드**: Vite
- **상태 관리**: Pinia
- **라우팅**: Vue Router 4
- **스타일**: Tailwind CSS
- **다국어**: vue-i18n

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

### 관리 대상 기능
- 사용자 관리
- 사용자 학습 이력
- 문항구조 관리
- 문항유형 관리
- 시험문항 관리
- 연습문항 관리
- 그룹코드 관리
- 코드 관리

### 다국어 (i18n)
- **모든 UI 텍스트는 반드시 `t()` 함수를 통해 출력한다.** 템플릿에 한글/영문/일문을 직접 쓰지 않는다.
- i18n 키는 도트 표기법으로 계층 구분: `admin.user.title`, `common.save`
- 새 페이지/컴포넌트 추가 시 ko.json, en.json, ja.json 세 파일 모두에 키를 추가한다.

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
