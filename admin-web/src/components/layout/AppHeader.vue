<!-- 관리자 웹 상단 헤더 — 타이틀 표시 -->
<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <header class="h-14 bg-gray-900 text-white flex items-center justify-center border-b border-red-600">
    <h1 class="text-xl font-bold tracking-wide">{{ t('app.title') }}</h1>
  </header>
</template>
