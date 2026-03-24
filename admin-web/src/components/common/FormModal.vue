<!--
  공통 폼 모달 컴포넌트
  - Teleport를 사용하여 body에 마운트
  - 어두운 오버레이 배경 + 가운데 흰색 모달 박스
  - 타이틀 바, 본문(슬롯), 하단 버튼(저장/삭제) 구조
  - 오버레이 클릭 또는 X 버튼으로 닫기
-->
<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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
  }
})

const emit = defineEmits(['close', 'save', 'delete'])

/** 오버레이 클릭 시 모달 닫기 */
function onOverlayClick() {
  emit('close')
}

/** 모달 내부 클릭 이벤트 전파 차단 */
function onModalClick(e) {
  e.stopPropagation()
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
      <div
        class="bg-white rounded-lg shadow-lg w-full max-w-lg mx-4"
        @click="onModalClick"
      >
        <!-- 타이틀 바 -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-800">{{ title }}</h2>
          <button
            class="w-8 h-8 flex items-center justify-center bg-gray-800 text-white rounded hover:bg-gray-700 text-sm font-bold"
            @click="emit('close')"
          >
            X
          </button>
        </div>

        <!-- 본문 영역 (슬롯) -->
        <div class="px-6 py-4">
          <slot />
        </div>

        <!-- 하단 버튼 바 -->
        <div class="flex items-center justify-center gap-3 px-6 py-4 border-t border-gray-200">
          <button
            class="px-6 py-2 bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded text-sm"
            @click="emit('save')"
          >
            {{ t('common.save') }}
          </button>
          <button
            v-if="showDelete"
            class="px-6 py-2 bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded text-sm"
            @click="emit('delete')"
          >
            {{ t('common.delete') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
