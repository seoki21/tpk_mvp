<!--
  관리자 웹 좌측 사이드바 메뉴
  - 펼침: 아이콘 + 텍스트 (w-56)
  - 접힘: 아이콘만 (w-16), 호버 시 tooltip
  - 활성 메뉴: 좌측 파란색 인디케이터 바 + 배경색
  - 문항유형 관리 아래 가로 구분선 + 관리자 관리/그룹코드관리/코드관리
  - transition-all duration-300 애니메이션
-->
<script setup>
import { useRoute } from 'vue-router';

const route = useRoute();

defineProps({
  /** 사이드바 접힘 상태 */
  collapsed: {
    type: Boolean,
    default: false
  }
});

/* 메뉴 항목 정의 — 아이콘 + 라벨 + 경로, separator로 구분선 표시 */
const menuItems = [
  { icon: '📊', label: '대시보드', path: '/' },
  { icon: '👤', label: '사용자 관리', path: '/users' },
  { icon: '📝', label: '시험 관리', path: '/exam-questions' },
  { icon: '📄', label: '기출문항 관리', path: '/past-exam-questions' },
  { icon: '📋', label: '연습문항 관리', path: '/practice-questions' },
  { icon: '🏗', label: '문항구조 관리', path: '/question-structures' },
  { icon: '📂', label: '문항유형 관리', path: '/question-types' },
  { separator: true },
  { icon: '🔐', label: '관리자 관리', path: '/admins' },
  { icon: '🏷', label: '그룹코드관리', path: '/group-codes' },
  { icon: '🔢', label: '코드관리', path: '/codes' }
];

/**
 * 현재 경로와 메뉴 경로가 일치하는지 확인
 */
function isActive(path) {
  return route.path === path;
}
</script>

<template>
  <nav
    class="flex shrink-0 flex-col overflow-hidden bg-gray-800 text-gray-300 transition-all duration-300"
    :class="collapsed ? 'w-16' : 'w-56'"
  >
    <!-- 메뉴 리스트 -->
    <div class="flex-1 overflow-y-auto py-2">
      <template v-for="(item, idx) in menuItems" :key="idx">
        <!-- 구분선 -->
        <div v-if="item.separator" class="mx-4 my-2 border-t border-gray-600"></div>

        <!-- 메뉴 항목 -->
        <router-link
          v-else
          :to="item.path"
          class="group relative mx-2 my-0.5 flex h-11 items-center rounded-lg transition-colors"
          :class="
            isActive(item.path)
              ? 'bg-blue-600/20 text-white'
              : 'text-gray-400 hover:bg-gray-700 hover:text-gray-200'
          "
          :title="collapsed ? item.label : ''"
        >
          <!-- 활성 메뉴 좌측 인디케이터 바 -->
          <div
            v-if="isActive(item.path)"
            class="absolute bottom-1.5 left-0 top-1.5 w-1 rounded-r bg-blue-500"
          ></div>

          <!-- 아이콘 -->
          <span
            class="flex shrink-0 items-center justify-center text-base"
            :class="collapsed ? 'ml-0 w-12' : 'ml-2 w-10'"
          >
            {{ item.icon }}
          </span>

          <!-- 라벨 (펼침 상태에서만 표시) -->
          <span v-if="!collapsed" class="overflow-hidden whitespace-nowrap text-sm">
            {{ item.label }}
          </span>
        </router-link>
      </template>
    </div>
  </nav>
</template>
