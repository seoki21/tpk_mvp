<!--
  관리자 웹 좌측 사이드바 메뉴
  - 펼침: 아이콘 + 텍스트 (w-56)
  - 접힘: 아이콘만 (w-16), 호버 시 tooltip
  - 활성 메뉴: 좌측 파란색 인디케이터 바 + 배경색
  - transition-all duration-300 애니메이션
-->
<script setup>
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

const { t } = useI18n()
const route = useRoute()

defineProps({
  /** 사이드바 접힘 상태 */
  collapsed: {
    type: Boolean,
    default: false
  }
})

/* 메뉴 항목 정의 — 아이콘 + 라벨 + 경로 */
const menuItems = [
  { icon: '👤', label: 'menu.userManagement', path: '/users' },
  { icon: '📝', label: 'menu.examQuestion', path: '/exam-questions' },
  { icon: '📋', label: 'menu.practiceQuestion', path: '/practice-questions' },
  { icon: '🏗', label: 'menu.questionStructure', path: '/question-structures' },
  { icon: '📂', label: 'menu.questionType', path: '/question-types' },
  { icon: '🏷', label: 'menu.groupCode', path: '/group-codes' },
  { icon: '🔢', label: 'menu.code', path: '/codes' }
]

/**
 * 현재 경로와 메뉴 경로가 일치하는지 확인
 */
function isActive(path) {
  return route.path === path
}
</script>

<template>
  <nav
    class="bg-gray-800 text-gray-300 flex flex-col overflow-hidden transition-all duration-300 shrink-0"
    :class="collapsed ? 'w-16' : 'w-56'"
  >
    <!-- 메뉴 리스트 -->
    <div class="flex-1 overflow-y-auto py-2">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="relative flex items-center h-11 mx-2 my-0.5 rounded-lg transition-colors group"
        :class="isActive(item.path)
          ? 'bg-blue-600/20 text-white'
          : 'hover:bg-gray-700 text-gray-400 hover:text-gray-200'"
        :title="collapsed ? t(item.label) : ''"
      >
        <!-- 활성 메뉴 좌측 인디케이터 바 -->
        <div
          v-if="isActive(item.path)"
          class="absolute left-0 top-1.5 bottom-1.5 w-1 bg-blue-500 rounded-r"
        ></div>

        <!-- 아이콘 -->
        <span
          class="shrink-0 text-base flex items-center justify-center"
          :class="collapsed ? 'w-12 ml-0' : 'w-10 ml-2'"
        >
          {{ item.icon }}
        </span>

        <!-- 라벨 (펼침 상태에서만 표시) -->
        <span
          v-if="!collapsed"
          class="text-sm whitespace-nowrap overflow-hidden"
        >
          {{ t(item.label) }}
        </span>
      </router-link>
    </div>
  </nav>
</template>
