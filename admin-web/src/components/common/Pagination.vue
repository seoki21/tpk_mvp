<!--
  공통 페이지네이션 컴포넌트
  - PREV / 페이지 번호 (5개 윈도우) / NEXT 구성
  - 현재 페이지, 페이지 크기, 전체 건수를 기반으로 동작
  - 페이지 변경 시 update:page 이벤트를 emit 한다.
-->
<script setup>
import { computed } from 'vue';

const props = defineProps({
  /** 현재 페이지 번호 (1부터 시작) */
  page: {
    type: Number,
    required: true
  },
  /** 페이지당 항목 수 */
  size: {
    type: Number,
    required: true
  },
  /** 전체 항목 수 */
  total: {
    type: Number,
    required: true
  }
});

const emit = defineEmits(['update:page']);

/** 전체 페이지 수 계산 */
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(props.total / props.size));
});

/** 표시할 페이지 번호 배열 (최대 5개 윈도우) */
const pageNumbers = computed(() => {
  const total = totalPages.value;
  const current = props.page;
  const windowSize = 5;

  let start = Math.max(1, current - Math.floor(windowSize / 2));
  let end = start + windowSize - 1;

  if (end > total) {
    end = total;
    start = Math.max(1, end - windowSize + 1);
  }

  const pages = [];
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  return pages;
});

/** PREV 버튼 비활성화 여부 */
const isPrevDisabled = computed(() => props.page <= 1);

/** NEXT 버튼 비활성화 여부 */
const isNextDisabled = computed(() => props.page >= totalPages.value);

/** 페이지 변경 핸들러 */
function goToPage(newPage) {
  if (newPage >= 1 && newPage <= totalPages.value && newPage !== props.page) {
    emit('update:page', newPage);
  }
}
</script>

<template>
  <div class="mt-4 flex items-center justify-center gap-1 py-2">
    <!-- PREV 버튼 -->
    <button
      class="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
      :disabled="isPrevDisabled"
      @click="goToPage(page - 1)"
    >
      PREV
    </button>

    <!-- 페이지 번호 버튼 -->
    <button
      v-for="num in pageNumbers"
      :key="num"
      class="rounded border px-3 py-1 text-sm"
      :class="
        num === page
          ? 'border-blue-500 bg-blue-500 text-white'
          : 'border-gray-300 hover:bg-gray-100'
      "
      @click="goToPage(num)"
    >
      {{ num }}
    </button>

    <!-- NEXT 버튼 -->
    <button
      class="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
      :disabled="isNextDisabled"
      @click="goToPage(page + 1)"
    >
      NEXT
    </button>
  </div>
</template>
