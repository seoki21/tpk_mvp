<!--
  기출문제 관리 페이지
  - 상단 조회조건: 기출문제 selectbox + 파일 selectbox + 파일 아이콘(JSON 변환 팝업) + 검수완료 버튼
  - 하단: 문제 목록(JSON → 화면) — 좌측 JSON 텍스트 + 우측 UI 렌더링
  - 마운트 시 기출문제 목록을 조회한다.
-->
<script setup>
import { onMounted, ref, reactive, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useExamQuestionStore } from '@/stores/examQuestion';
import { bulkSave, generateFeedback } from '@/api/examQuestion';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';

const router = useRouter();
const store = useExamQuestionStore();

/* ========== 확인 다이얼로그 ========== */
const showConfirm = ref(false);
const confirmMessage = ref('');
const confirmCallback = ref(null);

/* ========== 좌측 JSON 편집 상태 관리 ========== */

/**
 * 각 항목의 편집 중인 JSON 텍스트를 관리하는 Map
 * key: "q_{question_no}" 또는 "i_{ins_no}"
 * value: { text: string, parsed: object|null, error: boolean }
 */
const editStates = reactive(new Map());

/** pre 요소 참조 (스크롤 동기화용) */
const preRefs = ref({});

/**
 * 항목의 고유 키를 생성한다.
 * @param {Object} item - mergedItems의 항목
 */
function itemKey(item) {
  return item._type === 'question' ? `q_${item.question_no}` : `i_${item.ins_no}`;
}

/**
 * JSON 문자열을 pretty-print 형태로 변환한다.
 * 파싱 실패 시 원본 문자열 그대로 반환.
 */
function prettyPrint(jsonStr) {
  if (!jsonStr) return '{}';
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2);
  } catch {
    return jsonStr;
  }
}

/**
 * 항목의 편집 상태를 반환한다.
 * editStates에 없는 경우 기본값을 생성하여 반환.
 */
function getEditState(item) {
  const key = itemKey(item);
  if (!editStates.has(key)) {
    const raw = item._type === 'question' ? item.question_json : item.ins_json;
    editStates.set(key, { text: prettyPrint(raw), parsed: item._parsed, error: false });
  }
  return editStates.get(key);
}

/**
 * mergedItems가 변경될 때(시험/파일 선택 변경) 편집 상태를 초기화한다.
 */
watch(
  () => store.mergedItems,
  (items) => {
    editStates.clear();
    items.forEach((item) => {
      const key = itemKey(item);
      const raw = item._type === 'question' ? item.question_json : item.ins_json;
      editStates.set(key, { text: prettyPrint(raw), parsed: item._parsed, error: false });
    });
  }
);

/**
 * 좌측 JSON 편집 시 실시간 파싱하여 우측 UI에 반영한다.
 * 파싱 실패 시 마지막 유효 parsed를 유지하여 우측 깨짐을 방지한다.
 */
function handleJsonEdit(item, event) {
  const state = getEditState(item);
  state.text = event.target.value;
  try {
    state.parsed = JSON.parse(state.text);
    state.error = false;
  } catch {
    state.error = true;
  }
}

/**
 * textarea 스크롤 시 pre 오버레이의 스크롤을 동기화한다.
 */
function syncScroll(index, event) {
  const pre = preRefs.value[index];
  if (pre) {
    pre.scrollTop = event.target.scrollTop;
    pre.scrollLeft = event.target.scrollLeft;
  }
}

/**
 * pre 요소 ref를 동적으로 설정하는 함수
 */
function setPreRef(index, el) {
  if (el) preRefs.value[index] = el;
}

/** 시험 선택 변경 */
async function handleExamChange(event) {
  const examKey = event.target.value ? Number(event.target.value) : null;
  await store.selectExam(examKey);
}

/** 파일 선택 변경 — 선택 후 문제/지시문 재조회 */
async function handleFileChange(event) {
  const pdfKey = event.target.value ? Number(event.target.value) : null;
  store.selectFile(pdfKey);
  if (store.selectedExamKey) {
    await store.fetchQuestionsAndInstructions(store.selectedExamKey);
  }
}

