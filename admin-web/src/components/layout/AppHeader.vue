<!-- 관리자 웹 상단 헤더 — 햄버거 토글 + 타이틀 -->
<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps({
  /** 사이드바 접힘 상태 */
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle'])
</script>

<template>
  <header class="h-14 bg-gray-900 text-white flex items-center px-4 border-b border-gray-700 shrink-0">
    <!-- 햄버거 토글 버튼 -->
    <button
      class="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-700 transition-colors text-xl"
      @click="emit('toggle')"
    >
      ☰
    </button>

    <!-- 타이틀 -->
    <h1 class="text-lg font-bold tracking-wide ml-3">{{ t('app.title') }}</h1>
  </header>
</template>
