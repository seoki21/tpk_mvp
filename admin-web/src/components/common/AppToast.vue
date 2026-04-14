<!--
  전역 토스트 알림 컴포넌트
  - App.vue에 한 번만 배치하면 앱 어디서든 useToast()로 알림을 표시할 수 있다.
  - 우측 상단에 토스트 메시지가 스택으로 쌓인다.
  - 타입별 색상: success(초록), error(빨강), warning(노랑), info(파랑)
-->
<script setup>
import { useToast } from '@/composables/useToast';

const { toasts, remove } = useToast();

/** 타입별 스타일 클래스 */
const typeStyles = {
  success: 'border-green-400 bg-green-50 text-green-800',
  error: 'border-red-400 bg-red-50 text-red-800',
  warning: 'border-amber-400 bg-amber-50 text-amber-800',
  info: 'border-blue-400 bg-blue-50 text-blue-800'
};

/** 타입별 아이콘 SVG path */
const typeIcons = {
  success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
  warning:
    'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
  info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
};
</script>

<template>
  <Teleport to="body">
    <div class="fixed right-4 top-4 z-[100] flex flex-col gap-2">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="flex w-80 items-start gap-2 rounded-lg border px-4 py-3 shadow-lg"
          :class="typeStyles[toast.type] || typeStyles.info"
        >
          <!-- 아이콘 -->
          <svg
            class="mt-0.5 h-5 w-5 shrink-0"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              :d="typeIcons[toast.type] || typeIcons.info"
            />
          </svg>
          <!-- 메시지 -->
          <p class="flex-1 whitespace-pre-line text-sm">{{ toast.message }}</p>
          <!-- 닫기 버튼 -->
          <button class="shrink-0 opacity-60 hover:opacity-100" @click="remove(toast.id)">
            <svg
              class="h-4 w-4"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
/* 토스트 진입/퇴장 애니메이션 */
.toast-enter-active {
  transition: all 0.3s ease-out;
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
