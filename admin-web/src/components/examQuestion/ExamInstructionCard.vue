<!--
  지시문 렌더링 카드 컴포넌트
  - 기출문제 관리 화면의 우측 시험지 UI에서 지시문(item_type=I)을 렌더링한다.
  - 상단: 지시문 번호, 문제 번호 범위, 배점
  - 본문: question_text + choices
-->
<script setup>
const props = defineProps({
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

/** 선택지가 이미지 경로인지 판별 */
function isChoiceImage(choice) {
  if (!choice || typeof choice !== 'string') return false;
  const text = choice.replace(/^[①②③④⑤⑥⑦⑧⑨❶❷❸❹❺]\s*/, '').trim();
  return /\.(png|jpg|jpeg|webp)$/i.test(text);
}

/** 선택지에서 이미지 파일명 추출 */
function getChoiceImageFilename(choice) {
  return choice.replace(/^[①②③④⑤⑥⑦⑧⑨❶❷❸❹❺]\s*/, '').trim();
}

/** 이미지 파일 URL 생성 */
function getImageUrl(filename) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
  const examKey = props.item.exam_key;
  return `${baseUrl}/api/v1/exam-list/${examKey}/files/images/${filename}`;
}
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
    <!-- 문항 이미지 (question_img) — 지시문 바로 아래 -->
    <div v-if="parsed.question_img" class="mb-3">
      <img
        :src="getImageUrl(parsed.question_img)"
        :alt="`지시문 이미지`"
        class="max-w-full rounded border border-gray-200"
      />
    </div>
    <p
      v-if="parsed.question_text"
      class="mb-2 whitespace-pre-wrap text-sm leading-relaxed text-gray-800"
    >{{ parsed.question_text }}</p>
    <!-- 선택지: 이미지 (2열 그리드, 번호 옆에 이미지 가로 배치) -->
    <div
      v-if="parsed.choices && parsed.choices.length && isChoiceImage(parsed.choices[0])"
      class="mt-2 grid grid-cols-2 gap-2"
    >
      <div
        v-for="(choice, ci) in parsed.choices"
        :key="ci"
        class="flex items-center gap-2 rounded border border-gray-200 p-1"
      >
        <span class="shrink-0 text-sm font-medium text-gray-500">{{ String.fromCodePoint(0x2460 + ci) }}</span>
        <img
          :src="getImageUrl(getChoiceImageFilename(choice))"
          :alt="`선택지 ${ci + 1}`"
          class="min-w-0 flex-1"
        />
      </div>
    </div>
    <div
      v-else-if="parsed.choices && parsed.choices.length"
      class="mt-2 rounded border border-gray-300 bg-white p-3 text-sm leading-relaxed text-gray-700"
    >
      <span v-for="(choice, ci) in parsed.choices" :key="ci" class="mr-4">
        {{ choice }}
      </span>
    </div>
  </template>
  <p v-else class="text-sm text-gray-400">JSON 파싱 불가</p>
</template>
