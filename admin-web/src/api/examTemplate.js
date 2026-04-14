/**
 * 시험 템플릿 API 모듈
 * - tb_exam_template CRUD API 호출 함수를 정의한다.
 * - 복합 PK (tpk_type, tpk_level, section, question_no)로 단건을 식별한다.
 */
import api from './index';

const BASE_URL = '/api/v1/exam-template';

/**
 * 시험 템플릿 목록 조회 (페이징/검색 파라미터 포함)
 * @param {Object} params - 검색 조건 (page, size, tpk_type, tpk_level, section)
 */
export function getList(params) {
  return api.get(BASE_URL, { params });
}

/**
 * 시험 템플릿 단건 조회
 * @param {number} tpkType - 시험종류 코드
 * @param {number} tpkLevel - 토픽레벨 코드
 * @param {number} section - 영역 코드
 * @param {number} questionNo - 문항번호
 */
export function getDetail(tpkType, tpkLevel, section, questionNo) {
  return api.get(`${BASE_URL}/${tpkType}/${tpkLevel}/${section}/${questionNo}`);
}

/**
 * 시험 템플릿 등록
 * @param {Object} data - 등록할 템플릿 데이터
 */
export function create(data) {
  return api.post(BASE_URL, data);
}

/**
 * 시험 템플릿 수정 (지문유형/문항유형만 수정 가능)
 * @param {number} tpkType - 시험종류 코드
 * @param {number} tpkLevel - 토픽레벨 코드
 * @param {number} section - 영역 코드
 * @param {number} questionNo - 문항번호
 * @param {Object} data - 수정할 데이터
 */
export function update(tpkType, tpkLevel, section, questionNo, data) {
  return api.put(`${BASE_URL}/${tpkType}/${tpkLevel}/${section}/${questionNo}`, data);
}

/**
 * 시험 템플릿 삭제 (논리 삭제)
 * @param {number} tpkType - 시험종류 코드
 * @param {number} tpkLevel - 토픽레벨 코드
 * @param {number} section - 영역 코드
 * @param {number} questionNo - 문항번호
 */
export function remove(tpkType, tpkLevel, section, questionNo) {
  return api.delete(`${BASE_URL}/${tpkType}/${tpkLevel}/${section}/${questionNo}`);
}
