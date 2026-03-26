/**
 * 시험문항 API 모듈
 * - 시험문항 CRUD 관련 API 호출 함수를 정의한다.
 * - 시험문항은 exam_key(SERIAL)로 식별된다.
 */
import api from './index';

const BASE_URL = '/api/v1/exam-list';

/**
 * 시험문항 목록 조회 (페이징/검색 파라미터 포함)
 * @param {Object} params - 검색 조건 (page, size, exam_type, topic_level, round 등)
 */
export function getList(params) {
  return api.get(BASE_URL, { params });
}

/**
 * 시험문항 상세 조회
 * @param {number} examKey - 시험키 PK
 */
export function getDetail(examKey) {
  return api.get(`${BASE_URL}/${examKey}`);
}

/**
 * 시험문항 생성
 * @param {Object} data - 생성할 시험문항 데이터
 */
export function create(data) {
  return api.post(BASE_URL, data);
}

/**
 * 시험문항 수정
 * @param {number} examKey - 수정 대상 시험키 PK
 * @param {Object} data - 수정할 데이터
 */
export function update(examKey, data) {
  return api.put(`${BASE_URL}/${examKey}`, data);
}

/**
 * 시험문항 삭제
 * @param {number} examKey - 삭제 대상 시험키 PK
 */
export function remove(examKey) {
  return api.delete(`${BASE_URL}/${examKey}`);
}
