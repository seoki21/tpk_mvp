<!--
  기출문항 변환(JSON) 팝업 컴포넌트
  - 기출문항 관리 화면에서 "API 호출" 버튼 클릭 시 모달로 표시
  - JSON 변환(문제/피드백), 복사, 다운로드, 저장 기능 제공
  - PDF viewer는 제외하고 JSON 편집 영역만 표시
  - ExamConvertView.vue의 우측 영역 로직을 모달로 분리
-->
<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { useExamQuestionStore } from '@/stores/examQuestion';
import {
  convertPdfToJsonStream,
  bulkSave,
  getQuestionsAndInstructions
} from '@/api/examQuestion';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import AiProviderDropdown from '@/components/examQuestion/AiProviderDropdown.vue';
import { useToast } from '@/composables/useToast';

const props = defineProps({
  /** 팝업 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 시험키 */
  examKey: {
    type: Number,
    default: null
  },
  /** PDF 파일키 */
  pdfKey: {
    type: Number,
    default: null
  }
});

const emit = defineEmits(['close', 'saved']);

const store = useExamQuestionStore();
const toast = useToast();

/* ========== 상태 ========== */

/** 탭 상태: 'question' | 'feedback' */
const activeTab = ref('question');

/** 문제 탭 편집 가능 여부 */
const questionEditable = ref(false);

/** 피드백 탭 편집 가능 여부 */
const feedbackEditable = ref(false);

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

/** 선택된 AI 제공자 */
const selectedAiProvider = ref('claude');

/** 토큰 사용량 정보 */
const tokenUsage = ref(null);

/** 저장 확인 다이얼로그 */
const showConfirm = ref(false);

/** 문제 JSON 변환 확인 다이얼로그 */
const showConvertConfirm = ref(false);

/** JSON 결과 영역 ref (자동 스크롤용) */
const jsonContainer = ref(null);

/* ========== 계산된 속성 ========== */

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

/** 선택된 시험의 영역 코드 — PDF→JSON 변환 시 프롬프트 분기용 */
const examSection = computed(() => {
  const info = store.selectedExam;
  return info ? info.section : null;
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

/* ========== 팝업 열림 시 기존 데이터 로드 ========== */

watch(
  () => props.visible,
  async (val) => {
    if (val && props.examKey) {
      /* 상태 초기화 */
      activeTab.value = 'question';
      questionEditable.value = false;
      feedbackEditable.value = false;
      streamStatus.value = 'idle';
      tokenUsage.value = null;
      jsonText.value = '';
      feedbackJsonText.value = '';
      converting.value = false;
      feedbackConverting.value = false;

      /* 기존 저장된 JSON 로드 */
      await loadSavedJson(props.examKey);
    }
  }
);

/**
 * 기존 저장된 문제/지시문 데이터를 조회하여 원본 JSON 배열 형태로 복원한다.
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
      } catch { /* 파싱 실패 건너뜀 */ }
    });
    savedQuestions.forEach((q) => {
      try {
        const parsed = JSON.parse(q.question_json);
        items.push({ _sortKey: q.question_no, _isInstruction: false, data: parsed });
      } catch { /* 파싱 실패 건너뜀 */ }
    });
    items.sort((a, b) => {
      if (a._sortKey !== b._sortKey) return a._sortKey - b._sortKey;
      if (a._isInstruction && !b._isInstruction) return -1;
      if (!a._isInstruction && b._isInstruction) return 1;
      return 0;
    });
    jsonText.value = JSON.stringify(items.map((item) => item.data), null, 2);

    /* 피드백 탭: 문제별 feedback_json을 { question_no: feedback } 형태로 복원 */
    const feedbackMap = {};
    savedQuestions.forEach((q) => {
      if (q.feedback_json) {
        try { feedbackMap[q.question_no] = JSON.parse(q.feedback_json); } catch { /* */ }
      }
    });
    if (Object.keys(feedbackMap).length > 0) {
      feedbackJsonText.value = JSON.stringify(feedbackMap, null, 2);
    }
    streamStatus.value = 'loaded';
  } catch { /* 조회 실패 시 무시 */ }
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

/** JSON 변환(문제) 드롭다운에서 AI 제공자 선택 시 호출 */
function handleConvertWithProvider(provider) {
  if (!props.examKey || !props.pdfKey) return;
  selectedAiProvider.value = provider;
  showConvertConfirm.value = true;
}

