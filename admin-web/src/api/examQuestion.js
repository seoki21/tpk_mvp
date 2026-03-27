/**
 * 기출문제/지시문 API 모듈
 * - 기출문제 관리 화면에서 사용하는 API 호출 함수를 정의한다.
 * - 문제/지시문 조회, 일괄 저장, PDF→JSON 변환(SSE 스트리밍) 기능을 제공한다.
 */
import api from './index';

/**
 * 특정 시험의 문제 + 지시문 목록 조회
 * @param {number} examKey - 시험키 PK
 */
export function getQuestionsAndInstructions(examKey) {
  return api.get(`/api/v1/exam-list/${examKey}/questions`);
}

/**
 * 문제 + 지시문 일괄 저장
 * @param {number} examKey - 시험키 PK
 * @param {Object} data - { questions: [...], instructions: [...] }
 */
export function bulkSave(examKey, data) {
  return api.post(`/api/v1/exam-list/${examKey}/questions/bulk-save`, data);
}

/**
 * 다국어 피드백 일괄 생성 (Claude API)
 * 해당 시험의 모든 문제에 대해 feedback_json을 생성하여 DB에 저장한다.
 * @param {number} examKey - 시험키 PK
 */
export function generateFeedback(examKey) {
  return api.post(`/api/v1/exam-feedback/${examKey}/generate`);
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
 */
export async function convertPdfToJsonStream(examKey, pdfKey, onEvent) {
  /* API base URL — 개발 환경에서는 빈 문자열(Vite 프록시 사용) */
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';

  const response = await fetch(`${baseUrl}/api/v1/exam-list/${examKey}/convert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pdf_key: pdfKey })
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
