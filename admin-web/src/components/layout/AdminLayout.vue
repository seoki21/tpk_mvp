<!-- 관리자 웹 전체 레이아웃 — 헤더 + 사이드바 + 콘텐츠 영역 -->
<script setup>
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
</script>

<template>
  <div class="flex flex-col h-screen">
    <!-- 상단 헤더 -->
    <AppHeader />

    <!-- 본문: 사이드바 + 콘텐츠 -->
    <div class="flex flex-1 overflow-hidden">
      <AppSidebar />
      <main class="flex-1 overflow-y-auto p-6 bg-white">
        <router-view />
      </main>
    </div>
  </div>
</template>