/** 변환 확인 후 실행 — SSE 스트리밍 호출 */
async function confirmConvert() {
  showConvertConfirm.value = false;
  converting.value = true;
  streamStatus.value = 'connecting';
  jsonText.value = '';
  tokenUsage.value = null;

  try {
    await convertPdfToJsonStream(props.examKey, props.pdfKey, (event) => {
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
            toast.warning('AI 응답이 최대 토큰 한도에 도달하여 JSON이 잘렸을 수 있습니다.');
          }
          break;
        case 'error':
          streamStatus.value = 'error';
          toast.error(event.data.detail || 'PDF 변환에 실패했습니다.');
          break;
      }
    }, selectedAiProvider.value, examSection.value);
  } catch {
    streamStatus.value = 'error';
    toast.error('PDF 변환 중 네트워크 오류가 발생했습니다.');
  } finally {
    converting.value = false;
  }
}

/** 피드백 변환 드롭다운 (현재 미지원) */
function handleFeedbackConvertWithProvider() {
  toast.info('피드백 일괄 변환은 문제 목록 화면에서 개별 생성해 주세요.');
}

/** 복사 버튼 */
function handleCopy() {
  const text = activeTab.value === 'feedback' ? feedbackJsonText.value : jsonText.value;
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    toast.success('클립보드에 복사되었습니다.');
  });
}

/** 다운로드 버튼 */
function handleDownload() {
  const text = activeTab.value === 'feedback' ? feedbackJsonText.value : jsonText.value;
  if (!text) return;
  const suffix = activeTab.value === 'feedback' ? 'feedback' : 'converted';
  const blob = new Blob([text], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `exam_${props.examKey}_${suffix}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

/** 저장 버튼 클릭 → 확인 다이얼로그 표시 */
function handleSave() {
  if (!jsonText.value) {
    toast.warning('변환된 JSON 데이터가 없습니다.');
    return;
  }
  showConfirm.value = true;
}

/** JSON 텍스트에서 마크다운 코드블록을 제거하고 순수 JSON만 추출 */
function cleanJsonText(text) {
  let cleaned = text.trim();
  const codeBlockMatch = cleaned.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?\s*```$/);
  if (codeBlockMatch) cleaned = codeBlockMatch[1].trim();
  return cleaned;
}

