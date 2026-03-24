/**
 * 관리자 웹 앱 진입점
 * Vue, Pinia, Router, i18n을 초기화하고 앱을 마운트한다.
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import router from './router'
import App from './App.vue'
import './assets/main.css'

import ko from './locales/ko.json'

/* vue-i18n 설정 — 관리자 화면은 한국어 고정 */
const i18n = createI18n({
  legacy: false,
  locale: 'ko',
  fallbackLocale: 'ko',
  messages: { ko }
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.mount('#app')
