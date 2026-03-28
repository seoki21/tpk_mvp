/**
 * 토스트 알림 composable
 * alert() 대신 사용자 경험이 좋은 토스트 메시지를 표시한다.
 * 앱 전역에서 공유되는 reactive 상태를 사용하여 어디서든 토스트를 호출할 수 있다.
 */
import { reactive } from 'vue';

/** 토스트 메시지 목록 (전역 공유) */
const toasts = reactive([]);

/** 고유 ID 카운터 */
let idCounter = 0;

/**
 * 토스트 메시지를 추가한다.
 * @param {string} message - 표시할 메시지
 * @param {'success'|'error'|'info'|'warning'} type - 토스트 타입
 * @param {number} duration - 자동 닫힘 시간(ms), 0이면 수동 닫기
 */
function addToast(message, type = 'info', duration = 3000) {
  const id = ++idCounter;
  toasts.push({ id, message, type });

  if (duration > 0) {
    setTimeout(() => removeToast(id), duration);
  }
}

/** 토스트 메시지를 제거한다. */
function removeToast(id) {
  const index = toasts.findIndex((t) => t.id === id);
  if (index !== -1) toasts.splice(index, 1);
}

/**
 * 토스트 알림 composable
 * @returns {{ toasts, success, error, info, warning, remove }}
 */
export function useToast() {
  return {
    toasts,
    /** 성공 메시지 (초록) */
    success: (msg) => addToast(msg, 'success'),
    /** 에러 메시지 (빨강, 5초) */
    error: (msg) => addToast(msg, 'error', 5000),
    /** 정보 메시지 (파랑) */
    info: (msg) => addToast(msg, 'info'),
    /** 경고 메시지 (노랑, 5초) */
    warning: (msg) => addToast(msg, 'warning', 5000),
    /** 수동 제거 */
    remove: removeToast
  };
}