/** 저장 확인 후 실행 */
async function confirmSave() {
  showConfirm.value = false;
  try {
    let items;
    try {
      items = JSON.parse(cleanJsonText(jsonText.value));
    } catch {
      toast.error('JSON 형식이 올바르지 않습니다.');
      return;
    }
    if (!Array.isArray(items)) {
      toast.error('JSON이 배열 형식이 아닙니다.');
      return;
    }
    const questions = [];
    const instructions = [];
    let insCounter = 1;
    for (const item of items) {
      if (item.item_type === 'I') {
        instructions.push({ ins_no: insCounter++, ins_json: JSON.stringify(item) });
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
    await bulkSave(props.examKey, { questions, instructions });
    toast.success('저장되었습니다.');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '저장에 실패했습니다.');
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="mx-4 flex h-[85vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-xl">
        <!-- 헤더 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <div>
            <h3 class="text-sm font-bold text-gray-800">API 호출</h3>
            <p class="mt-0.5 text-xs text-gray-500">{{ examTitle }}</p>
          </div>
          <button
            class="flex h-7 w-7 items-center justify-center rounded text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            @click="emit('close')"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- 버튼 영역 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-2">
          <!-- 스트리밍 상태 메시지 -->
          <div class="flex items-center gap-2 text-xs text-gray-500">
            <svg
              v-if="streamStatus === 'connecting' || streamStatus === 'streaming'"
              class="h-3.5 w-3.5 animate-spin text-blue-500"
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
            <AiProviderDropdown
              label="JSON 변환(문제)"
              loading-label="변환 중..."
              theme="blue"
              :loading="converting"
              :disabled="converting || feedbackConverting"
              @select="handleConvertWithProvider"
            />
            <AiProviderDropdown
              label="JSON 변환(피드백)"
              loading-label="변환 중..."
              theme="purple"
              :loading="feedbackConverting"
              :disabled="feedbackConverting || converting || !jsonText"
              @select="handleFeedbackConvertWithProvider"
            />
            <button
              class="btn btn-sm btn-ghost"
              :disabled="activeTab === 'question' ? !jsonText : !feedbackJsonText"
              @click="handleCopy"
            >
              복사
            </button>
            <button
              class="btn btn-sm btn-ghost"
              :disabled="activeTab === 'question' ? !jsonText : !feedbackJsonText"
              @click="handleDownload"
            >
              다운로드
            </button>
            <!-- 가로 구분선 -->
            <div class="h-6 w-px bg-gray-300"></div>
            <button
              class="btn btn-sm btn-primary"
              :disabled="!jsonText || converting"
              @click="handleSave"
            >
              저장
            </button>
          </div>
        </div>

        <!-- 본문: JSON 편집 영역 -->
        <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
          <!-- 탭바 -->
          <div class="flex items-center border-b border-gray-700 bg-gray-800 px-4">
            <button
              class="px-4 py-2 text-sm transition-colors"
              :class="activeTab === 'question' ? 'border-b-2 border-blue-400 font-medium text-blue-400' : 'text-gray-400 hover:text-gray-200'"
              @click="activeTab = 'question'"
            >
              문제
            </button>
            <button
              class="px-4 py-2 text-sm transition-colors"
              :class="activeTab === 'feedback' ? 'border-b-2 border-blue-400 font-medium text-blue-400' : 'text-gray-400 hover:text-gray-200'"
              @click="activeTab = 'feedback'"
            >
              피드백
            </button>
            <label
              v-show="activeTab === 'question'"
              class="ml-auto flex cursor-pointer items-center gap-1.5 text-xs text-gray-400"
            >
              <input v-model="questionEditable" type="checkbox" class="h-3.5 w-3.5 rounded border-gray-500 bg-gray-700 text-blue-500" />
              편집 가능
            </label>
            <label
              v-show="activeTab === 'feedback'"
              class="ml-auto flex cursor-pointer items-center gap-1.5 text-xs text-gray-400"
            >
              <input v-model="feedbackEditable" type="checkbox" class="h-3.5 w-3.5 rounded border-gray-500 bg-gray-700 text-blue-500" />
              편집 가능
            </label>
          </div>

          <!-- 문제 탭 내용 -->
          <div v-show="activeTab === 'question'" ref="jsonContainer" class="flex-1 overflow-auto bg-gray-900 p-4">
            <textarea
              v-if="jsonText && questionEditable"
              v-model="jsonText"
              class="h-full w-full resize-none border-0 bg-gray-900 font-mono text-sm leading-relaxed text-green-400 outline-none focus:ring-0"
              spellcheck="false"
            ></textarea>
            <pre v-else-if="jsonText" class="whitespace-pre-wrap text-sm leading-relaxed text-green-400">{{ jsonText }}</pre>
            <div v-else-if="streamStatus === 'connecting'" class="flex h-full items-center justify-center text-gray-400">
              <div class="text-center">
                <svg class="mx-auto mb-3 h-8 w-8 animate-spin text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <p>{{ selectedAiProvider === 'gemini' ? 'Gemini' : 'Claude' }} API 연결 중...</p>
              </div>
            </div>
            <div v-else class="flex h-full items-center justify-center text-gray-500">
              'JSON 변환(문제)' 버튼을 클릭하세요.
            </div>
          </div>

          <!-- 피드백 탭 내용 -->
          <div v-show="activeTab === 'feedback'" class="flex-1 overflow-auto bg-gray-900 p-4">
            <textarea
              v-if="feedbackJsonText && feedbackEditable"
              v-model="feedbackJsonText"
              class="h-full w-full resize-none border-0 bg-gray-900 font-mono text-sm leading-relaxed text-green-400 outline-none focus:ring-0"
              spellcheck="false"
            ></textarea>
            <pre v-else-if="feedbackJsonText" class="whitespace-pre-wrap text-sm leading-relaxed text-green-400">{{ feedbackJsonText }}</pre>
            <div v-else class="flex h-full items-center justify-center text-gray-500">
              피드백 데이터가 없습니다.
            </div>
          </div>
        </div>

        <!-- JSON 변환 확인 다이얼로그 -->
        <ConfirmDialog
          :visible="showConvertConfirm"
          :message="`JSON 변환을 시작하시겠습니까?\n(${selectedAiProvider === 'gemini' ? 'Gemini' : 'Claude'} API 호출)`"
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
      </div>
    </div>
  </Teleport>
</template>
