/**
 * 코드 API 모듈
 * - 코드 CRUD 관련 API 호출 함수를 정의한다.
 * - 코드는 code_group + code 복합키로 식별된다.
 */
import api from './index';

const BASE_URL = '/api/v1/codes';

/**
 * 코드 목록 조회 (페이징/검색 파라미터 포함)
 * @param {Object} params - 검색 조건 (page, size, code_group, code_name 등)
 */
export function getList(params) {
  return api.get(BASE_URL, { params });
}

/**
 * 코드 상세 조회
 * @param {string} codeGroup - 그룹코드
 * @param {string} code - 코드
 */
export function getDetail(codeGroup, code) {
  return api.get(`${BASE_URL}/${codeGroup}/${code}`);
}

/**
 * 코드 생성
 * @param {Object} data - 생성할 코드 데이터
 */
export function create(data) {
  return api.post(BASE_URL, data);
}

/**
 * 코드 수정
 * @param {string} codeGroup - 그룹코드
 * @param {string} code - 코드
 * @param {Object} data - 수정할 데이터
 */
export function update(codeGroup, code, data) {
  return api.put(`${BASE_URL}/${codeGroup}/${code}`, data);
}

/**
 * 코드 삭제
 * @param {string} codeGroup - 그룹코드
 * @param {string} code - 코드
 */
export function remove(codeGroup, code) {
  return api.delete(`${BASE_URL}/${codeGroup}/${code}`);
}
