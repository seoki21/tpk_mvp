<!--
  PDF 인라인 뷰어 컴포넌트
  - DataTable과 동일한 Box 스타일 (rounded border + gray header)
  - 헤더 좌측에 "파일 보기" 타이틀, 우측에 현재 파일명 표시
  - iframe으로 PDF를 인라인 렌더링
  - URL이 없을 때는 안내 메시지 표시
-->
<script setup>
defineProps({
  /** PDF 표시 URL (빈 문자열이면 빈 상태) */
  url: {
    type: String,
    default: ''
  },
  /** 현재 표시 중인 파일명 */
  fileName: {
    type: String,
    default: ''
  }
});
</script>

<template>
  <div class="flex flex-col overflow-hidden rounded border border-gray-300">
    <!-- 헤더: DataTable 상단 바와 동일한 스타일 -->
    <div class="flex shrink-0 items-center justify-between border-b border-gray-300 bg-gray-50 px-4 py-2">
      <span class="text-sm font-medium text-gray-700">파일 보기</span>
      <span v-if="fileName" class="truncate text-sm text-gray-500">{{ fileName }}</span>
    </div>

    <!-- PDF 표시 영역 — 부모 높이에 맞춰 자동 확장 -->
    <div v-if="url" class="min-h-[400px] flex-1">
      <iframe :src="url" class="h-full w-full border-0"></iframe>
    </div>
    <div v-else class="flex min-h-[400px] flex-1 items-center justify-center bg-gray-50 text-gray-400">
      파일을 선택하세요
    </div>
  </div>
</template>
