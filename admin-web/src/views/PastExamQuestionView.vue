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
import { bulkSave, generateFeedback, generateFeedbackSingle, updateQuestionSingle } from '@/api/examQuestion';
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
    const state = { text: prettyPrint(raw), parsed: item._parsed, error: false };
    /* 문제 항목은 피드백 편집 상태도 관리 */
    if (item._type === 'question') {
      state.feedbackText = prettyPrint(item.feedback_json);
      state.feedbackParsed = item._feedbackParsed;
      state.feedbackError = false;
      state.activeTab = 'question';
    }
    editStates.set(key, state);
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
      const state = { text: prettyPrint(raw), parsed: item._parsed, error: false };
      if (item._type === 'question') {
        state.feedbackText = prettyPrint(item.feedback_json);
        state.feedbackParsed = item._feedbackParsed;
        state.feedbackError = false;
        state.activeTab = 'question';
      }
      editStates.set(key, state);
    });
  }
);

/**
 * 좌측 JSON 편집 시 실시간 파싱하여 우측 UI에 반영한다.
 * 파싱 실패 시 마지막 유효 parsed를 유지하여 우측 깨짐을 방지한다.
 */
function handleJsonEdit(item, event) {
  const state = getEditState(item);
  const isFeedbackTab = item._type === 'question' && state.activeTab === 'feedback';

  if (isFeedbackTab) {
    state.feedbackText = event.target.value;
    try {
      state.feedbackParsed = JSON.parse(state.feedbackText);
      state.feedbackError = false;
    } catch {
      state.feedbackError = true;
    }
  } else {
    state.text = event.target.value;
    try {
      state.parsed = JSON.parse(state.text);
      state.error = false;
    } catch {
      state.error = true;
    }
  }
}

/** 좌측 JSON 탭 전환 (문제 항목 전용) */
function setJsonTab(item, tab) {
  getEditState(item).activeTab = tab;
}

/** 현재 활성 탭에 해당하는 JSON 텍스트 반환 */
function getActiveJsonText(item) {
  const state = getEditState(item);
  if (item._type === 'question' && state.activeTab === 'feedback') return state.feedbackText;
  return state.text;
}

