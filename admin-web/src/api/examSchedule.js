/**
 * 시험일정 API 모듈
 * - tb_exam_schedule + tb_exam_location CRUD API 호출 함수를 정의한다.
 * - location은 schedule API에서 배열로 함께 처리한다.
 */
import api from './index';

const BASE_URL = '/api/v1/exam-schedule';

/**
 * 시험일정 목록 조회 (페이징/검색 파라미터 포함)
 * @param {Object} params - 검색 조건 (page, size, tpk_type)
 */
export function getList(params) {
  return api.get(BASE_URL, { params });
}

/**
 * 시험일정 단건 조회 (locations 포함)
 * @param {number} examKey - 시험일정 키
 */
export function getDetail(examKey) {
  return api.get(`${BASE_URL}/${examKey}`);
}

/**
 * 시험일정 등록 (locations 일괄 포함)
 * @param {Object} data - { tpk_type, round, locations: [{exam_region, test_date}] }
 */
export function create(data) {
  return api.post(BASE_URL, data);
}

/**
 * 시험일정 수정 (locations 전체 교체)
 * @param {number} examKey - 시험일정 키
 * @param {Object} data - { locations: [{exam_region, test_date}] }
 */
export function update(examKey, data) {
  return api.put(`${BASE_URL}/${examKey}`, data);
}

/**
 * 시험일정 삭제 (논리 삭제, locations 포함)
 * @param {number} examKey - 시험일정 키
 */
export function remove(examKey) {
  return api.delete(`${BASE_URL}/${examKey}`);
}
