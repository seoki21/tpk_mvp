<!--
  듣기 문항 렌더링 카드 컴포넌트
  - 기출문제 관리(듣기) 화면의 우측 시험지 UI에서 문항(item_type=Q)을 렌더링한다.
  - 상단: 문항번호(정답 색상), section, type, score 뱃지
  - MP3 플레이어: 문제번호에 매칭되는 음성 파일 재생 (없으면 비활성 표시)
  - 본문: question_text + 선택지(2열)
  - 하단: 다국어 피드백 탭바 + 피드백 리스트
-->
<script setup>
import { reactive, computed } from 'vue';
import { getDownloadUrl } from '@/api/examFile';

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

const props = defineProps({
  /** 문항 항목 원본 (store.mergedItems의 항목) */
  item: { type: Object, required: true },
  /** 파싱된 question JSON 객체 (editState.parsed) */
  parsed: { type: Object, default: null },
  /** 정답 번호 */
  correctAnswer: { type: [Number, String], default: null },
  /** 피드백 데이터 { tabs: [{ key, label, list }], source: string } */
  feedbackData: { type: Object, default: () => ({ tabs: [], source: 'none' }) },
  /** MP3 파일 정보 (store.mp3FileMap에서 조회) — null이면 음성 파일 없음 */
  mp3File: { type: Object, default: null },
  /** 시험키 PK (MP3 다운로드 URL 생성용) */
  examKey: { type: Number, default: null },
  /** 영역(section) 코드 목록 — [{ code, code_name }] */
  sectionCodes: { type: Array, default: () => [] },
  /** 지문유형(passage_type) 코드 목록 */
  passageTypeCodes: { type: Array, default: () => [] },
  /** 문제유형(question_type) 코드 목록 */
  questionTypeCodes: { type: Array, default: () => [] }
});

const emit = defineEmits(['code-change']);

/* ========== MP3 재생 URL ========== */
const mp3Url = computed(() => {
  if (!props.mp3File || !props.examKey) return null;
  return getDownloadUrl(props.examKey, props.mp3File.pdf_key);
});

/* ========== 피드백 탭 상태 관리 ========== */
const feedbackActiveTab = reactive({});

function setFeedbackTab(lang) {
  feedbackActiveTab[props.item.question_no] = lang;
}

function getActiveFeedbackTab() {
  if (props.feedbackData.tabs.length === 0) return null;
  const saved = feedbackActiveTab[props.item.question_no];
  if (saved && props.feedbackData.tabs.some((t) => t.key === saved)) return saved;
  return props.feedbackData.tabs[0].key;
}

function getActiveFeedbackList() {
  const activeKey = getActiveFeedbackTab();
  const tab = props.feedbackData.tabs.find((t) => t.key === activeKey);
  return tab ? tab.list : [];
}

/* ========== 정답 판단 ========== */
const circleNumMap = { '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5, '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9 };

function parseFeedback(fb) {
  if (!fb || typeof fb !== 'string') return { label: '', isCorrect: false, text: fb || '' };
  const colonIdx = fb.indexOf(':');
  if (colonIdx === -1) return { label: '', isCorrect: false, text: fb };
  const label = fb.substring(0, colonIdx);
  const rest = fb.substring(colonIdx + 1);
  const underscoreIdx = rest.indexOf('_');
  const text = underscoreIdx !== -1 ? rest.substring(underscoreIdx + 1) : rest;
  const labelNum = circleNumMap[label.trim()];
  const isCorrect = labelNum != null && labelNum === Number(props.correctAnswer);
  return { label, isCorrect, text };
}
</script>

