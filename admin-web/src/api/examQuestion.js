/**
 * 기출문제/지시문 API 모듈
 * - 기출문제 관리 화면에서 사용하는 API 호출 함수를 정의한다.
 * - 문제/지시문 조회, 일괄 저장, PDF→JSON 변환(SSE 스트리밍) 기능을 제공한다.
 */
import api, { API_TIMEOUT_LONG, API_TIMEOUT_AI } from './index';

/**
 * 특정 시험의 문제 + 지시문 목록 조회
 * @param {number} examKey - 시험키 PK
 * @param {Object} [config] - Axios 요청 옵션 (skipProgress 등)
 */
export function getQuestionsAndInstructions(examKey, config) {
  return api.get(`/api/v1/exam-list/${examKey}/questions`, config);
}

/**
 * 문제 + 지시문 일괄 저장
 * @param {number} examKey - 시험키 PK
 * @param {Object} data - { questions: [...], instructions: [...] }
 */
export function bulkSave(examKey, data) {
  return api.post(`/api/v1/exam-list/${examKey}/questions/bulk-save`, data, {
    timeout: API_TIMEOUT_LONG
  });
}

/**
 * 다국어 피드백 일괄 생성 (AI API)
 * 해당 시험의 모든 문제에 대해 feedback_json을 생성하여 DB에 저장한다.
 * @param {number} examKey - 시험키 PK
 * @param {string} aiProvider - AI 제공자 ('claude' 또는 'gemini')
 * @param {string[]|null} locales - 생성할 locale 코드 목록 (null이면 ko만)
 */
export function generateFeedback(examKey, aiProvider = 'claude', locales = null) {
  return api.post(`/api/v1/exam-feedback/${examKey}/generate`, {
    ai_provider: aiProvider,
    locales
  });
}

/**
 * 단건 피드백 생성 (AI API)
 * question_json을 전달하여 다국어 피드백을 생성한다. DB 저장 없이 결과만 반환.
 * @param {string} questionJson - 문제 JSON 문자열
 * @param {string} aiProvider - AI 제공자 ('claude' 또는 'gemini')
 * @param {string[]|null} locales - 생성할 locale 코드 목록 (null이면 ko만)
 * @param {string|null} section - 영역명 (듣기/읽기 — 프롬프트 분기용)
 */
export function generateFeedbackSingle(
  questionJson,
  aiProvider = 'claude',
  locales = null,
  section = null
) {
  return api.post(
    '/api/v1/exam-feedback/generate-single',
    {
      question_json: questionJson,
      ai_provider: aiProvider,
      locales,
      section
    },
    { timeout: API_TIMEOUT_AI }
  );
}

/**
 * 단건 피드백 저장
 * 특정 문항의 feedback_json을 DB에 저장한다.
 * @param {number} examKey - 시험키 PK
 * @param {number} questionNo - 문제 번호
 * @param {string} feedbackJson - 피드백 JSON 문자열
 */
export function saveFeedbackSingle(examKey, questionNo, feedbackJson) {
  return api.post(`/api/v1/exam-feedback/${examKey}/save-single`, {
    question_no: questionNo,
    feedback_json: feedbackJson
  });
}

/**
 * 단건 문제+피드백 저장
 * 특정 문항의 question_json과 feedback_json을 DB에 업데이트한다.
 * 기존 row가 없으면 에러 반환 (전체 저장 후 수정만 가능).
 * @param {number} examKey - 시험키 PK
 * @param {number} questionNo - 문제 번호
 * @param {string|null} questionJson - 문제 JSON 문자열
 * @param {string|null} feedbackJson - 피드백 JSON 문자열
 */
export function updateQuestionSingle(examKey, questionNo, questionJson, feedbackJson) {
  return api.post(`/api/v1/exam-feedback/${examKey}/update-single`, {
    question_no: questionNo,
    question_json: questionJson,
    feedback_json: feedbackJson
  });
}

/**
 * PDF에서 이미지 영역을 자동 검출하여 crop한다.
 * @param {number} examKey - 시험키 PK
 * @param {number} pdfKey - PDF 파일키 PK
 */
export function cropImages(examKey, pdfKey) {
  return api.post(
    `/api/v1/exam-list/${examKey}/images/crop`,
    { pdf_key: pdfKey },
    { timeout: API_TIMEOUT_AI }
  );
}

/**
 * crop된 이미지 파일명을 최종 파일명으로 일괄 변경한다.
 * @param {number} examKey - 시험키 PK
 * @param {Array} renameMap - [{ old_filename, new_filename }, ...]
 */
export function renameCropImages(examKey, renameMap) {
  return api.post(`/api/v1/exam-list/${examKey}/images/rename`, { rename_map: renameMap });
}

/**
 * PDF 파일의 총 페이지 수를 조회한다.
 * @param {number} examKey - 시험키 PK
 * @param {number} pdfKey - PDF 파일키 PK
 */
