<!-- 관리자 웹 상단 헤더 — 햄버거 토글 + 타이틀 -->
<script setup>
defineProps({
  /** 사이드바 접힘 상태 */
  collapsed: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['toggle']);
</script>

<template>
  <header
    class="flex h-14 shrink-0 items-center border-b border-gray-700 bg-gray-900 px-4 text-white"
  >
    <!-- 햄버거 토글 버튼 -->
    <button
      class="flex h-10 w-10 items-center justify-center rounded-lg text-xl transition-colors hover:bg-gray-700"
      @click="emit('toggle')"
    >
      ☰
    </button>

    <!-- 타이틀 -->
    <h1 class="ml-3 text-lg font-bold tracking-wide">TPK Pilot UI</h1>
  </header>
</template>
