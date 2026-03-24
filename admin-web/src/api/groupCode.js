/**
 * 그룹코드 API 모듈
 * - 그룹코드 CRUD 관련 API 호출 함수를 정의한다.
 * - 모든 요청은 공통 Axios 인스턴스를 사용한다.
 */
import api from './index'

const BASE_URL = '/api/v1/group-codes'

/**
 * 그룹코드 목록 조회 (페이징/검색 파라미터 포함)
 * @param {Object} params - 검색 조건 (page, size, group_code, group_name 등)
 */
export function getList(params) {
  return api.get(BASE_URL, { params })
}

/**
 * 전체 그룹코드 목록 조회 (셀렉트박스 등에서 사용)
 */
export function getAll() {
  return api.get(`${BASE_URL}/all`)
}

/**
 * 그룹코드 상세 조회
 * @param {string} groupCode - 그룹코드 PK
 */
export function getDetail(groupCode) {
  return api.get(`${BASE_URL}/${groupCode}`)
}

/**
 * 그룹코드 생성
 * @param {Object} data - 생성할 그룹코드 데이터
 */
export function create(data) {
  return api.post(BASE_URL, data)
}

/**
 * 그룹코드 수정
 * @param {string} groupCode - 수정 대상 그룹코드 PK
 * @param {Object} data - 수정할 데이터
 */
export function update(groupCode, data) {
  return api.put(`${BASE_URL}/${groupCode}`, data)
}

/**
 * 그룹코드 삭제
 * @param {string} groupCode - 삭제 대상 그룹코드 PK
 */
export function remove(groupCode) {
  return api.delete(`${BASE_URL}/${groupCode}`)
}