/** JSON 변환(일괄) 버튼 클릭 → 변환 페이지로 이동 */
function handleConvertClick() {
  if (!store.selectedExamKey || !store.selectedPdfKey) {
    alert('기출문제와 파일을 먼저 선택하세요.');
    return;
  }
  router.push({
    name: 'examConvert',
    params: { examKey: store.selectedExamKey, pdfKey: store.selectedPdfKey }
  });
}

/**
 * JSON 변환(업로드) 파일 선택 핸들러
 * 선택된 JSON 파일을 읽어 문제/지시문을 저장한다. (추후 구현)
 */
function handleJsonUploadSelect(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  alert(`선택된 파일: ${file.name}\n(업로드 처리는 추후 구현 예정)`);
  /* input 초기화 (같은 파일 재선택 가능하도록) */
  event.target.value = '';
}

/**
 * 개별 문제/지시문 저장 버튼
 * 편집된 JSON 텍스트를 기반으로 단건 저장
 */
async function handleSaveItem(item) {
  if (!store.selectedExamKey) return;

  /* 편집된 JSON 유효성 검증 */
  const state = getEditState(item);
  if (state.error) {
    alert('JSON 형식이 올바르지 않습니다. 수정 후 다시 시도하세요.');
    return;
  }

  /* 편집된 텍스트를 minify하여 저장용 JSON 문자열로 변환 */
  let jsonForSave;
  try {
    jsonForSave = JSON.stringify(JSON.parse(state.text));
  } catch {
    alert('JSON 형식이 올바르지 않습니다.');
    return;
  }

  confirmMessage.value = '저장하시겠습니까?';
  confirmCallback.value = async () => {
    try {
      const payload = { questions: [], instructions: [] };

      if (item._type === 'question') {
        /* 편집된 JSON에서 section, type, score 등도 반영 */
        const parsed = state.parsed || {};
        payload.questions.push({
          question_no: item.question_no,
          section: parsed.section || item.section,
          question_type: parsed.type || item.question_type,
          struct_type: item.struct_type,
          question_json: jsonForSave,
          score: parsed.score || item.score,
          difficulty: item.difficulty
        });
      } else {
        payload.instructions.push({
          ins_no: item.ins_no,
          ins_json: jsonForSave
        });
      }

      await bulkSave(store.selectedExamKey, payload);
      alert('저장되었습니다.');
      await store.fetchQuestionsAndInstructions(store.selectedExamKey);
    } catch (error) {
      alert(error.detail || '저장에 실패했습니다.');
    }
  };
  showConfirm.value = true;
}

/** 확인 다이얼로그 — 확인 */
function handleConfirm() {
  showConfirm.value = false;
  if (confirmCallback.value) confirmCallback.value();
}

/** 확인 다이얼로그 — 취소 */
function handleCancel() {
  showConfirm.value = false;
  confirmCallback.value = null;
}

/**
 * JSON 텍스트에 구문 강조 HTML을 적용한다.
 * 키(보라), 문자열 값(초록), 숫자(파랑), boolean/null(주황) 색상 적용.
 * 입력은 이미 pretty-print된 텍스트를 받으므로 재파싱하지 않는다.
 * 마지막에 줄바꿈을 추가하여 textarea와 높이를 맞춘다.
 */
function highlightJson(text) {
  if (!text) return '{}';
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return (
    escaped
      .replace(/"([^"]+)"(?=\s*:)/g, '<span class="text-purple-600">"$1"</span>')
      .replace(/:\s*"([^"]*)"/g, ': <span class="text-green-600">"$1"</span>')
      .replace(/:\s*(\d+\.?\d*)/g, ': <span class="text-blue-600">$1</span>')
      .replace(/:\s*(true|false|null)/g, ': <span class="text-orange-600">$1</span>') + '\n'
  );
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

/**
 * 문항의 정답 번호를 반환한다.
 * feedback_json → question_json(편집 상태) 순으로 조회.
 */
function getCorrectAnswer(item) {
  const fbParsed = item._feedbackParsed;
  if (fbParsed && fbParsed.correct_answer) return fbParsed.correct_answer;
  const parsed = getEditState(item).parsed;
  if (parsed && parsed.correct_answer) return parsed.correct_answer;
  return null;
}

/**
 * 문항의 피드백 데이터를 반환한다.
 * feedback_json(_feedbackParsed)이 있으면 다국어 탭 데이터를 구성하고,
 * 없으면 question_json 내 feedback을 'ko' 단일 탭으로 폴백.
 *
 * @param {Object} item - mergedItems의 문항 항목
 * @returns {{ tabs: { key: string, label: string, list: string[] }[], source: string }}
 */
