/**
 * 관리자 웹 앱 진입점
 * Vue, Pinia, Router를 초기화하고 앱을 마운트한다.
 */
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import router from './router';
import App from './App.vue';
import './assets/main.css';

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount('#app');