<template>
  <!-- 상단: {no}번 + 코드 셀렉트박스 (section, passage_type, question_type) + 배점 -->
  <div class="mb-3 border-b border-gray-200 pb-2">
    <div class="flex flex-wrap items-center gap-2 text-sm">
      <span class="font-bold text-gray-800"> {{ item.question_no }}번 </span>
      <!-- 영역(section) 셀렉트박스 -->
      <select
        v-if="parsed"
        :value="parsed.section"
        class="rounded border border-blue-200 bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700 focus:border-blue-400 focus:outline-none"
        @change="emit('code-change', item, 'section', $event.target.value)"
      >
        <option value="">영역</option>
        <option v-for="c in sectionCodes" :key="c.code" :value="c.code">{{ c.code_name }}</option>
      </select>
      <!-- 지문유형(passage_type) 셀렉트박스 -->
      <select
        v-if="parsed"
        :value="parsed.passage_type"
        class="rounded border border-purple-200 bg-purple-50 px-1.5 py-0.5 text-xs text-purple-700 focus:border-purple-400 focus:outline-none"
        @change="emit('code-change', item, 'passage_type', $event.target.value)"
      >
        <option value="">지문유형</option>
        <option v-for="c in passageTypeCodes" :key="c.code" :value="c.code">{{ c.code_name }}</option>
      </select>
      <!-- 문제유형(question_type) 셀렉트박스 -->
      <select
        v-if="parsed"
        :value="parsed.question_type"
        class="rounded border border-green-200 bg-green-50 px-1.5 py-0.5 text-xs text-green-700 focus:border-green-400 focus:outline-none"
        @change="emit('code-change', item, 'question_type', $event.target.value)"
      >
        <option value="">문제유형</option>
        <option v-for="c in questionTypeCodes" :key="c.code" :value="c.code">{{ c.code_name }}</option>
      </select>
      <span v-if="parsed && parsed.score" class="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700">
        {{ parsed.score }}점
      </span>
    </div>
  </div>

  <!-- MP3 플레이어 영역 — v-show로 DOM 유지하여 audio 요소 재생성 방지 -->
  <div class="mb-3">
    <div
      v-show="mp3Url"
      class="flex items-center gap-2 rounded border border-gray-200 bg-gray-50 px-3 py-2"
    >
      <audio controls preload="none" class="h-8 w-full" :src="mp3Url || ''">
        브라우저에서 오디오를 지원하지 않습니다.
      </audio>
    </div>
    <!-- MP3 파일 없음 — 비활성 플레이어 -->
    <div
      v-show="!mp3Url"
      class="flex items-center gap-2 rounded border border-gray-200 bg-gray-100 px-3 py-2 text-gray-400"
    >
      <!-- 음소거 아이콘 -->
      <svg
        class="h-5 w-5 shrink-0"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M17.25 9.75L19.5 12m0 0l2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6l4.72-3.15a.75.75 0 011.28.53v13.74a.75.75 0 01-1.28.53L6.75 14.25H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z"
        />
      </svg>
      <span class="text-sm">음성 파일 없음</span>
    </div>
  </div>

  <!-- 본문 -->
  <template v-if="parsed">
    <!-- 문제 번호 -->
    <p class="mb-1 text-sm font-medium text-gray-800">{{ item.question_no }}.</p>

    <!-- 문항 이미지 (question_img) — 문항번호 바로 아래 -->
    <div v-if="parsed.question_img" class="mb-3">
      <img
        :src="getImageUrl(parsed.question_img)"
        :alt="`문항 ${item.question_no} 이미지`"
        class="max-w-full rounded border border-gray-200"
      />
    </div>

    <!-- question_text (듣기: 대화 지문 등 표시) -->
    <div
      v-if="parsed.question_text"
      class="mb-3 rounded border border-gray-300 bg-white p-3 text-sm leading-relaxed text-gray-700"
    >
      <p class="whitespace-pre-wrap">{{ parsed.question_text }}</p>
    </div>

    <!-- 선택지: 이미지 (2열 그리드, 번호 옆에 이미지 가로 배치) -->
    <div
      v-if="parsed.choices && parsed.choices.length && isChoiceImage(parsed.choices[0])"
      class="mb-2 grid grid-cols-2 gap-2"
    >
      <div
        v-for="(choice, ci) in parsed.choices"
        :key="ci"
        class="flex items-center gap-2 rounded border p-1"
        :class="ci + 1 === Number(correctAnswer) ? 'border-blue-400 bg-blue-50' : 'border-gray-200'"
      >
        <span class="shrink-0 text-sm font-medium text-gray-500">{{
          String.fromCodePoint(0x2460 + ci)
        }}</span>
        <img
          :src="getImageUrl(getChoiceImageFilename(choice))"
          :alt="`선택지 ${ci + 1}`"
          class="min-w-0 flex-1"
        />
      </div>
    </div>
    <div v-else-if="parsed.choices" class="mb-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
      <span
        v-for="(choice, ci) in parsed.choices"
        :key="ci"
        :class="ci + 1 === Number(correctAnswer) ? 'font-medium text-blue-700' : 'text-gray-700'"
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
          :class="parseFeedback(fb).isCorrect ? 'font-medium text-blue-700' : 'text-gray-600'"
        >
          <span class="shrink-0">{{ parseFeedback(fb).label }}</span>
          <span>{{ parseFeedback(fb).text }}</span>
        </div>
      </div>
      <p v-else class="py-2 text-sm text-gray-400">피드백 데이터가 없습니다.</p>
    </div>
  </template>
  <p v-else class="text-sm text-gray-400">JSON 파싱 불가</p>
</template>
