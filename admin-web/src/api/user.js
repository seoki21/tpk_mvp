/**
 * 사용자 API 모듈
 * - 사용자 목록 조회 API 호출 함수를 정의한다.
 */
import api from './index'

const BASE_URL = '/api/v1/users'

/**
 * 사용자 목록 조회 (페이징/검색 파라미터 포함)
 * @param {Object} params - 검색 조건 (page, size, email 등)
 */
export function getList(params) {
  return api.get(BASE_URL, { params })
}
