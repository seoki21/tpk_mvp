<!--
  공통 검색바 컴포넌트
  - 검색 입력 필드를 slot으로 받아 유연하게 구성
  - 조회/등록 버튼을 오른쪽에 배치
  - 각 목록 페이지에서 재사용한다.
-->
<script setup>
defineProps({
  /** 등록 버튼 숨김 여부 (조회 전용 화면에서 사용) */
  hideRegister: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['search', 'register']);
</script>

<template>
  <div
    class="mb-4 flex items-center justify-between rounded border border-gray-300 bg-gray-50 px-4 py-3"
  >
    <!-- 검색 필드 영역 (슬롯) -->
    <div class="flex flex-wrap items-center gap-4">
      <slot></slot>
    </div>

    <!-- 조회/등록 버튼 영역 -->
    <div class="ml-4 flex shrink-0 items-center gap-2">
      <button class="btn btn-sm btn-secondary" @click="emit('search')">조회</button>
      <button v-if="!hideRegister" class="btn btn-sm btn-secondary" @click="emit('register')">
        등록
      </button>
    </div>
  </div>
</template>
