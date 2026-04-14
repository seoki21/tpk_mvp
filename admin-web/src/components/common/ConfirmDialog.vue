<!--
  공통 확인 다이얼로그 컴포넌트
  - 삭제 등 위험한 작업 전에 사용자 확인을 받기 위해 사용
  - 어두운 오버레이 위에 간단한 메시지와 확인/취소 버튼을 표시
-->
<script setup>
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
});

const emit = defineEmits(['confirm', 'cancel']);
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-y-0 right-0 z-[60] flex items-center justify-center overflow-auto bg-black/50" style="left: var(--sidebar-w, 224px); min-width: calc(1200px - var(--sidebar-w, 224px))">
      <div class="mx-4 w-full max-w-sm rounded-lg bg-white p-6 shadow-lg">
        <!-- 메시지 -->
        <p class="mb-6 text-center text-gray-700">{{ message }}</p>

        <!-- 버튼 영역 -->
        <div class="flex items-center justify-center gap-3">
          <button class="btn btn-sm btn-primary px-6" @click="emit('confirm')">확인</button>
          <button class="btn btn-sm btn-secondary px-6" @click="emit('cancel')">취소</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
