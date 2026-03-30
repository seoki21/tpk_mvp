/**
 * 인증 API 모듈
 * - 관리자 로그인/현재 사용자 조회 API 호출 함수를 정의한다.
 */
import api from './index';

/**
 * 관리자 로그인
 * @param {string} adminId - 관리자 ID
 * @param {string} password - 비밀번호
 */
export function login(adminId, password) {
  return api.post('/api/v1/auth/login', { admin_id: adminId, password });
}

/**
 * 현재 로그인한 관리자 정보 조회
 */
export function getMe() {
  return api.get('/api/v1/auth/me');
}
