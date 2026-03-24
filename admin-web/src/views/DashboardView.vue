<!-- 관리자 대시보드 — 기본 랜딩 페이지 (추후 구현 예정) -->
<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div class="flex items-center justify-center h-full text-gray-400 text-lg">
    {{ t('app.title') }}
  </div>
</template>
