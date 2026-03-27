<!--
  기출문항 변환(JSON) 페이지
  - 기출문제 관리 화면에서 "JSON 변환(일괄)" 버튼 클릭 시 이 페이지로 이동
  - 좌측: PDF 뷰어 (해당 파일 표시)
  - 우측: JSON 변환 버튼 클릭 시 Claude API SSE 스트리밍으로 JSON 결과 실시간 출력
  - 하단: 저장 버튼 (문제→tb_exam_question, 지시문→tb_exam_instruction)
-->
<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useExamQuestionStore } from '@/stores/examQuestion';
import { getInlineViewUrl } from '@/api/examFile';
import {
  convertPdfToJsonStream,
  bulkSave,
  getQuestionsAndInstructions,
  generateFeedback
} from '@/api/examQuestion';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';

const route = useRoute();
const router = useRouter();
const store = useExamQuestionStore();

/** route params에서 examKey, pdfKey 추출 */
const examKey = computed(() => Number(route.params.examKey) || null);
const pdfKey = computed(() => Number(route.params.pdfKey) || null);

/* ========== 상태 ========== */

/** 우측 탭 상태: 'question' | 'feedback' */
const activeTab = ref('question');

/** 문제 JSON 변환 결과 텍스트 */
const jsonText = ref('');

/** 피드백 JSON 텍스트 */
const feedbackJsonText = ref('');

/** 문제 변환 로딩 상태 */
const converting = ref(false);

/** 피드백 변환 로딩 상태 */
const feedbackConverting = ref(false);

/** 스트리밍 상태: idle | connecting | streaming | done | error | loaded */
const streamStatus = ref('idle');

/** JSON 변환(문제) 드롭다운 메뉴 표시 여부 */
const showConvertMenu = ref(false);

/** 피드백 변환 드롭다운 메뉴 표시 여부 */
const showFeedbackMenu = ref(false);

/** 선택된 AI 제공자 (드롭다운에서 선택 시 설정) */
const selectedAiProvider = ref('claude');

/** 토큰 사용량 정보 */
const tokenUsage = ref(null);

/** 저장 확인 다이얼로그 */
const showConfirm = ref(false);

/** 문제 JSON 변환 확인 다이얼로그 */
const showConvertConfirm = ref(false);

/** 피드백 JSON 변환 확인 다이얼로그 */
const showFeedbackConvertConfirm = ref(false);

/** JSON 결과 영역 ref (자동 스크롤용) */
const jsonContainer = ref(null);

/* ========== 계산된 속성 ========== */

/** PDF 인라인 뷰어 URL */
const pdfUrl = computed(() => {
  if (examKey.value && pdfKey.value) {
    return getInlineViewUrl(examKey.value, pdfKey.value);
  }
  return '';
});

/** 기출 제목 */
const examTitle = computed(() => {
  const info = store.selectedExam;
  if (!info) return '';
  const parts = [];
  if (info.exam_year) parts.push(info.exam_year + '년');
  if (info.round) parts.push('제' + info.round + '회');
  if (info.tpk_level_name) parts.push(info.tpk_level_name);
  if (info.section_name) parts.push(info.section_name);
  return parts.join(' ');
});

/** 파일명 */
const fileName = computed(() => {
  const info = store.selectedFile;
  return info ? info.file_name : '';
});

/** 스트리밍 상태에 따른 안내 메시지 */
const statusMessage = computed(() => {
  switch (streamStatus.value) {
    case 'connecting':
      return `${selectedAiProvider.value === 'gemini' ? 'Gemini' : 'Claude'} API 연결 중...`;
    case 'streaming':
      return '변환 중...';
    case 'done':
      if (tokenUsage.value) {
        return `변환 완료 (입력: ${tokenUsage.value.input_tokens.toLocaleString()}토큰 / 출력: ${tokenUsage.value.output_tokens.toLocaleString()}토큰)`;
      }
      return '변환 완료';
    case 'loaded':
      return '저장된 JSON을 불러왔습니다.';
    case 'error':
      return '변환 실패';
    default:
      return '';
  }
});

/* ========== 드롭다운 외부 클릭 닫기 ========== */

function handleOutsideClick() {
  showConvertMenu.value = false;
  showFeedbackMenu.value = false;
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick);
});

onUnmounted(() => {
  document.removeEventListener('click', handleOutsideClick);
});

/* ========== 초기 데이터 로드 ========== */

