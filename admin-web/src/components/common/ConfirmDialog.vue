<!--
  공통 확인 다이얼로그 컴포넌트
  - 삭제 등 위험한 작업 전에 사용자 확인을 받기 위해 사용
  - 어두운 오버레이 위에 간단한 메시지와 확인/취소 버튼을 표시
-->
<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps({
  /** 다이얼로그 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 표시할 메시지 */
  message: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50"
    >
      <div class="bg-white rounded-lg shadow-lg w-full max-w-sm mx-4 p-6">
        <!-- 메시지 -->
        <p class="text-center text-gray-700 mb-6">{{ message }}</p>

        <!-- 버튼 영역 -->
        <div class="flex items-center justify-center gap-3">
          <button
            class="px-6 py-2 bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded text-sm"
            @click="emit('confirm')"
          >
            {{ t('common.confirm') }}
          </button>
          <button
            class="px-6 py-2 bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded text-sm"
            @click="emit('cancel')"
          >
            {{ t('common.cancel') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
