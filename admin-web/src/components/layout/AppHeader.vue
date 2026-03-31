<!-- 관리자 웹 상단 헤더 — 햄버거 토글 + 타이틀 + 로그인 사용자 정보 + 로그아웃 -->
<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

defineProps({
  /** 사이드바 접힘 상태 */
  collapsed: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['toggle']);

/** 로그아웃 후 로그인 페이지로 이동 */
function handleLogout() {
  authStore.logout();
  router.push({ name: 'login' });
}
</script>

<template>
  <header
    class="flex h-14 shrink-0 items-center border-b border-gray-700 bg-gray-900 px-4 text-white"
  >
    <!-- 햄버거 토글 버튼 -->
    <button
      class="flex h-10 w-10 items-center justify-center rounded-lg text-xl transition-colors hover:bg-gray-700"
      @click="emit('toggle')"
    >
      ☰
    </button>

    <!-- 타이틀 — 클릭 시 대시보드로 이동 -->
    <router-link to="/" class="ml-3 text-lg font-bold tracking-wide hover:text-gray-300">
      TPK Pilot UI
    </router-link>

    <!-- 우측: 로그인 사용자 정보 + 로그아웃 -->
    <div v-if="authStore.isLoggedIn" class="ml-auto flex items-center gap-3">
      <span class="text-sm text-gray-300">{{ authStore.adminId }}</span>
      <button
        class="rounded border border-gray-500 px-3 py-1 text-xs text-gray-300 transition-colors hover:bg-gray-700 hover:text-white"
        @click="handleLogout"
      >
        로그아웃
      </button>
    </div>
  </header>
</template>