onMounted(async () => {
  /* store에 시험 옵션이 없으면 로드 (직접 URL 진입 대응) */
  if (store.examOptions.length === 0) {
    await store.fetchExamOptions();
  }
  /* store 선택 상태를 route params에 맞춰 설정 */
  if (examKey.value && store.selectedExamKey !== examKey.value) {
    await store.selectExam(examKey.value);
  }
  if (pdfKey.value && store.selectedPdfKey !== pdfKey.value) {
    store.selectFile(pdfKey.value);
  }

  /* 기존 저장된 JSON 로드 */
  if (examKey.value) {
    await loadSavedJson(examKey.value);
  }
});

/**
 * 기존 저장된 문제/지시문 데이터를 조회하여 원본 JSON 배열 형태로 복원한다.
 * @param {number} ek - 시험키 PK
 */
async function loadSavedJson(ek) {
  try {
    const res = await getQuestionsAndInstructions(ek);
    const data = res.data || {};
    const savedQuestions = data.questions || [];
    const savedInstructions = data.instructions || [];

    if (savedQuestions.length === 0 && savedInstructions.length === 0) return;

    /* 문제 탭: 지시문 + 문제를 번호순 정렬하여 JSON 배열로 복원 */
    const items = [];

    savedInstructions.forEach((ins) => {
      try {
        const parsed = JSON.parse(ins.ins_json);
        const firstNo = parsed.no_list && parsed.no_list.length ? parsed.no_list[0] : ins.ins_no;
        items.push({ _sortKey: firstNo, _isInstruction: true, data: parsed });
      } catch {
        /* 파싱 실패 항목은 건너뜀 */
      }
    });

    savedQuestions.forEach((q) => {
      try {
        const parsed = JSON.parse(q.question_json);
        items.push({ _sortKey: q.question_no, _isInstruction: false, data: parsed });
      } catch {
        /* 파싱 실패 항목은 건너뜀 */
      }
    });

    items.sort((a, b) => {
      if (a._sortKey !== b._sortKey) return a._sortKey - b._sortKey;
      if (a._isInstruction && !b._isInstruction) return -1;
      if (!a._isInstruction && b._isInstruction) return 1;
      return 0;
    });

    const jsonArray = items.map((item) => item.data);
    jsonText.value = JSON.stringify(jsonArray, null, 2);

    /* 피드백 탭: 문제별 feedback_json을 { question_no: feedback } 형태로 복원 */
    const feedbackMap = {};
    savedQuestions.forEach((q) => {
      if (q.feedback_json) {
        try {
          feedbackMap[q.question_no] = JSON.parse(q.feedback_json);
        } catch {
          /* 파싱 실패 시 건너뜀 */
        }
      }
    });
    if (Object.keys(feedbackMap).length > 0) {
      feedbackJsonText.value = JSON.stringify(feedbackMap, null, 2);
    }

    streamStatus.value = 'loaded';
  } catch {
    /* 조회 실패 시 무시 */
  }
}

/* ========== 자동 스크롤 ========== */

function scrollToBottom() {
  nextTick(() => {
    if (jsonContainer.value) {
      jsonContainer.value.scrollTop = jsonContainer.value.scrollHeight;
    }
  });
}

/* ========== 액션 ========== */

/**
 * JSON 변환(문제) 드롭다운에서 AI 제공자 선택 시 호출
 * @param {string} provider - 'claude' 또는 'gemini'
 */
function handleConvertWithProvider(provider) {
  showConvertMenu.value = false;
  if (!examKey.value || !pdfKey.value) return;
  selectedAiProvider.value = provider;
  showConvertConfirm.value = true;
}

/** 변환 확인 후 실행 — 선택된 AI API SSE 스트리밍 호출 */
async function confirmConvert() {
  showConvertConfirm.value = false;

  converting.value = true;
  streamStatus.value = 'connecting';
  jsonText.value = '';
  tokenUsage.value = null;

  try {
    await convertPdfToJsonStream(examKey.value, pdfKey.value, (event) => {
      switch (event.type) {
        case 'start':
          streamStatus.value = 'streaming';
          break;
        case 'text_delta':
          jsonText.value += event.data.text;
          scrollToBottom();
          break;
        case 'done':
          streamStatus.value = 'done';
          tokenUsage.value = event.data.token_usage;
          if (event.data.stop_reason === 'max_tokens') {
            alert(
              'AI 응답이 최대 토큰 한도에 도달하여 JSON이 잘렸을 수 있습니다.\n' +
                '저장 전에 JSON이 완전한지 확인해 주세요.'
            );
          }
          break;
        case 'error':
          streamStatus.value = 'error';
          alert(event.data.detail || 'PDF 변환에 실패했습니다.');
          break;
      }
    }, selectedAiProvider.value);
  } catch {
    streamStatus.value = 'error';
    alert('PDF 변환 중 네트워크 오류가 발생했습니다.');
  } finally {
    converting.value = false;
  }
}