/** 현재 활성 탭의 에러 상태 반환 */
function getActiveJsonError(item) {
  const state = getEditState(item);
  if (item._type === 'question' && state.activeTab === 'feedback') return state.feedbackError;
  return state.error;
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
 * 전체 문제/지시문 일괄 저장
 * 모든 항목의 편집된 JSON 텍스트를 검증 후 일괄 저장한다.
 */
async function handleSaveAll() {
  if (!store.selectedExamKey || store.mergedItems.length === 0) return;

  const payload = { questions: [], instructions: [] };

  /* 모든 항목의 JSON 유효성 검증 및 payload 구성 */
  for (const item of store.mergedItems) {
    const state = getEditState(item);

    /* JSON 유효성 검증 */
    if (state.error || (item._type === 'question' && state.feedbackError)) {
      const label =
        item._type === 'question' ? `${item.question_no}번 문제` : `지시문 ${item.ins_no}`;
      alert(`${label}의 JSON 형식이 올바르지 않습니다. 수정 후 다시 시도하세요.`);
      return;
    }

    /* 편집된 텍스트를 minify하여 저장용 JSON 문자열로 변환 */
    let jsonForSave;
    try {
      jsonForSave = JSON.stringify(JSON.parse(state.text));
    } catch {
      const label =
        item._type === 'question' ? `${item.question_no}번 문제` : `지시문 ${item.ins_no}`;
      alert(`${label}의 JSON 형식이 올바르지 않습니다.`);
      return;
    }

    if (item._type === 'question') {
      const parsed = state.parsed || {};
      const questionData = {
        question_no: item.question_no,
        section: parsed.section || item.section,
        question_type: parsed.type || item.question_type,
        struct_type: item.struct_type,
        question_json: jsonForSave,
        score: parsed.score || item.score,
        difficulty: item.difficulty
      };
      /* feedback_json이 있으면 함께 저장 */
      if (state.feedbackText && state.feedbackText.trim() !== '{}') {
        try {
          questionData.feedback_json = JSON.stringify(JSON.parse(state.feedbackText));
        } catch {
          alert(`${item.question_no}번 문제의 피드백 JSON 형식이 올바르지 않습니다.`);
          return;
        }
      }
      payload.questions.push(questionData);
    } else {
      payload.instructions.push({
        ins_no: item.ins_no,
        ins_json: jsonForSave
      });
    }
  }

  confirmMessage.value = '전체 저장하시겠습니까?';
  confirmCallback.value = async () => {
    try {
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
  /* 편집 상태의 feedbackParsed 우선, 없으면 store 원본 사용 */
  const state = getEditState(item);
  const fbParsed = state.feedbackParsed || item._feedbackParsed;

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

  confirmMessage.value = `모든 문제에 대해 다국어 피드백을 생성하시겠습니까?\n\n(주의: Claude API를 호출하므로 시간도 오래 걸리고 Token 사용이 많을 수도 있습니다)`;
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

/**
 * 개별 문항 피드백 생성 버튼 클릭 핸들러
 * 해당 문항의 question_json을 기반으로 피드백을 생성한다.
 * (현재는 전체 일괄 생성 API를 호출 — 추후 단건 API로 변경 가능)
 */
async function handleGenerateFeedbackForItem(item) {
  if (!store.selectedExamKey) return;

  confirmMessage.value = `피드백을 생성하시겠습니까? Claude API를 사용합니다`;
  confirmCallback.value = async () => {
    feedbackGenerating.value = true;
    try {
      /* 좌측 문제 탭의 JSON 텍스트를 API에 전달 */
      const state = getEditState(item);
      const questionJson = JSON.stringify(JSON.parse(state.text));
      const res = await generateFeedbackSingle(questionJson);
      const feedbackJson = res.data?.feedback_json;

      if (feedbackJson) {
        /* 편집 상태에 반영 (DB 저장 안 함 — 사용자가 별도 '저장' 클릭) */
        const parsed = JSON.parse(feedbackJson);
        state.feedbackText = JSON.stringify(parsed, null, 2);
        state.feedbackParsed = parsed;
        state.feedbackError = false;
        /* 피드백 탭으로 전환하여 결과 즉시 확인 */
        state.activeTab = 'feedback';
      }
    } catch (error) {
      alert(error.detail || '피드백 생성에 실패했습니다.');
    } finally {
      feedbackGenerating.value = false;
    }
  };
  showConfirm.value = true;
}

/** 단건 저장 상태 */
const itemSaving = ref(false);

/**
 * 개별 문항 저장 버튼 클릭 핸들러
 * 문제 탭의 question_json과 피드백 탭의 feedback_json을 모두 DB에 업데이트한다.
 * 기존 row가 없으면 '전체 저장' 후 수정만 가능하다고 안내한다.
 */
async function handleSaveItemSingle(item) {
  if (!store.selectedExamKey) return;

  const state = getEditState(item);
  const questionNo = item.question_no;

  /* 문제 JSON 유효성 검증 */
  let questionMinified = null;
  if (state.text && state.text.trim()) {
    try {
      questionMinified = JSON.stringify(JSON.parse(state.text));
    } catch {
      alert('문제 JSON 형식이 올바르지 않습니다.');
      return;
    }
  }

  /* 피드백 JSON 유효성 검증 */
  let feedbackMinified = null;
  if (state.feedbackText && state.feedbackText.trim()) {
    try {
      feedbackMinified = JSON.stringify(JSON.parse(state.feedbackText));
    } catch {
      alert('피드백 JSON 형식이 올바르지 않습니다.');
      return;
    }
  }

  confirmMessage.value = `${questionNo}번 문제를 저장하시겠습니까?`;
  confirmCallback.value = async () => {
    itemSaving.value = true;
    try {
      await updateQuestionSingle(
        store.selectedExamKey, questionNo, questionMinified, feedbackMinified
      );
      alert('저장되었습니다.');
    } catch (error) {
      alert(error.detail || '저장에 실패했습니다.');
    } finally {
      itemSaving.value = false;
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

        <!-- 전체 변환(API) 화면 버튼 — 페이지 이동이므로 링크 스타일 + 화살표 아이콘 -->
        <button
          class="inline-flex items-center gap-1 rounded border border-blue-400 bg-blue-50 px-3 py-1.5 text-sm text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!store.selectedPdfKey"
          @click="handleConvertClick"
        >
          전체 변환(API) 화면
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
          </svg>
        </button>

        <!-- 가로 구분자 -->
        <div class="h-6 w-px bg-gray-300"></div>

        <!-- 전체 변환(파일 업로드) 버튼 -->
        <button
          class="rounded border border-gray-300 bg-gray-100 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!store.selectedExamKey"
          @click="$refs.jsonUploadInput.click()"
        >
          전체 변환(파일 업로드)
        </button>
        <input
          ref="jsonUploadInput"
          type="file"
          accept=".json"
          class="hidden"
          @change="handleJsonUploadSelect"
        />

        <!-- 전체 저장 버튼 -->
        <button
          class="rounded border border-gray-300 bg-gray-100 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="!store.selectedExamKey || store.mergedItems.length === 0"
          @click="handleSaveAll"
        >
          전체 저장
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
              <!-- 탭바 (문제 항목만 — 문제/피드백 전환) -->
              <div
                v-if="item._type === 'question'"
                class="mb-1 flex items-center gap-1 border-b border-gray-200 pb-1"
              >
                <button
                  class="rounded-t px-2.5 py-1 text-xs transition-colors"
                  :class="
                    getEditState(item).activeTab === 'question'
                      ? 'border-b-2 border-blue-500 font-medium text-blue-700'
                      : 'text-gray-400 hover:text-gray-600'
                  "
                  @click="setJsonTab(item, 'question')"
                >
                  문제
                </button>
                <button
                  class="rounded-t px-2.5 py-1 text-xs transition-colors"
                  :class="
                    getEditState(item).activeTab === 'feedback'
                      ? 'border-b-2 border-blue-500 font-medium text-blue-700'
                      : 'text-gray-400 hover:text-gray-600'
                  "
                  @click="setJsonTab(item, 'feedback')"
                >
                  피드백
                </button>
                <button
                  class="ml-auto rounded border border-purple-300 bg-purple-50 px-2 py-0.5 text-[11px] text-purple-700 hover:bg-purple-100 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="feedbackGenerating"
                  @click="handleGenerateFeedbackForItem(item)"
                >
                  {{ feedbackGenerating ? '생성 중...' : '피드백 생성(API)' }}
                </button>
                <button
                  class="rounded border border-gray-300 bg-gray-100 px-2 py-0.5 text-[11px] text-gray-700 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
                  :disabled="itemSaving"
                  @click="handleSaveItemSingle(item)"
                >
                  {{ itemSaving ? '저장 중...' : '저장' }}
                </button>
              </div>
              <!-- JSON 편집기 -->
              <div
                class="relative min-h-[80px] flex-1 overflow-hidden rounded border bg-gray-50"
                :class="getActiveJsonError(item) ? 'border-red-400' : 'border-gray-200'"
              >
                <!-- 구문 강조 표시 레이어 (시각적 표시만, 클릭 투과) -->
                <pre
                  :ref="(el) => setPreRef(index, el)"
                  class="pointer-events-none absolute inset-0 overflow-hidden whitespace-pre-wrap break-all p-2 font-mono text-xs leading-relaxed"
                  v-html="highlightJson(getActiveJsonText(item))"
                ></pre>
                <!-- 투명 입력 레이어 (실제 편집 수신, 컨테이너 꽉 채움) -->
                <textarea
                  :value="getActiveJsonText(item)"
                  spellcheck="false"
                  class="absolute inset-0 h-full w-full resize-none whitespace-pre-wrap break-all bg-transparent p-2 font-mono text-xs leading-relaxed text-transparent caret-gray-800 outline-none"
                  @input="handleJsonEdit(item, $event)"
                  @scroll="syncScroll(index, $event)"
                ></textarea>
              </div>
              <!-- JSON 에러 표시 -->
              <span v-if="getActiveJsonError(item)" class="mt-1 block text-xs text-red-500">
                JSON 형식 오류
              </span>
            </div>

            <!-- 우측: 시험지 UI (60%) -->
            <div class="w-3/5 min-w-0">
              <!-- ===== 지시문 ===== -->
              <template v-if="item._type === 'instruction'">
                <!-- 상단: 지시문 {no} [{no_list}] {score}점 -->
                <div class="mb-3 border-b border-gray-200 pb-2">
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
                <!-- 상단: {no}번(정답 색상) {section} {type} {score}점 -->
                <div class="mb-3 border-b border-gray-200 pb-2">
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