export function getPdfPageCount(examKey, pdfKey) {
  return api.get(`/api/v1/exam-list/${examKey}/images/pdf-page-count`, {
    params: { pdf_key: pdfKey }
  });
}

/**
 * PDF 특정 페이지를 PNG 이미지 Blob으로 가져온다.
 * JWT 인증이 필요하므로 axios blob 방식으로 fetch한다.
 * @param {number} examKey - 시험키 PK
 * @param {number} pdfKey - PDF 파일키 PK
 * @param {number} page - 페이지 번호 (1-based)
 * @param {number} dpi - 렌더링 해상도 (기본 150)
 * @returns {Promise<Blob>} PNG 이미지 Blob
 */
export function fetchPdfPageImage(examKey, pdfKey, page, dpi = 150) {
  return api.get(`/api/v1/exam-list/${examKey}/images/pdf-page`, {
    params: { pdf_key: pdfKey, page, dpi },
    responseType: 'blob'
  });
}

/**
 * 사용자가 지정한 좌표로 PDF에서 이미지를 수동 crop한다.
 * @param {number} examKey - 시험키 PK
 * @param {number} pdfKey - PDF 파일키 PK
 * @param {Array} crops - [{ page, x, y, w, h, filename }] (좌표는 300dpi 기준)
 */
export function cropManualImages(examKey, pdfKey, crops) {
  return api.post(
    `/api/v1/exam-list/${examKey}/images/crop-manual`,
    { pdf_key: pdfKey, crops },
    { timeout: API_TIMEOUT_AI }
  );
}

/**
 * PDF → JSON 변환 (Claude API SSE 스트리밍)
 * fetch API를 사용하여 SSE 스트리밍 응답을 수신한다.
 * axios는 스트리밍을 네이티브 지원하지 않으므로 fetch + ReadableStream을 사용한다.
 *
 * @param {number} examKey - 시험키 PK
 * @param {number} pdfKey - PDF 파일키 PK
 * @param {Function} onEvent - SSE 이벤트 콜백 ({ type, data })
 *   - type: 'start' | 'text_delta' | 'done' | 'error'
 *   - data: 이벤트별 데이터 객체
 * @param {string} aiProvider - AI 제공자 ('claude' 또는 'gemini')
 * @param {string|null} section - 영역 (듣기/읽기) — 프롬프트 분기용
 */
export async function convertPdfToJsonStream(
  examKey,
  pdfKey,
  onEvent,
  aiProvider = 'claude',
  section = null
) {
  /* API base URL — 개발 환경에서는 빈 문자열(Vite 프록시 사용) */
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

  /* localStorage에서 JWT 토큰을 읽어 Authorization 헤더에 첨부 */
  const token = localStorage.getItem('admin_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${baseUrl}/api/v1/exam-list/${examKey}/convert`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ pdf_key: pdfKey, ai_provider: aiProvider, section })
  });

  /* HTTP 에러 응답 처리 (스트리밍 시작 전 에러) */
  if (!response.ok) {
    let detail = 'PDF 변환 요청에 실패했습니다.';
    try {
      const errBody = await response.json();
      detail = errBody.detail || detail;
    } catch {
      /* JSON 파싱 실패 시 기본 메시지 사용 */
    }
    onEvent({ type: 'error', data: { detail } });
    return;
  }

  /* ReadableStream으로 SSE 텍스트를 수신하여 이벤트 파싱 */
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    /* SSE 이벤트는 빈 줄(\n\n)로 구분된다 */
    const events = buffer.split('\n\n');
    /* 마지막 요소는 아직 완성되지 않은 이벤트일 수 있으므로 버퍼에 보관 */
    buffer = events.pop() || '';

    for (const eventStr of events) {
      if (!eventStr.trim()) continue;
      const parsed = parseSseEvent(eventStr);
      if (parsed) {
        onEvent(parsed);
      }
    }
  }

  /* 버퍼에 남은 마지막 이벤트 처리 */
  if (buffer.trim()) {
    const parsed = parseSseEvent(buffer);
    if (parsed) {
      onEvent(parsed);
    }
  }
}

/**
 * SSE 이벤트 문자열을 파싱하여 { type, data } 객체로 변환한다.
 * SSE 포맷: "event: <type>\ndata: <json>"
 *
 * @param {string} eventStr - SSE 이벤트 문자열
 * @returns {{ type: string, data: object } | null}
 */
function parseSseEvent(eventStr) {
  let type = '';
  let dataStr = '';

  for (const line of eventStr.split('\n')) {
    if (line.startsWith('event: ')) {
      type = line.slice(7).trim();
    } else if (line.startsWith('data: ')) {
      dataStr = line.slice(6);
    }
  }

  if (!type || !dataStr) return null;

  try {
    return { type, data: JSON.parse(dataStr) };
  } catch {
    return null;
  }
}
