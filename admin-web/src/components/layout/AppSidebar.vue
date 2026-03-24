<!-- 관리자 웹 좌측 사이드바 메뉴 -->
<script setup>
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

const { t } = useI18n()
const route = useRoute()

/* 메뉴 항목 정의 — 레이아웃 이미지 순서 기준 */
const menuItems = [
  { label: 'menu.userManagement', path: '/users' },
  { label: 'menu.examQuestion', path: '/exam-questions' },
  { label: 'menu.practiceQuestion', path: '/practice-questions' },
  { label: 'menu.questionStructure', path: '/question-structures' },
  { label: 'menu.questionType', path: '/question-types' },
  { label: 'menu.groupCode', path: '/group-codes' },
  { label: 'menu.code', path: '/codes' }
]

/**
 * 현재 경로와 메뉴 경로가 일치하는지 확인
 * @param {string} path - 메뉴 경로
 * @returns {boolean}
 */
function isActive(path) {
  return route.path === path
}
</script>

<template>
  <nav class="w-52 bg-gray-50 border-r border-gray-300 p-4 space-y-2 overflow-y-auto">
    <router-link
      v-for="item in menuItems"
      :key="item.path"
      :to="item.path"
      class="block w-full px-4 py-3 text-sm text-center rounded-lg transition-colors"
      :class="isActive(item.path)
        ? 'bg-blue-100 text-blue-800 font-bold border border-blue-300'
        : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-100'"
    >
      {{ t(item.label) }}
    </router-link>
  </nav>
</template>
