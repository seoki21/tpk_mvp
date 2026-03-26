import js from '@eslint/js';
import pluginVue from 'eslint-plugin-vue';
import prettierConfig from 'eslint-config-prettier';
import globals from 'globals';

export default [
  // 글로벌 무시 패턴
  {
    ignores: ['dist/**', 'node_modules/**']
  },

  // ESLint 권장 JS 규칙
  js.configs.recommended,

  // Vue 3 권장 규칙 (essential + strongly-recommended + recommended)
  ...pluginVue.configs['flat/recommended'],

  // Prettier 충돌 규칙 비활성화 (반드시 마지막에 위치)
  prettierConfig,

  // 프로젝트 커스텀 규칙
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node
      }
    },
    rules: {
      // === Vue 규칙 ===
      // 멀티 워드 컴포넌트 이름 강제 해제 (App.vue 등 단일 단어 허용)
      'vue/multi-word-component-names': 'off',

      // HTML 셀프 클로징 태그 설정
      'vue/html-self-closing': [
        'error',
        {
          html: { void: 'always', normal: 'never', component: 'always' },
          svg: 'always',
          math: 'always'
        }
      ],

      // 속성 순서 강제 (가독성)
      'vue/attributes-order': ['warn', { alphabetical: false }],

      // SFC 블록 순서: script → template → style
      'vue/block-order': [
        'error',
        {
          order: ['script', 'template', 'style']
        }
      ],

      // === JS 규칙 ===
      // console.log 허용 (MVP 단계에서는 디버깅에 유용)
      'no-console': 'off',

      // 미사용 변수 — 경고로 처리하되 _로 시작하는 변수는 허용
      'no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_'
        }
      ],

      // var 금지 — const/let만 사용
      'no-var': 'error',

      // 가능한 경우 const 사용 강제
      'prefer-const': 'warn'
    }
  }
];
