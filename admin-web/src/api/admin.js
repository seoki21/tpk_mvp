/**
 * 관리자 관리 API 모듈
 * - 관리자 CRUD 관련 API 호출 함수를 정의한다.
 */
import api from './index';

const BASE_URL = '/api/v1/admins';

/** 관리자 목록 조회 */
export function getList(params) {
  return api.get(BASE_URL, { params });
}

/** 관리자 생성 */
export function create(data) {
  return api.post(BASE_URL, data);
}

/** 관리자 수정 */
export function update(adminId, data) {
  return api.put(`${BASE_URL}/${adminId}`, data);
}

/** 관리자 삭제 */
export function remove(adminId) {
  return api.delete(`${BASE_URL}/${adminId}`);
}
