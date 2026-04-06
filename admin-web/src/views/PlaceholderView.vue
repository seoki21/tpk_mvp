<!-- 미구현 기능 안내 페이지 — 진입 시 토스트 표시 + 화면 중앙 안내 문구 -->
<script setup>
import { onMounted } from 'vue';
import { useToast } from '@/composables/useToast';

const toast = useToast();
const MESSAGE = '아직 화면 및 기능 준비중입니다.';

onMounted(() => {
  toast.info(MESSAGE);
});
</script>

<template>
  <div class="flex h-full items-center justify-center text-gray-400">
    {{ MESSAGE }}
  </div>
</template>
