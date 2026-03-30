/**
 * 인증 Pinia 스토어
 * - 로그인/로그아웃 상태, JWT 토큰, 관리자 정보를 관리한다.
 * - localStorage에 토큰과 관리자 정보를 영속 저장한다.
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import * as authApi from '@/api/auth';

export const useAuthStore = defineStore('auth', () => {
  /* ========== 상태 ========== */

  /** JWT 액세스 토큰 */
  const token = ref(localStorage.getItem('admin_token') || '');

  /** 로그인한 관리자 정보 { admin_id, roles } */
  const adminInfo = ref(JSON.parse(localStorage.getItem('admin_info') || 'null'));

  /* ========== 계산된 속성 ========== */

  /** 로그인 여부 */
  const isLoggedIn = computed(() => !!token.value);

  /** 관리자 ID */
  const adminId = computed(() => adminInfo.value?.admin_id || '');

  /** 권한 목록 */
  const roles = computed(() => adminInfo.value?.roles || []);

  /** SUPER 권한 여부 */
  const isSuper = computed(() => roles.value.includes('SUPER'));

  /* ========== 액션 ========== */

  /**
   * 로그인 — ID/비밀번호로 JWT 토큰을 발급받고 저장한다.
   * @param {string} adminId - 관리자 ID
   * @param {string} password - 비밀번호
   */
  async function login(id, password) {
    const res = await authApi.login(id, password);
    const data = res.data;

    token.value = data.access_token;
    adminInfo.value = { admin_id: data.admin_id, roles: data.roles };

    localStorage.setItem('admin_token', data.access_token);
    localStorage.setItem('admin_info', JSON.stringify(adminInfo.value));

    return data;
  }

  /** 로그아웃 — 토큰과 관리자 정보를 제거한다. */
  function logout() {
    token.value = '';
    adminInfo.value = null;
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_info');
  }

  return {
    token,
    adminInfo,
    isLoggedIn,
    adminId,
    roles,
    isSuper,
    login,
    logout
  };
});
