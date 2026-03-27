/**
 * 시험 파일 API 모듈
 * - 시험 파일 업로드/조회/삭제/다운로드 관련 API 호출 함수를 정의한다.
 * - 파일 업로드는 multipart/form-data로 전송한다.
 */
import api from './index';

/**
 * 파일 목록 조회
 * @param {number} examKey - 시험키 PK
 */
export function getFiles(examKey) {
  return api.get(`/api/v1/exam-list/${examKey}/files`);
}

/**
 * 파일 업로드 (여러 파일 동시 업로드 가능)
 * @param {number} examKey - 시험키 PK
 * @param {File[]} files - 업로드할 파일 배열
 * @param {string} fileType - 파일 유형 ('pdf' | 'json', 기본값 'pdf')
 */
export function uploadFiles(examKey, files, fileType = 'pdf') {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  formData.append('file_type', fileType);
  /* Content-Type을 명시하지 않아야 Axios가 boundary를 자동 생성한다 */
  return api.post(`/api/v1/exam-list/${examKey}/files`, formData, {
    headers: { 'Content-Type': undefined }
  });
}

/**
 * 파일 삭제
 * @param {number} examKey - 시험키 PK
 * @param {number} pdfKey - 파일키 PK
 */
export function deleteFile(examKey, pdfKey) {
  return api.delete(`/api/v1/exam-list/${examKey}/files/${pdfKey}`);
}

/**
 * 파일 다운로드 URL 생성
 * @param {number} examKey - 시험키 PK
 * @param {number} pdfKey - 파일키 PK
 * @returns {string} 다운로드 URL
 */
export function getDownloadUrl(examKey, pdfKey) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
  return `${baseUrl}/api/v1/exam-list/${examKey}/files/${pdfKey}/download`;
}

/**
 * PDF 인라인 뷰어용 URL 생성 (iframe에서 직접 표시)
 * @param {number} examKey - 시험키 PK
 * @param {number} pdfKey - 파일키 PK
 * @returns {string} 인라인 표시 URL
 */
export function getInlineViewUrl(examKey, pdfKey) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
  return `${baseUrl}/api/v1/exam-list/${examKey}/files/${pdfKey}/download?inline=true`;
}
