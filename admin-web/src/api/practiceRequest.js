/**
 * 연습문제 생성 요청 API 모듈
 * tb_practice_request 테이블에 대한 CRUD API 호출 함수를 정의한다.
 */
import api from './index';

const BASE_URL = '/api/v1/practice-request';

/**
 * 연습문제 생성 요청 목록 조회
 * @param {Object} params - 검색 조건 (page, size, exam_type, tpk_level, section, gen_method, status)
 */
export function getList(params) {
  return api.get(BASE_URL, { params });
}

/**
 * 연습문제 생성 요청 등록
 * @param {Object} data - 등록 데이터
 */
export function create(data) {
  return api.post(BASE_URL, data);
}

/**
 * 연습문제 생성 요청 수정
 * @param {number} requestKey - 요청 PK
 * @param {Object} data - 수정 데이터
 */
export function update(requestKey, data) {
  return api.put(`${BASE_URL}/${requestKey}`, data);
}

/**
 * 연습문제 생성 요청 삭제
 * @param {number} requestKey - 요청 PK
 */
export function remove(requestKey) {
  return api.delete(`${BASE_URL}/${requestKey}`);
}
