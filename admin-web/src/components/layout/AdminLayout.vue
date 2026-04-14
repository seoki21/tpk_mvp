<!-- 관리자 웹 전체 레이아웃 — 헤더 + 사이드바(접기/펼치기) + 콘텐츠 영역 -->
<script setup>
import { ref, computed } from 'vue';
import AppHeader from './AppHeader.vue';
import AppSidebar from './AppSidebar.vue';

/** 사이드바 접힘 상태 */
const collapsed = ref(false);

/** 사이드바 너비 (px) — 팝업 오버레이 위치 계산용 CSS 변수로 제공 */
const sidebarWidth = computed(() => (collapsed.value ? '64px' : '224px'));

/** 사이드바 토글 */
function toggleSidebar() {
  collapsed.value = !collapsed.value;
}
</script>

<template>
  <div class="flex h-screen flex-col" :style="{ '--sidebar-w': sidebarWidth }">
    <!-- 상단 헤더 -->
    <AppHeader :collapsed="collapsed" @toggle="toggleSidebar" />

    <!-- 본문: 사이드바 + 콘텐츠 -->
    <div class="flex flex-1 overflow-hidden">
      <AppSidebar :collapsed="collapsed" />
      <!-- 메인 콘텐츠: 일정 너비 이하에서 가로 스크롤 발생 (사이드바/헤더는 고정 유지) -->
      <main class="flex-1 overflow-auto bg-white p-6">
        <div class="min-w-[1200px]">
          <router-view />
        </div>
      </main>
    </div>
  </div>
</template>
