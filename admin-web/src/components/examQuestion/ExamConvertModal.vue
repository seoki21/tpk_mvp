<!--
  기출문항 변환(JSON) 팝업 컴포넌트
  - 기출문제 관리 화면에서 파일 아이콘 클릭 시 모달로 표시
  - 좌측: PDF 뷰어 (해당 파일 표시)
  - 우측: JSON 변환 버튼 클릭 시 Claude API SSE 스트리밍으로 JSON 결과 실시간 출력
  - 하단: 저장 버튼 (문제→tb_exam_question, 지시문→tb_exam_instruction)
-->
<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import { getInlineViewUrl } from '@/api/examFile';
import { convertPdfToJsonStream, bulkSave } from '@/api/examQuestion';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';

const props = defineProps({
  /** 팝업 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 시험키 PK */
  examKey: {
    type: Number,
    default: null
  },
  /** PDF 파일키 PK */
  pdfKey: {
    type: Number,
    default: null
  },
  /** 시험 정보 객체 (selectbox에서 선택된 시험) */
  examInfo: {
    type: Object,
    default: null
  },
  /** 파일 정보 객체 */
  fileInfo: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close', 'saved']);

/* ========== 상태 ========== */

/** JSON 변환 결과 텍스트 */
const jsonText = ref('');

/** 변환 로딩 상태 */
const converting = ref(false);

/** 스트리밍 상태: idle | connecting | streaming | done | error */
const streamStatus = ref('idle');

/** 토큰 사용량 정보 */
const tokenUsage = ref(null);

/** 저장 확인 다이얼로그 */
const showConfirm = ref(false);

/** JSON 결과 영역 ref (자동 스크롤용) */
const jsonContainer = ref(null);

/* ========== 계산된 속성 ========== */

/** PDF 인라인 뷰어 URL */
const pdfUrl = computed(() => {
  if (props.examKey && props.pdfKey) {
    return getInlineViewUrl(props.examKey, props.pdfKey);
  }
  return '';
});

/** 기출 제목 (예시 형태) */
const examTitle = computed(() => {
  if (!props.examInfo) return '';
  const parts = [];
  if (props.examInfo.exam_year) parts.push(props.examInfo.exam_year + '년');
  if (props.examInfo.round) parts.push('제' + props.examInfo.round + '회');
  if (props.examInfo.tpk_level_name) parts.push(props.examInfo.tpk_level_name);
  if (props.examInfo.section_name) parts.push(props.examInfo.section_name);
  return parts.join(' ');
});

/** 스트리밍 상태에 따른 안내 메시지 */
const statusMessage = computed(() => {
  switch (streamStatus.value) {
    case 'connecting':
      return 'Claude API 연결 중...';
    case 'streaming':
      return '변환 중...';
    case 'done':
      if (tokenUsage.value) {
        return `변환 완료 (입력: ${tokenUsage.value.input_tokens.toLocaleString()}토큰 / 출력: ${tokenUsage.value.output_tokens.toLocaleString()}토큰)`;
      }
      return '변환 완료';
    case 'error':
      return '변환 실패';
    default:
      return '';
  }
});

/* ========== 모달 열림/닫힘 시 초기화 ========== */
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      jsonText.value = '';
      streamStatus.value = 'idle';
      tokenUsage.value = null;
    }
  }
);

/* ========== 자동 스크롤 ========== */

/** JSON 텍스트가 추가될 때 스크롤을 하단으로 이동 */
function scrollToBottom() {
  nextTick(() => {
    if (jsonContainer.value) {
      jsonContainer.value.scrollTop = jsonContainer.value.scrollHeight;
    }
  });
}

/* ========== 액션 ========== */

