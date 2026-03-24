/**
 * Axios 인스턴스 설정
 * - 개발 환경에서는 Vite 프록시를 사용하므로 baseURL을 빈 문자열로 설정
 * - 운영 환경에서는 VITE_API_BASE_URL 환경변수를 사용
 * - 응답 인터셉터: response.data를 자동 언래핑
 * - 에러 인터셉터: 콘솔에 에러 로깅 후 reject
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/* 응답 인터셉터 — response.data만 반환하여 호출부에서 편리하게 사용 */
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('[API Error]', error.response?.status, error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api
