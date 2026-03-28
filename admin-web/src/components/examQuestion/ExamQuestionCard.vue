<!--
  문항 렌더링 카드 컴포넌트
  - 기출문제 관리 화면의 우측 시험지 UI에서 문항(item_type=Q)을 렌더링한다.
  - 상단: 문항번호(정답 색상), section, type, score 뱃지
  - 본문: full_sentence + paragraph + question_text + 선택지(2열)
  - 하단: 다국어 피드백 탭바 + 피드백 리스트
-->
<script setup>
import { reactive } from 'vue';

const props = defineProps({
  /** 문항 항목 원본 (store.mergedItems의 항목) */
  item: {
    type: Object,
    required: true
  },
  /** 파싱된 question JSON 객체 (editState.parsed) */
  parsed: {
    type: Object,
    default: null
  },
  /** 정답 번호 */
  correctAnswer: {
    type: [Number, String],
    default: null
  },
  /**
   * 피드백 데이터
   * { tabs: [{ key, label, list }], source: string }
   */
  feedbackData: {
    type: Object,
    default: () => ({ tabs: [], source: 'none' })
  }
});

/* ========== 피드백 탭 상태 관리 ========== */
const feedbackActiveTab = reactive({});

/** 피드백 탭 선택 */
function setFeedbackTab(lang) {
  feedbackActiveTab[props.item.question_no] = lang;
}

/** 활성 피드백 탭 키 반환 */
function getActiveFeedbackTab() {
  if (props.feedbackData.tabs.length === 0) return null;
  const saved = feedbackActiveTab[props.item.question_no];
  if (saved && props.feedbackData.tabs.some((t) => t.key === saved)) return saved;
  return props.feedbackData.tabs[0].key;
}

/** 활성 탭의 피드백 리스트 반환 */
function getActiveFeedbackList() {
  const activeKey = getActiveFeedbackTab();
  const tab = props.feedbackData.tabs.find((t) => t.key === activeKey);
  return tab ? tab.list : [];
}

/**
 * 피드백 문자열 파싱
 * "①:T_정답 설명" → { label: "①", isCorrect: true, text: "정답 설명" }
 */
function parseFeedback(fb) {
  if (!fb || typeof fb !== 'string') return { label: '', isCorrect: false, text: fb || '' };
  const colonIdx = fb.indexOf(':');
  if (colonIdx === -1) return { label: '', isCorrect: false, text: fb };
  const label = fb.substring(0, colonIdx);
  const rest = fb.substring(colonIdx + 1);
  const isCorrect = rest.startsWith('T');
  const underscoreIdx = rest.indexOf('_');
  const text = underscoreIdx !== -1 ? rest.substring(underscoreIdx + 1) : rest;
  return { label, isCorrect, text };
}
</script>

<template>
  <!-- 상단: {no}번(정답 색상) {section} {type} {score}점 -->
  <div class="mb-3 border-b border-gray-200 pb-2">
    <div class="flex items-baseline gap-2 text-sm">
      <span
        class="font-bold"
        :class="
          correctAnswer
            ? 'rounded bg-blue-600 px-1.5 py-0.5 text-white'
            : 'text-gray-800'
        "
      >
        {{ item.question_no }}번
        <template v-if="correctAnswer">
          (정답: {{ correctAnswer }})
        </template>
      </span>
      <span
        v-if="parsed && parsed.section"
        class="rounded bg-blue-50 px-1.5 py-0.5 text-blue-700"
      >
        {{ parsed.section }}
      </span>
      <span
        v-if="parsed && parsed.type"
        class="rounded bg-green-50 px-1.5 py-0.5 text-green-700"
      >
        {{ parsed.type }}
      </span>
      <span
        v-if="parsed && parsed.score"
        class="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700"
      >
        {{ parsed.score }}점
      </span>
    </div>
  </div>
  <!-- 본문 -->
  <template v-if="parsed">
    <p
      v-if="parsed.full_sentence"
      class="mb-2 text-sm leading-relaxed text-gray-800"
    >
      {{ parsed.full_sentence }}
    </p>
    <div
      v-if="parsed.paragraph"
      class="mb-3 rounded border border-gray-300 bg-white p-3 text-sm leading-relaxed text-gray-700"
    >
      <p class="whitespace-pre-wrap">{{ parsed.paragraph }}</p>
    </div>
    <p
      v-if="parsed.question_text"
      class="mb-2 text-sm leading-relaxed text-gray-800"
    >
      {{ item.question_no }}. {{ parsed.question_text }}
    </p>
    <!-- 선택지 -->
    <div
      v-if="parsed.choices"
      class="mb-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm"
    >
      <span
        v-for="(choice, ci) in parsed.choices"
        :key="ci"
        class="text-gray-700"
      >
        {{ choice }}
      </span>
    </div>
    <!-- 피드백 영역 (다국어 탭바) -->
    <div
      v-if="feedbackData.tabs.length"
      class="mt-3 rounded border border-gray-100 bg-slate-50 px-3 pb-3 pt-2"
    >
      <!-- 탭바: 다국어 전환 -->
      <div class="mb-2 flex items-center gap-1 border-b border-gray-200 pb-1">
        <button
          v-for="tab in feedbackData.tabs"
          :key="tab.key"
          class="rounded-t px-2.5 py-1 text-sm transition-colors"
          :class="
            getActiveFeedbackTab() === tab.key
              ? 'border-b-2 border-blue-500 font-medium text-blue-700'
              : 'text-gray-400 hover:text-gray-600'
          "
          @click="setFeedbackTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>
      <!-- 피드백 리스트 -->
      <div v-if="getActiveFeedbackList().length" class="space-y-1">
        <div
          v-for="(fb, fi) in getActiveFeedbackList()"
          :key="fi"
          class="flex items-start gap-1.5 text-sm leading-relaxed"
          :class="
            parseFeedback(fb).isCorrect
              ? 'font-medium text-blue-700'
              : 'text-gray-600'
          "
        >
          <span class="shrink-0">{{ parseFeedback(fb).label }}</span>
          <span>{{ parseFeedback(fb).text }}</span>
        </div>
      </div>
      <p v-else class="py-2 text-sm text-gray-400">
        피드백 데이터가 없습니다.
      </p>
    </div>
  </template>
  <p v-else class="text-sm text-gray-400">JSON 파싱 불가</p>
</template>