/**
 * 피드백 변환 드롭다운에서 AI 제공자 선택 시 호출
 * @param {string} provider - 'claude' 또는 'gemini'
 */
function handleFeedbackConvertWithProvider(_provider) {
  showFeedbackMenu.value = false;
  alert('현재(26.03.27) 피드백은 일괄 생성할 수 없습니다. (단건 생성 또는 파일 업로드만 가능)');
}

/**
 * 피드백 변환 확인 후 실행
 * exam_key 기반 일괄 API로 모든 문제의 피드백을 생성한다.
 * DB에 저장된 question_json을 서버에서 조회하여 처리한다.
 */
async function confirmFeedbackConvert() {
  showFeedbackConvertConfirm.value = false;

  if (!examKey.value) {
    alert('시험 정보가 없습니다.');
    return;
  }

  feedbackConverting.value = true;

  try {
    const res = await generateFeedback(examKey.value, selectedAiProvider.value);
    const data = res.data || {};
    const msg = `피드백 변환 완료\n- 전체: ${data.total}건\n- 성공: ${data.success}건\n- 실패: ${data.failed}건`;

    /* 피드백 결과를 다시 로드하여 피드백 탭에 표시 */
    await loadSavedJson(examKey.value);

    /* 피드백 탭으로 전환 */
    activeTab.value = 'feedback';
    alert(msg);
  } catch (error) {
    alert(error.detail || '피드백 변환에 실패했습니다.');
  } finally {
    feedbackConverting.value = false;
  }
}

/** 복사 버튼 */
function handleCopy() {
  if (!jsonText.value) return;
  navigator.clipboard.writeText(jsonText.value).then(() => {
    alert('클립보드에 복사되었습니다.');
  });
}

