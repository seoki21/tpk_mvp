# 사용자 웹 개발 지침

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
user-web/
├── src/
│   ├── main.js           # 앱 진입점 (Vue, Pinia, Router, i18n 초기화)
│   ├── App.vue           # 루트 컴포넌트
│   ├── router/           # Vue Router 라우트 정의
│   │   └── index.js
│   ├── stores/           # Pinia 스토어 (도메인별 분리)
│   ├── views/            # 페이지 단위 컴포넌트
│   ├── components/       # 재사용 가능한 공통 컴포넌트
│   ├── composables/      # Vue 컴포저블 (재사용 로직)
│   ├── api/              # API 호출 모듈 (axios 등)
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
cd user-web
npm install
npm run dev
```

## 코딩 규칙

### Vue 컴포넌트
- **Composition API + `<script setup>`** 문법을 사용한다.
- 컴포넌트 파일 상단에 한글 주석으로 컴포넌트의 역할을 설명한다.
- 단일 파일 컴포넌트(SFC) 순서: `<script setup>` → `<template>` → `<style>`

```vue
<!-- 시험 문제 목록을 표시하는 컴포넌트 -->
<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
// ...
</script>

<template>
  <div>
    <h1>{{ t('exam.title') }}</h1>
  </div>
</template>
```

### 다국어 (i18n)
- **모든 UI 텍스트는 반드시 `t()` 함수를 통해 출력한다.** 템플릿에 한글/영문/일문을 직접 쓰지 않는다.
- i18n 키는 도트 표기법으로 계층 구분: `exam.title`, `common.submit`
- 시험 문제 본문/선택지는 번역하지 않고 한국어 원문 그대로 표시한다.
- 새 페이지/컴포넌트 추가 시 ko.json, en.json, ja.json 세 파일 모두에 키를 추가한다.

### API 호출
- `src/api/` 디렉토리에 도메인별로 API 호출 함수를 모듈화한다.
- API 베이스 URL은 환경변수(`VITE_API_BASE_URL`)로 관리한다.

### 라우팅
- 페이지 컴포넌트는 `views/` 에 배치한다.
- 라우트 경로에 lazy loading (`() => import(...)`)을 사용한다.

### 상태 관리
- Pinia 스토어는 도메인별로 분리한다 (예: `stores/exam.js`, `stores/user.js`).
- 서버 상태와 UI 상태를 구분하여 관리한다.