function getFeedbackData(item) {
  /** 지원 언어 목록 (표시 순서 고정) */
  const langOrder = [
    { key: 'ko', label: '한국어' },
    { key: 'en', label: 'English' },
    { key: 'ja', label: '日本語' },
    { key: 'zh', label: '中文' },
    { key: 'vi', label: 'Tiếng Việt' }
  ];
  const fbParsed = item._feedbackParsed;

  if (fbParsed) {
    /*
     * feedback_json 구조 대응:
     *   형식 A: { "feedback": { "ko": [...], "en": [...] } }  (Claude API 생성)
     *   형식 B: { "ko": [...], "en": [...] }                  (번역 스크립트 생성)
     */
    const feedbackMap = fbParsed.feedback || fbParsed;
    const hasData = langOrder.some((l) => Array.isArray(feedbackMap[l.key]) && feedbackMap[l.key].length);
    if (hasData) {
      const tabs = langOrder.map((l) => ({
        key: l.key,
        label: l.label,
        list: Array.isArray(feedbackMap[l.key]) ? feedbackMap[l.key] : []
      }));
      return { tabs, source: 'feedback_json' };
    }
  }

  /* 폴백: question_json 내 feedback → 한국어 탭만 데이터 있고 나머지는 빈 상태 */
  const parsed = getEditState(item).parsed;
  if (parsed && parsed.feedback && parsed.feedback.length) {
    const tabs = langOrder.map((l) => ({
      key: l.key,
      label: l.label,
      list: l.key === 'ko' ? parsed.feedback : []
    }));
    return { tabs, source: 'question_json' };
  }

  return { tabs: [], source: 'none' };
}

/** 피드백 탭 활성 상태 관리 (key: itemKey, value: 활성 탭 lang 키) */
const feedbackActiveTab = reactive({});

/** 피드백 탭 선택 */
function setFeedbackTab(item, lang) {
  feedbackActiveTab[itemKey(item)] = lang;
}

/** 피드백 활성 탭 반환 (기본: 첫 번째 탭) */
function getActiveFeedbackTab(item) {
  const data = getFeedbackData(item);
  if (data.tabs.length === 0) return null;
  const saved = feedbackActiveTab[itemKey(item)];
  if (saved && data.tabs.some((t) => t.key === saved)) return saved;
  return data.tabs[0].key;
}

/** 활성 탭의 피드백 리스트 반환 */
function getActiveFeedbackList(item) {
  const data = getFeedbackData(item);
  const activeKey = getActiveFeedbackTab(item);
  const tab = data.tabs.find((t) => t.key === activeKey);
  return tab ? tab.list : [];
}

/**
 * 기출문제 selectbox 표시 텍스트 생성
 * 포맷: "{exam_year}년 제{round}회 {tpk_level_name} {section_name}"
 */
function getExamLabel(exam) {
  const parts = [];
  if (exam.exam_year) parts.push(exam.exam_year + '년');
  if (exam.round) parts.push('제' + exam.round + '회');
  if (exam.tpk_level_name) parts.push(exam.tpk_level_name);
  if (exam.section_name) parts.push(exam.section_name);
  return parts.join(' ') || `시험 ${exam.exam_key}`;
}

/* ========== 피드백 생성 상태 ========== */
const feedbackGenerating = ref(false);

/**
 * 피드백 생성 버튼 클릭 핸들러
 * Claude API를 통해 모든 문제의 다국어 피드백을 일괄 생성한다.
 */
async function handleGenerateFeedback() {
  if (!store.selectedExamKey) {
    alert('기출문제를 먼저 선택하세요.');
    return;
  }
  if (store.mergedItems.filter((i) => i._type === 'question').length === 0) {
    alert('피드백을 생성할 문제가 없습니다.');
    return;
  }

  confirmMessage.value = '모든 문제에 대해 다국어 피드백을 생성하시겠습니까?\n\n(주의:Claude API를 호출하므로 시간도 오래 걸리고 Token 사용이 많을 수도 있습니다)';
  confirmCallback.value = async () => {
    feedbackGenerating.value = true;
    try {
      const res = await generateFeedback(store.selectedExamKey);
      const data = res.data || {};
      const msg = `피드백 생성 완료\n- 전체: ${data.total}건\n- 성공: ${data.success}건\n- 실패: ${data.failed}건`;
      alert(msg);
      /* 목록 새로고침하여 feedback_json 반영 */
      await store.fetchQuestionsAndInstructions(store.selectedExamKey);
    } catch (error) {
      alert(error.detail || '피드백 생성에 실패했습니다.');
    } finally {
      feedbackGenerating.value = false;
    }
  };
  showConfirm.value = true;
}