/** JSON 변환 버튼 클릭 — Claude API SSE 스트리밍 호출 */
async function handleConvert() {
  if (!props.examKey || !props.pdfKey) return;

  converting.value = true;
  streamStatus.value = 'connecting';
  jsonText.value = '';
  tokenUsage.value = null;

  try {
    await convertPdfToJsonStream(props.examKey, props.pdfKey, (event) => {
      switch (event.type) {
        case 'start':
          /* 스트리밍 시작 — 모델 정보 수신 */
          streamStatus.value = 'streaming';
          break;
        case 'text_delta':
          /* JSON 텍스트 청크 실시간 누적 */
          jsonText.value += event.data.text;
          scrollToBottom();
          break;
        case 'done':
          /* 변환 완료 — 토큰 사용량 표시 */
          streamStatus.value = 'done';
          tokenUsage.value = event.data.token_usage;
          /* 응답이 max_tokens로 잘린 경우 경고 */
          if (event.data.stop_reason === 'max_tokens') {
            alert(
              'AI 응답이 최대 토큰 한도에 도달하여 JSON이 잘렸을 수 있습니다.\n' +
                '저장 전에 JSON이 완전한지 확인해 주세요.'
            );
          }
          break;
        case 'error':
          /* 에러 발생 */
          streamStatus.value = 'error';
          alert(event.data.detail || 'PDF 변환에 실패했습니다.');
          break;
      }
    });
  } catch {
    streamStatus.value = 'error';
    alert('PDF 변환 중 네트워크 오류가 발생했습니다.');
  } finally {
    converting.value = false;
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
  a.download = `exam_${props.examKey}_converted.json`;
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
 * Claude API가 가끔 ```json ... ``` 형태로 감싸서 반환하는 경우 대응.
 */
function cleanJsonText(text) {
  let cleaned = text.trim();
  // 마크다운 코드블록 제거 (```json ... ``` 또는 ``` ... ```)
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
    // JSON 파싱 (마크다운 코드블록 제거 후)
    let items;
    try {
      items = JSON.parse(cleanJsonText(jsonText.value));
    } catch {
      alert('JSON 형식이 올바르지 않습니다.');
      return;
    }

    // 배열이 아닌 경우 처리
    if (!Array.isArray(items)) {
      alert('JSON이 배열 형식이 아닙니다.');
      return;
    }

    // 문제(Q)와 지시문(I) 분리
    const questions = [];
    const instructions = [];
    let insCounter = 1;

    for (const item of items) {
      if (item.item_type === 'I') {
        // 지시문
        instructions.push({
          ins_no: insCounter++,
          ins_json: JSON.stringify(item)
        });
      } else if (item.item_type === 'Q') {
        // 문제
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
      // notes 등 기타 항목은 무시
    }

    // 일괄 저장
    await bulkSave(props.examKey, { questions, instructions });
    alert('저장되었습니다.');
    emit('saved');
  } catch (error) {
    alert(error.detail || '저장에 실패했습니다.');
  }
}

/** 오버레이 클릭 시 닫기 */
function onOverlayClick() {
  emit('close');
}

/** 모달 내부 클릭 전파 차단 */
function onModalClick(e) {
  e.stopPropagation();
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click="onOverlayClick"
    >
      <!-- 모달 박스 — 거의 전체 화면 크기 -->
      <div
        class="mx-4 flex h-[90vh] w-full max-w-7xl flex-col rounded-lg bg-white shadow-lg"
        @click="onModalClick"
      >
        <!-- 서브 타이틀 바 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 class="text-lg font-semibold text-gray-800">기출문항 변환(JSON)</h2>
          <button
            class="flex h-8 w-8 items-center justify-center rounded bg-gray-800 text-sm font-bold text-white hover:bg-gray-700"
            @click="emit('close')"
          >
            X
          </button>
        </div>

        <!-- 기출 제목 -->
        <div class="border-b border-gray-200 px-6 py-3">
          <p class="text-base font-bold text-gray-800">{{ examTitle }}</p>
        </div>

        <!-- 하위 타이틀 + 버튼 영역 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-2">
          <!-- 스트리밍 상태 메시지 -->
          <div class="flex items-center gap-2 text-sm text-gray-500">
            <!-- 로딩 스피너 (연결 중 / 스트리밍 중) -->
            <svg
              v-if="streamStatus === 'connecting' || streamStatus === 'streaming'"
              class="h-4 w-4 animate-spin text-blue-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            <span>{{ statusMessage }}</span>
          </div>
          <div class="flex gap-2">
            <button
              class="rounded border border-gray-400 bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300 disabled:opacity-50"
              :disabled="converting"
              @click="handleConvert"
            >
              {{ converting ? '변환 중...' : 'JSON 변환' }}
            </button>
            <button
              class="rounded border border-gray-400 bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
              :disabled="!jsonText"
              @click="handleCopy"
            >
              복사
            </button>
            <button
              class="rounded border border-gray-400 bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
              :disabled="!jsonText"
              @click="handleDownload"
            >
              다운로드
            </button>
          </div>
        </div>

        <!-- 본문: 좌측 PDF + 우측 JSON -->
        <div class="flex flex-1 overflow-hidden">
          <!-- 좌측: PDF 뷰어 -->
          <div class="w-1/2 border-r border-gray-200">
            <div v-if="pdfUrl">
              <iframe
                :src="pdfUrl"
                class="h-full w-full border-0"
                style="min-height: calc(90vh - 200px)"
              ></iframe>
            </div>
            <div v-else class="flex h-full items-center justify-center text-gray-400">
              PDF 파일 없음
            </div>
          </div>

          <!-- 우측: JSON 결과 -->
          <div class="flex w-1/2 flex-col">
            <div ref="jsonContainer" class="flex-1 overflow-auto bg-gray-900 p-4">
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
                    <circle
                      class="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      stroke-width="4"
                    />
                    <path
                      class="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  <p>Claude API 연결 중...</p>
                  <p class="mt-1 text-xs text-gray-500">PDF 파일을 분석하고 있습니다.</p>
                </div>
              </div>
              <div v-else class="flex h-full items-center justify-center text-gray-500">
                'JSON 변환' 버튼을 클릭하세요.
              </div>
            </div>
          </div>
        </div>

        <!-- 하단 저장 버튼 -->
        <div class="flex items-center justify-center border-t border-gray-200 px-6 py-4">
          <button
            class="rounded border border-gray-400 bg-gray-200 px-6 py-2 text-sm hover:bg-gray-300 disabled:opacity-50"
            :disabled="!jsonText || converting"
            @click="handleSave"
          >
            저장
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- 저장 확인 다이얼로그 -->
  <ConfirmDialog
    :visible="showConfirm"
    message="저장하시겠습니까?"
    @confirm="confirmSave"
    @cancel="showConfirm = false"
  />
</template>
