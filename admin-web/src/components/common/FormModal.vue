<!--
  공통 폼 모달 컴포넌트
  - Teleport를 사용하여 body에 마운트
  - 어두운 오버레이 배경 + 가운데 흰색 모달 박스
  - 타이틀 바, 본문(슬롯), 하단 버튼(저장/삭제) 구조
  - 오버레이 클릭 또는 X 버튼으로 닫기
-->
<script setup>
defineProps({
  /** 모달 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 모달 타이틀 텍스트 */
  title: {
    type: String,
    default: ''
  },
  /** 삭제 버튼 표시 여부 (수정 모드에서만 true) */
  showDelete: {
    type: Boolean,
    default: false
  },
  /** 모달 최대 너비 Tailwind 클래스 (기본: max-w-lg) */
  maxWidth: {
    type: String,
    default: 'max-w-lg'
  }
});

const emit = defineEmits(['close', 'save', 'delete']);

/** 오버레이 클릭 시 모달 닫기 */
function onOverlayClick() {
  emit('close');
}

/** 모달 내부 클릭 이벤트 전파 차단 */
function onModalClick(e) {
  e.stopPropagation();
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click="onOverlayClick"
    >
      <!-- 모달 박스 -->
      <div :class="['mx-4 w-full rounded-lg bg-white shadow-lg', maxWidth]" @click="onModalClick">
        <!-- 타이틀 바 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 class="text-lg font-semibold text-gray-800">{{ title }}</h2>
          <button
            class="flex h-8 w-8 items-center justify-center rounded bg-gray-800 text-sm font-bold text-white hover:bg-gray-700"
            @click="emit('close')"
          >
            X
          </button>
        </div>

        <!-- 본문 영역 (슬롯) -->
        <div class="px-6 py-4">
          <slot></slot>
        </div>

        <!-- 하단 버튼 바 -->
        <div class="flex items-center justify-center gap-3 border-t border-gray-200 px-6 py-4">
          <button
            class="rounded border border-gray-400 bg-gray-200 px-6 py-2 text-sm hover:bg-gray-300"
            @click="emit('save')"
          >
            저장
          </button>
          <button
            v-if="showDelete"
            class="rounded border border-gray-400 bg-gray-200 px-6 py-2 text-sm hover:bg-gray-300"
            @click="emit('delete')"
          >
            삭제
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