/** 기출문제 목록 재조회 */
function handleRetryExamOptions() {
  store.fetchExamOptions();
}

/* ========== 초기 데이터 로드 ========== */
onMounted(() => {
  store.fetchExamOptions();
});
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">기출문제 관리</h2>

    <!-- 상단 조회조건 -->
    <div class="mb-4 flex items-center gap-4 rounded border border-gray-300 bg-gray-50 px-4 py-3">
      <!-- 기출문제 selectbox -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">기출문제</label>
        <select
          :value="store.selectedExamKey || ''"
          class="min-w-[260px] rounded border border-gray-300 px-3 py-1.5 text-sm"
          :disabled="store.examOptionsLoading"
          @change="handleExamChange"
        >
          <option value="">{{ store.examOptionsLoading ? '조회 중...' : '선택하세요' }}</option>
          <option v-for="exam in store.examOptions" :key="exam.exam_key" :value="exam.exam_key">
            {{ getExamLabel(exam) }}
          </option>
        </select>
        <!-- 에러 발생 시 메시지 + 재조회 버튼 -->
        <template v-if="store.examOptionsError && store.examOptions.length === 0">
          <span class="text-xs text-red-500">{{ store.examOptionsError }}</span>
          <button
            class="rounded border border-gray-300 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50"
            @click="handleRetryExamOptions"
          >
            재조회
          </button>
        </template>
      </div>

      <!-- 파일 selectbox -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">파일</label>
        <select
          :value="store.selectedPdfKey || ''"
          class="min-w-[200px] rounded border border-gray-300 px-3 py-1.5 text-sm"
          :disabled="!store.selectedExamKey"
          @change="handleFileChange"
        >
          <option value="">선택하세요</option>
          <option v-for="file in store.fileOptions" :key="file.pdf_key" :value="file.pdf_key">
            {{ file.file_name }}
          </option>
        </select>

        <!-- JSON 변환 버튼 — 클릭 시 JSON 변환 팝업 -->
        <button
          class="rounded border border-blue-400 bg-blue-50 px-3 py-1.5 text-sm text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!store.selectedPdfKey"
          @click="handleConvertClick"
        >
          JSON 변환(일괄)
        </button>

        <!-- JSON 변환(업로드) 버튼 — 파일 선택 후 업로드 처리 (추후 구현) -->
        <button
          class="rounded border border-teal-400 bg-teal-50 px-3 py-1.5 text-sm text-teal-700 hover:bg-teal-100 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!store.selectedExamKey"
          @click="$refs.jsonUploadInput.click()"
        >
          JSON 변환(업로드)
        </button>
        <input
          ref="jsonUploadInput"
          type="file"
          accept=".json"
          class="hidden"
          @change="handleJsonUploadSelect"
        />

        <!-- 피드백 생성 버튼 -->
        <button
          class="rounded border border-purple-400 bg-purple-50 px-3 py-1.5 text-sm text-purple-700 hover:bg-purple-100 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!store.selectedExamKey || feedbackGenerating || store.mergedItems.length === 0"
          @click="handleGenerateFeedback"
        >
          {{ feedbackGenerating ? '피드백 생성 중...' : '피드백 생성' }}
        </button>
      </div>
    </div>

    <!-- 문제 목록(JSON → 화면) -->
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden rounded border border-gray-300">
      <div class="flex shrink-0 items-center justify-between border-b border-gray-300 bg-gray-50 px-4 py-2">
        <div>
          <span class="text-sm font-medium text-gray-700">문제 목록</span>
          <span class="ml-2 text-xs text-gray-400">※ JSON 데이터를 수정하면 우측 화면에서 실시간으로 결과를 확인할 수 있습니다</span>
        </div>
        <button
          class="rounded border border-gray-300 px-2.5 py-1 text-xs text-gray-600 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!store.selectedExamKey || store.mergedItems.length === 0"
        >
          모두 저장
        </button>
      </div>

      <!-- 스크롤 영역 — 부모 flex-1로 남은 높이 전체 사용 -->
      <div class="flex-1 overflow-y-auto">
        <!-- 데이터 없음 -->
        <div
          v-if="!store.loading && store.mergedItems.length === 0"
          class="flex h-40 items-center justify-center text-gray-400"
        >
          {{
            !store.selectedExamKey
              ? '기출문제를 선택하세요.'
              : !store.selectedPdfKey
                ? '파일을 선택하세요.'
                : '문제 데이터가 없습니다.'
          }}
        </div>

        <!-- 로딩 -->
        <div v-if="store.loading" class="flex h-40 items-center justify-center text-gray-400">
          조회 중...
        </div>

        <!-- 항목 목록 -->
        <div v-if="!store.loading && store.mergedItems.length > 0" class="divide-y divide-gray-200">
          <div v-for="(item, index) in store.mergedItems" :key="index" class="flex gap-4 p-4">
            <!-- 좌측: JSON 편집 영역 (40%, 오버레이 구문 강조, 우측과 같은 높이) -->
            <div class="flex w-2/5 shrink-0 flex-col">
              <div
                class="relative min-h-[80px] flex-1 overflow-hidden rounded border bg-gray-50"
                :class="getEditState(item).error ? 'border-red-400' : 'border-gray-200'"
              >
                <!-- 구문 강조 표시 레이어 (시각적 표시만, 클릭 투과) -->
                <pre
                  :ref="(el) => setPreRef(index, el)"
                  class="pointer-events-none absolute inset-0 overflow-hidden whitespace-pre-wrap break-all p-2 font-mono text-xs leading-relaxed"
                  v-html="highlightJson(getEditState(item).text)"
                ></pre>
                <!-- 투명 입력 레이어 (실제 편집 수신, 컨테이너 꽉 채움) -->
                <textarea
                  :value="getEditState(item).text"
                  spellcheck="false"
                  class="absolute inset-0 h-full w-full resize-none whitespace-pre-wrap break-all bg-transparent p-2 font-mono text-xs leading-relaxed text-transparent caret-gray-800 outline-none"
                  @input="handleJsonEdit(item, $event)"
                  @scroll="syncScroll(index, $event)"
                ></textarea>
              </div>
              <!-- JSON 에러 표시 -->
              <span v-if="getEditState(item).error" class="mt-1 block text-xs text-red-500">
                JSON 형식 오류
              </span>
            </div>

            <!-- 우측: 시험지 UI (60%) -->
            <div class="w-3/5 min-w-0">
              <!-- ===== 지시문 ===== -->
              <template v-if="item._type === 'instruction'">
                <!-- 상단: 지시문 {no} [{no_list}] {score}점 + 저장 -->
                <div class="mb-3 flex items-center justify-between border-b border-gray-200 pb-2">
                  <div class="flex items-baseline gap-2 text-sm">
                    <span class="font-bold text-gray-800">지시문 {{ item.ins_no }}</span>
                    <span
                      v-if="
                        getEditState(item).parsed &&
                        getEditState(item).parsed.no_list &&
                        getEditState(item).parsed.no_list.length
                      "
                      class="text-gray-500"
                    >
                      [{{ getEditState(item).parsed.no_list.join(', ') }}]
                    </span>
                    <span
                      v-if="getEditState(item).parsed && getEditState(item).parsed.score"
                      class="text-gray-500"
                    >
                      {{ getEditState(item).parsed.score }}점
                    </span>
                  </div>
                  <button
                    class="shrink-0 rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100"
                    @click="handleSaveItem(item)"
                  >
                    저장
                  </button>
                </div>
                <!-- 본문 -->
                <template v-if="getEditState(item).parsed">
                  <p
                    v-if="getEditState(item).parsed.full_sentence"
                    class="mb-2 text-sm leading-relaxed text-gray-800"
                  >
                    {{ getEditState(item).parsed.full_sentence }}
                  </p>
                  <div
                    v-if="getEditState(item).parsed.paragraph"
                    class="mt-2 rounded border border-gray-300 bg-white p-3 text-sm leading-relaxed text-gray-700"
                  >
                    <p class="whitespace-pre-wrap">{{ getEditState(item).parsed.paragraph }}</p>
                  </div>
                </template>
                <p v-else class="text-sm text-gray-400">JSON 파싱 불가</p>
              </template>

              <!-- ===== 문항 ===== -->
              <template v-if="item._type === 'question'">
                <!-- 상단: {no}번(정답 색상) {section} {type} {score}점 + 저장 -->
                <div class="mb-3 flex items-center justify-between border-b border-gray-200 pb-2">
                  <div class="flex items-baseline gap-2 text-sm">
                    <span
                      class="font-bold"
                      :class="
                        getCorrectAnswer(item)
                          ? 'rounded bg-blue-600 px-1.5 py-0.5 text-white'
                          : 'text-gray-800'
                      "
                    >
                      {{ item.question_no }}번
                      <template v-if="getCorrectAnswer(item)">
                        (정답: {{ getCorrectAnswer(item) }})
                      </template>
                    </span>
                    <span
                      v-if="getEditState(item).parsed && getEditState(item).parsed.section"
                      class="rounded bg-blue-50 px-1.5 py-0.5 text-blue-700"
                    >
                      {{ getEditState(item).parsed.section }}
                    </span>
                    <span
                      v-if="getEditState(item).parsed && getEditState(item).parsed.type"
                      class="rounded bg-green-50 px-1.5 py-0.5 text-green-700"
                    >
                      {{ getEditState(item).parsed.type }}
                    </span>
                    <span
                      v-if="getEditState(item).parsed && getEditState(item).parsed.score"
                      class="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700"
                    >
                      {{ getEditState(item).parsed.score }}점
                    </span>
                  </div>
                  <button
                    class="shrink-0 rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100"
                    @click="handleSaveItem(item)"
                  >
                    저장
                  </button>
                </div>
                <!-- 본문 -->
                <template v-if="getEditState(item).parsed">
                  <p
                    v-if="getEditState(item).parsed.full_sentence"
                    class="mb-2 text-sm leading-relaxed text-gray-800"
                  >
                    {{ getEditState(item).parsed.full_sentence }}
                  </p>
                  <div
                    v-if="getEditState(item).parsed.paragraph"
                    class="mb-3 rounded border border-gray-300 bg-white p-3 text-sm leading-relaxed text-gray-700"
                  >
                    <p class="whitespace-pre-wrap">
                      {{ getEditState(item).parsed.paragraph }}
                    </p>
                  </div>
                  <p
                    v-if="getEditState(item).parsed.question_text"
                    class="mb-2 text-sm leading-relaxed text-gray-800"
                  >
                    {{ item.question_no }}. {{ getEditState(item).parsed.question_text }}
                  </p>
                  <!-- 선택지 -->
                  <div
                    v-if="getEditState(item).parsed.choices"
                    class="mb-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm"
                  >
                    <span
                      v-for="(choice, ci) in getEditState(item).parsed.choices"
                      :key="ci"
                      class="text-gray-700"
                    >
                      {{ choice }}
                    </span>
                  </div>
                  <!-- 피드백 영역 (다국어 탭바) -->
                  <div
                    v-if="getFeedbackData(item).tabs.length"
                    class="mt-3 rounded border border-gray-100 bg-slate-50 px-3 pb-3 pt-2"
                  >
                    <!-- 탭바: 다국어 전환 -->
                    <div class="mb-2 flex items-center gap-1 border-b border-gray-200 pb-1">
                      <button
                        v-for="tab in getFeedbackData(item).tabs"
                        :key="tab.key"
                        class="rounded-t px-2.5 py-1 text-sm transition-colors"
                        :class="
                          getActiveFeedbackTab(item) === tab.key
                            ? 'border-b-2 border-blue-500 font-medium text-blue-700'
                            : 'text-gray-400 hover:text-gray-600'
                        "
                        @click="setFeedbackTab(item, tab.key)"
                      >
                        {{ tab.label }}
                      </button>
                    </div>
                    <!-- 피드백 리스트 (문제 텍스트와 동일한 text-sm) -->
                    <div v-if="getActiveFeedbackList(item).length" class="space-y-1">
                      <div
                        v-for="(fb, fi) in getActiveFeedbackList(item)"
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
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 확인 다이얼로그 -->
    <ConfirmDialog
      :visible="showConfirm"
      :message="confirmMessage"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    />
  </div>
</template>
