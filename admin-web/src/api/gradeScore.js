/**
 * 등급 관리 API 모듈
 * - tb_grade_score CRUD API 호출 함수를 정의한다.
 * - 복합 PK (tpk_type, tpk_level, tpk_grade)로 단건을 식별한다.
 */
import api from './index';

const BASE_URL = '/api/v1/grade-score';

/**
 * 등급 목록 전체 조회 (시험종류 필터 선택)
 * @param {Object} params - 검색 조건 (tpk_type)
 */
export function getList(params) {
  return api.get(BASE_URL, { params });
}

/**
 * 등급 단건 조회
 * @param {number} tpkType - 시험종류 코드
 * @param {number} tpkLevel - 토픽레벨 코드
 * @param {number} tpkGrade - 등급
 */
export function getDetail(tpkType, tpkLevel, tpkGrade) {
  return api.get(`${BASE_URL}/${tpkType}/${tpkLevel}/${tpkGrade}`);
}

/**
 * 등급 등록
 * @param {Object} data - 등록할 등급 데이터
 */
export function create(data) {
  return api.post(BASE_URL, data);
}

/**
 * 등급 수정 (점수 범위/총점만 수정 가능)
 * @param {number} tpkType - 시험종류 코드
 * @param {number} tpkLevel - 토픽레벨 코드
 * @param {number} tpkGrade - 등급
 * @param {Object} data - 수정할 데이터
 */
export function update(tpkType, tpkLevel, tpkGrade, data) {
  return api.put(`${BASE_URL}/${tpkType}/${tpkLevel}/${tpkGrade}`, data);
}

/**
 * 등급 삭제 (논리 삭제)
 * @param {number} tpkType - 시험종류 코드
 * @param {number} tpkLevel - 토픽레벨 코드
 * @param {number} tpkGrade - 등급
 */
export function remove(tpkType, tpkLevel, tpkGrade) {
  return api.delete(`${BASE_URL}/${tpkType}/${tpkLevel}/${tpkGrade}`);
}
