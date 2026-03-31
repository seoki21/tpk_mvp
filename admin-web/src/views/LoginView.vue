<!--
  관리자 로그인 화면
  - 아이디/비밀번호 입력 후 JWT 토큰을 발급받아 로그인한다.
  - 로그인 성공 시 대시보드로 이동한다.
-->
<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const adminId = ref('admin');
const password = ref('dear#405');
const errorMsg = ref('');
const loading = ref(false);

/** 로그인 폼 제출 */
async function handleSubmit() {
  errorMsg.value = '';

  if (!adminId.value || !password.value) {
    errorMsg.value = '아이디와 비밀번호를 입력하세요.';
    return;
  }

  loading.value = true;
  try {
    await authStore.login(adminId.value, password.value);
    router.push({ name: 'dashboard' });
  } catch (error) {
    errorMsg.value = error.detail || '로그인에 실패했습니다.';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-100">
    <div class="w-full max-w-sm rounded-lg bg-white p-8 shadow-md">
      <!-- 타이틀 -->
      <h1 class="mb-6 text-center text-2xl font-bold text-gray-800">TOPIK 관리자</h1>

      <!-- 로그인 폼 -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- 아이디 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-gray-700">아이디</label>
          <input
            v-model="adminId"
            type="text"
            autocomplete="username"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="관리자 아이디"
          />
        </div>

        <!-- 비밀번호 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-gray-700">비밀번호</label>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            placeholder="비밀번호"
            @keyup.enter="handleSubmit"
          />
        </div>

        <!-- 에러 메시지 -->
        <p v-if="errorMsg" class="text-sm text-red-500">{{ errorMsg }}</p>

        <!-- 로그인 버튼 -->
        <button
          type="submit"
          class="w-full rounded bg-blue-600 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
          :disabled="loading"
        >
          {{ loading ? '로그인 중...' : '로그인' }}
        </button>
      </form>
    </div>
  </div>
</template>