/** 다운로드 버튼 */
function handleDownload() {
  if (!jsonText.value) return;
  const blob = new Blob([jsonText.value], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `exam_${examKey.value}_converted.json`;
  a.click();
  URL.revokeObjectURL(url);
}

/** 저장 버튼 클릭 → 확인 다이얼로그 표시 */
function handleSave() {
  if (!jsonText.value) {
    alert('변환된 JSON 데이터가 없습니다.');
    return;
  }
  showConfirm.value = true;
}

/**
 * JSON 텍스트에서 마크다운 코드블록을 제거하고 순수 JSON만 추출한다.
 */
function cleanJsonText(text) {
  let cleaned = text.trim();
  const codeBlockMatch = cleaned.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?\s*```$/);
  if (codeBlockMatch) {
    cleaned = codeBlockMatch[1].trim();
  }
  return cleaned;
}

/**
 * 저장 확인 후 실행
 * JSON을 파싱하여 문제/지시문으로 분리하고 일괄 저장
 */
async function confirmSave() {
  showConfirm.value = false;

  try {
    let items;
    try {
      items = JSON.parse(cleanJsonText(jsonText.value));
    } catch {
      alert('JSON 형식이 올바르지 않습니다.');
      return;
    }

    if (!Array.isArray(items)) {
      alert('JSON이 배열 형식이 아닙니다.');
      return;
    }

    const questions = [];
    const instructions = [];
    let insCounter = 1;

    for (const item of items) {
      if (item.item_type === 'I') {
        instructions.push({
          ins_no: insCounter++,
          ins_json: JSON.stringify(item)
        });
      } else if (item.item_type === 'Q') {
        questions.push({
          question_no: item.no,
          section: item.section || null,
          question_type: item.type || null,
          struct_type: null,
          question_json: JSON.stringify(item),
          score: item.score || null,
          difficulty: null
        });
      }
    }

    await bulkSave(examKey.value, { questions, instructions });
    alert('저장되었습니다.');
  } catch (error) {
    alert(error.detail || '저장에 실패했습니다.');
  }
}

/** 뒤로가기 — 기출문제 관리 화면으로 복귀 */
function goBack() {
  router.push({ name: 'pastExamQuestions' });
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 서브 타이틀 + 뒤로가기 -->
    <div class="mb-4 flex items-center gap-2">
      <button
        class="flex h-8 w-8 items-center justify-center rounded-full text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
        title="기출문제 관리로 돌아가기"
        @click="goBack"
      >
        <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <h2 class="text-xl font-bold text-gray-800">기출문항 변환(JSON)</h2>
    </div>

    <!-- 기출 제목 + 파일명 -->
    <div class="mb-4 rounded border border-gray-300 bg-gray-50 px-4 py-3">
      <p class="text-base font-bold text-gray-800">{{ examTitle }}</p>
      <p v-if="fileName" class="mt-1 text-sm text-gray-500">{{ fileName }}</p>
    </div>

    <!-- 하위 타이틀 + 버튼 영역 -->
    <div class="mb-2 flex items-center justify-between">
      <!-- 스트리밍 상태 메시지 -->
      <div class="flex items-center gap-2 text-sm text-gray-500">
        <svg
          v-if="streamStatus === 'connecting' || streamStatus === 'streaming'"
          class="h-4 w-4 animate-spin text-blue-500"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>{{ statusMessage }}</span>
      </div>
      <div class="flex gap-2">
        <!-- JSON 변환(문제) 드롭다운 버튼 -->
        <div class="relative">
          <button
            class="inline-flex items-center gap-1 rounded-md border border-blue-300 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 disabled:cursor-not-allowed disabled:border-gray-200 disabled:bg-gray-50 disabled:text-gray-400"
            :disabled="converting || feedbackConverting"
            @click.stop="showConvertMenu = !showConvertMenu; showFeedbackMenu = false"
          >
            {{ converting ? '변환 중...' : 'JSON 변환(문제)' }}
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <!-- 드롭다운 메뉴 -->
          <div
            v-if="showConvertMenu"
            class="absolute right-0 z-10 mt-1 w-44 rounded-md border border-gray-200 bg-white py-1 shadow-lg"
          >
            <button
              class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 hover:bg-blue-50"
              @click="handleConvertWithProvider('claude')"
            >
              <span class="inline-block h-2 w-2 rounded-full bg-orange-400"></span>
              Claude
            </button>
            <button
              class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 hover:bg-blue-50"
              @click="handleConvertWithProvider('gemini')"
            >
              <span class="inline-block h-2 w-2 rounded-full bg-blue-400"></span>
              Gemini
            </button>
          </div>
        </div>

        <!-- JSON 변환(피드백) 드롭다운 버튼 -->
        <div class="relative">
          <button
            class="inline-flex items-center gap-1 rounded-md border border-purple-300 bg-purple-50 px-4 py-1.5 text-sm font-medium text-purple-700 transition-colors hover:bg-purple-100 disabled:cursor-not-allowed disabled:border-gray-200 disabled:bg-gray-50 disabled:text-gray-400"
            :disabled="feedbackConverting || converting || !jsonText"
            @click.stop="showFeedbackMenu = !showFeedbackMenu; showConvertMenu = false"
          >
            {{ feedbackConverting ? '변환 중...' : 'JSON 변환(피드백)' }}
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <!-- 드롭다운 메뉴 -->
          <div
            v-if="showFeedbackMenu"
            class="absolute right-0 z-10 mt-1 w-44 rounded-md border border-gray-200 bg-white py-1 shadow-lg"
          >
            <button
              class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 hover:bg-purple-50"
              @click="handleFeedbackConvertWithProvider('claude')"
            >
              <span class="inline-block h-2 w-2 rounded-full bg-orange-400"></span>
              Claude
            </button>
            <button
              class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 hover:bg-purple-50"
              @click="handleFeedbackConvertWithProvider('gemini')"
            >
              <span class="inline-block h-2 w-2 rounded-full bg-blue-400"></span>
              Gemini
            </button>
          </div>
        </div>
        <button
          class="rounded-md px-3 py-1.5 text-sm text-gray-600 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:text-gray-300"
          :disabled="!jsonText"
          @click="handleCopy"
        >
          복사
        </button>
        <button
          class="rounded-md px-3 py-1.5 text-sm text-gray-600 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:text-gray-300"
          :disabled="!jsonText"
          @click="handleDownload"
        >
          다운로드
        </button>
        <button
          class="rounded-md border border-gray-300 bg-gray-100 px-5 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200 disabled:cursor-not-allowed disabled:border-gray-200 disabled:bg-gray-50 disabled:text-gray-400"
          :disabled="!jsonText || converting"
          @click="handleSave"
        >
          저장
        </button>
      </div>
    </div>

    <!-- 본문: 좌측 PDF + 우측 JSON -->
    <div class="flex min-h-0 flex-1 overflow-hidden rounded border border-gray-300">
      <!-- 좌측: PDF 뷰어 -->
      <div class="w-1/2 border-r border-gray-200">
        <div v-if="pdfUrl" class="h-full">
          <iframe :src="pdfUrl" class="h-full w-full border-0"></iframe>
        </div>
        <div v-else class="flex h-full items-center justify-center text-gray-400">
          PDF 파일 없음
        </div>
      </div>

      <!-- 우측: JSON 결과 (문제/피드백 탭) -->
      <div class="flex w-1/2 flex-col">
        <!-- 탭바 -->
        <div class="flex border-b border-gray-700 bg-gray-800 px-4">
          <button
            class="px-4 py-2 text-sm transition-colors"
            :class="
              activeTab === 'question'
                ? 'border-b-2 border-blue-400 font-medium text-blue-400'
                : 'text-gray-400 hover:text-gray-200'
            "
            @click="activeTab = 'question'"
          >
            문제
          </button>
          <button
            class="px-4 py-2 text-sm transition-colors"
            :class="
              activeTab === 'feedback'
                ? 'border-b-2 border-blue-400 font-medium text-blue-400'
                : 'text-gray-400 hover:text-gray-200'
            "
            @click="activeTab = 'feedback'"
          >
            피드백
          </button>
        </div>

        <!-- 문제 탭 내용 -->
        <div v-show="activeTab === 'question'" ref="jsonContainer" class="flex-1 overflow-auto bg-gray-900 p-4">
          <pre
            v-if="jsonText"
            class="whitespace-pre-wrap text-sm leading-relaxed text-green-400"
            >{{ jsonText }}</pre
          >
          <div
            v-else-if="streamStatus === 'connecting'"
            class="flex h-full items-center justify-center text-gray-400"
          >
            <div class="text-center">
              <svg
                class="mx-auto mb-3 h-8 w-8 animate-spin text-blue-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <p>{{ selectedAiProvider === 'gemini' ? 'Gemini' : 'Claude' }} API 연결 중...</p>
              <p class="mt-1 text-xs text-gray-500">PDF 파일을 분석하고 있습니다.</p>
            </div>
          </div>
          <div v-else class="flex h-full items-center justify-center text-gray-500">
            'JSON 변환(일괄)' 버튼을 클릭하세요.
          </div>
        </div>

        <!-- 피드백 탭 내용 -->
        <div v-show="activeTab === 'feedback'" class="flex-1 overflow-auto bg-gray-900 p-4">
          <pre
            v-if="feedbackJsonText"
            class="whitespace-pre-wrap text-sm leading-relaxed text-green-400"
            >{{ feedbackJsonText }}</pre
          >
          <div v-else class="flex h-full items-center justify-center text-gray-500">
            피드백 데이터가 없습니다.
          </div>
        </div>
      </div>
    </div>

    <!-- JSON 변환 확인 다이얼로그 -->
    <ConfirmDialog
      :visible="showConvertConfirm"
      :message="`JSON 변환을 시작하시겠습니까?\n(주의: ${selectedAiProvider === 'gemini' ? 'Gemini' : 'Claude'} API를 호출하여 시간이 오래 걸리거나 토큰 사용량이 많아질 수 있습니다)`"
      @confirm="confirmConvert"
      @cancel="showConvertConfirm = false"
    />

    <!-- 저장 확인 다이얼로그 -->
    <ConfirmDialog
      :visible="showConfirm"
      message="저장하시겠습니까?"
      @confirm="confirmSave"
      @cancel="showConfirm = false"
    />

    <!-- 피드백 변환 확인 다이얼로그 -->
    <ConfirmDialog
      :visible="showFeedbackConvertConfirm"
      :message="`피드백 JSON 변환을 시작하시겠습니까?\n(주의: 문제 수만큼 ${selectedAiProvider === 'gemini' ? 'Gemini' : 'Claude'} API를 호출합니다)`"
      @confirm="confirmFeedbackConvert"
      @cancel="showFeedbackConvertConfirm = false"
    />
  </div>
</template>
