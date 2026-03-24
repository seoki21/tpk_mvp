<!--
  공통 검색바 컴포넌트
  - 검색 입력 필드를 slot으로 받아 유연하게 구성
  - 조회/등록 버튼을 오른쪽에 배치
  - 각 목록 페이지에서 재사용한다.
-->
<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits(['search', 'register'])
</script>

<template>
  <div class="flex items-center justify-between border border-gray-300 rounded px-4 py-3 mb-4 bg-gray-50">
    <!-- 검색 필드 영역 (슬롯) -->
    <div class="flex items-center gap-4 flex-wrap">
      <slot />
    </div>

    <!-- 조회/등록 버튼 영역 -->
    <div class="flex items-center gap-2 ml-4 shrink-0">
      <button
        class="px-4 py-1.5 bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded text-sm"
        @click="emit('search')"
      >
        {{ t('common.search') }}
      </button>
      <button
        class="px-4 py-1.5 bg-gray-200 hover:bg-gray-300 border border-gray-400 rounded text-sm"
        @click="emit('register')"
      >
        {{ t('common.register') }}
      </button>
    </div>
  </div>
</template>
