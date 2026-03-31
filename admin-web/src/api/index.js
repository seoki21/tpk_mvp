/**
 * Axios 인스턴스 설정
 * - 개발 환경에서는 Vite 프록시를 사용하므로 baseURL을 빈 문자열로 설정
 * - 운영 환경에서는 VITE_API_BASE_URL 환경변수를 사용
 * - 요청 인터셉터: Authorization 헤더에 JWT 토큰 첨부
 * - 응답 인터셉터: response.data를 자동 언래핑, 401 시 로그인 리다이렉트
 */
import axios from 'axios';
import NProgress from 'nprogress';

/** 진행 중인 API 요청 수 (다중 요청 시 모두 완료될 때까지 프로그레스바 유지) */
let activeRequests = 0;

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

/* 요청 인터셉터 — JWT 토큰 첨부 + 프로그레스바 시작 */
api.interceptors.request.use((config) => {
  /* skipProgress 옵션이 없으면 프로그레스바 표시 (폴링 등 제외용) */
  if (!config.skipProgress) {
    if (activeRequests === 0) NProgress.start();
    activeRequests++;
  }

  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/** 응답 완료 시 프로그레스바 카운터 감소 (성공/실패 공통) */
function finishProgress(config) {
  if (!config?.skipProgress) {
    activeRequests = Math.max(activeRequests - 1, 0);
    if (activeRequests === 0) NProgress.done();
  }
}

/* 응답 인터셉터 — response.data만 반환하여 호출부에서 편리하게 사용 */
api.interceptors.response.use(
  (response) => {
    finishProgress(response.config);
    return response.data;
  },
  (error) => {
    finishProgress(error.config);
    console.error('[API Error]', error.response?.status, error.response?.data || error.message);

    /* 401 인증 실패 시 토큰 제거 후 로그인 페이지로 이동 */
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_info');
      /* 이미 로그인 페이지에 있으면 리다이렉트하지 않음 */
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    /* 서버 에러 응답에서 detail 메시지를 추출하여 error.detail에 설정 */
    const detail = error.response?.data?.detail || error.message || '알 수 없는 오류';
    error.detail = detail;
    return Promise.reject(error);
  }
);

export default api;
