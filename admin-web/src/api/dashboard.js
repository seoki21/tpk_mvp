/**
 * 대시보드 통계 API 모듈
 * - 요약 카드, 시험 통계, API 사용량 조회
 */
import api from './index';

/** 상단 요약 카드 데이터 조회 */
export function getSummary() {
  return api.get('/api/v1/dashboard/summary');
}

/** 시험/문제 현황 조회 */
export function getExamStats() {
  return api.get('/api/v1/dashboard/exam-stats');
}

/** API 사용량 조회 (period: 'daily', 'weekly', 'monthly') */
export function getApiUsage(period = 'daily') {
  return api.get('/api/v1/dashboard/api-usage', { params: { period } });
}
