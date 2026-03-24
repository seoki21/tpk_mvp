<!-- 관리자 웹 전체 레이아웃 — 헤더 + 사이드바(접기/펼치기) + 콘텐츠 영역 -->
<script setup>
import { ref } from 'vue'
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'

/** 사이드바 접힘 상태 */
const collapsed = ref(false)

/** 사이드바 토글 */
function toggleSidebar() {
  collapsed.value = !collapsed.value
}
</script>

<template>
  <div class="flex flex-col h-screen">
    <!-- 상단 헤더 -->
    <AppHeader :collapsed="collapsed" @toggle="toggleSidebar" />

    <!-- 본문: 사이드바 + 콘텐츠 -->
    <div class="flex flex-1 overflow-hidden">
      <AppSidebar :collapsed="collapsed" />
      <main class="flex-1 overflow-y-auto p-6 bg-white">
        <router-view />
      </main>
    </div>
  </div>
</template>
