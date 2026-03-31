<!--
  지시문 렌더링 카드 컴포넌트
  - 기출문제 관리 화면의 우측 시험지 UI에서 지시문(item_type=I)을 렌더링한다.
  - 상단: 지시문 번호, 문제 번호 범위, 배점
  - 본문: question_text + choices
-->
<script setup>
defineProps({
  /** 지시문 항목 원본 (store.mergedItems의 항목) */
  item: {
    type: Object,
    required: true
  },
  /** 파싱된 JSON 객체 (editState.parsed) */
  parsed: {
    type: Object,
    default: null
  }
});
</script>

<template>
  <!-- 상단: instruction 필드 값 또는 지시문 {no} [{no_list}] {score}점 -->
  <div class="mb-3 border-b border-gray-200 pb-2">
    <div v-if="parsed && parsed.instruction" class="text-sm">
      <span class="font-bold text-gray-800">{{ parsed.instruction }}</span>
    </div>
    <div v-else class="flex items-baseline gap-2 text-sm">
      <span class="font-bold text-gray-800">지시문 {{ item.ins_no }}</span>
      <span
        v-if="parsed && parsed.no_list && parsed.no_list.length"
        class="text-gray-500"
      >
        [{{ parsed.no_list.join(', ') }}]
      </span>
      <span v-if="parsed && parsed.score" class="text-gray-500">
        {{ parsed.score }}점
      </span>
    </div>
  </div>
  <!-- 본문 -->
  <template v-if="parsed">
    <p
      v-if="parsed.question_text"
      class="mb-2 text-sm leading-relaxed text-gray-800"
    >
      {{ parsed.question_text }}
    </p>
    <div
      v-if="parsed.choices && parsed.choices.length"
      class="mt-2 rounded border border-gray-300 bg-white p-3 text-sm leading-relaxed text-gray-700"
    >
      <span v-for="(choice, ci) in parsed.choices" :key="ci" class="mr-4">
        {{ choice }}
      </span>
    </div>
  </template>
  <p v-else class="text-sm text-gray-400">JSON 파싱 불가</p>
</template>
