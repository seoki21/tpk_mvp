<!--
  기출문항 관리 상단 조회조건 공통 컴포넌트
  - 통합 selectbox (시험 + 영역 + 파일) + API 호출 버튼 + 전체 저장 버튼
  - 읽기(PastExamQuestionView)와 듣기(PastExamListeningView) 화면에서 공유한다.
-->
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { getInlineViewUrl } from '@/api/examFile';

const props = defineProps({
  /** store 인스턴스 */
  store: { type: Object, required: true },
});

const emit = defineEmits([
  'combined-change',
  'convert-click',
  'save-all',
  'retry-exam-options',
  'toggle-json-filter',
]);

/* ========== 파일선택 드롭다운 ========== */
const showFileMenu = ref(false);

/** 문항 JSON 파일 선택용 hidden input ref */
const questionFileInput = ref(null);
/** 피드백 JSON 파일 선택용 hidden input ref */
const feedbackFileInput = ref(null);

/**
 * 서브메뉴 클릭 시 해당 file input 트리거
 * @param {'question'|'feedback'} type - 파일 유형
 */
function handleFileMenuClick(type) {
  showFileMenu.value = false;
  if (type === 'question') {
    questionFileInput.value?.click();
  } else {
    feedbackFileInput.value?.click();
  }
}

/**
 * 파일 선택 완료 후 처리 (미구현 상태 알림)
 * @param {Event} event - change 이벤트
 */
function handleFileSelected(event) {
  const file = event.target.files?.[0];
  if (file) {
    alert('아직 미구현 상태입니다');
  }
  // 같은 파일 재선택 가능하도록 value 초기화
  event.target.value = '';
}

/** 외부 클릭 시 파일선택 드롭다운 닫기 */
function handleFileMenuOutsideClick() {
  showFileMenu.value = false;
}

onMounted(() => document.addEventListener('click', handleFileMenuOutsideClick));
onUnmounted(() => document.removeEventListener('click', handleFileMenuOutsideClick));

/**
 * 통합 selectbox에서 선택된 값(examKey_pdfKey)을 파싱하여 emit
 */
function handleCombinedChange(event) {
  const val = event.target.value;
  if (!val) {
    emit('combined-change', null, null);
    return;
  }
  const [examKey, pdfKey] = val.split('_').map(Number);
  emit('combined-change', examKey, pdfKey);
}

/* ========== PDF 뷰어 팝업 ========== */
const showPdfViewer = ref(false);

/** 선택된 PDF의 인라인 뷰어 URL */
const pdfViewerUrl = computed(() => {
  if (props.store.selectedExamKey && props.store.selectedPdfKey) {
    return getInlineViewUrl(props.store.selectedExamKey, props.store.selectedPdfKey);
  }
  return '';
});

/** 선택된 파일명 */
const selectedFileName = computed(() => props.store.selectedFile?.file_name || '');
</script>

<template>
  <div class="mb-4 flex items-center gap-4 rounded border border-gray-300 bg-gray-50 px-4 py-3">
    <!-- 통합 selectbox + JSON 미변환 필터 체크박스 -->
    <div class="flex items-center gap-2">
      <label class="whitespace-nowrap text-sm font-medium text-gray-700">기출문제 파일</label>
      <select
        :value="store.selectedExamKey && store.selectedPdfKey ? store.selectedExamKey + '_' + store.selectedPdfKey : ''"
        class="min-w-[420px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        :disabled="store.examOptionsLoading"
        @change="handleCombinedChange"
      >
        <option value="">{{ store.examOptionsLoading ? '조회 중...' : '선택하세요' }}</option>
        <option
          v-for="opt in store.filteredCombinedOptions"
          :key="opt.examKey + '_' + opt.pdfKey"
          :value="opt.examKey + '_' + opt.pdfKey"
        >
          {{ opt.label }}
        </option>
      </select>
      <!-- PDF 뷰어 아이콘 버튼 -->
      <button
        class="flex h-7 w-7 items-center justify-center rounded text-blue-400 transition-colors hover:bg-blue-50 hover:text-blue-600 disabled:cursor-not-allowed disabled:text-gray-300 disabled:hover:bg-transparent"
        :disabled="!store.selectedPdfKey"
        title="PDF 파일 보기"
        @click="showPdfViewer = true"
      >
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          <path d="M14 2v6h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          <text x="12" y="17" text-anchor="middle" fill="currentColor" font-size="6" font-weight="bold" font-family="Arial">PDF</text>
        </svg>
      </button>
      <label class="flex cursor-pointer items-center gap-1 whitespace-nowrap text-sm text-gray-600">
        <input
          :checked="store.jsonFilterOnly"
          type="checkbox"
          class="h-3.5 w-3.5 rounded border-gray-300 text-blue-500 focus:ring-1 focus:ring-blue-500 focus:ring-offset-0"
          @change="emit('toggle-json-filter', $event.target.checked)"
        />
        JSON 미변환 파일만
      </label>
      <!-- 에러 발생 시 메시지 + 재조회 버튼 -->
      <template v-if="store.examOptionsError && store.examOptions.length === 0">
        <span class="text-xs text-red-500">{{ store.examOptionsError }}</span>
        <button
          class="rounded border border-gray-300 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50"
          @click="emit('retry-exam-options')"
        >
          재조회
        </button>
      </template>
    </div>

    <!-- API 팝업 버튼 -->
    <button
      class="btn btn-sm btn-primary gap-1"
      :disabled="!store.selectedPdfKey"
      @click="emit('convert-click')"
    >
      API 팝업
      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
      </svg>
    </button>

    <!-- 파일선택 드롭다운 버튼 -->
    <div class="relative">
      <button
        class="inline-flex items-center gap-1 rounded-md border border-blue-300 bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-600 transition-colors hover:border-blue-400 hover:bg-blue-100 disabled:cursor-not-allowed disabled:border-gray-200 disabled:bg-gray-50 disabled:text-gray-400"
        :disabled="!store.selectedPdfKey"
        @click.stop="showFileMenu = !showFileMenu"
      >
        JSON 파일 선택
        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      <!-- 서브메뉴 -->
      <div
        v-if="showFileMenu"
        class="absolute right-0 z-10 mt-1 w-44 rounded-md border border-gray-200 bg-white py-1 shadow-lg"
      >
        <button
          class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 hover:bg-blue-50"
          @click="handleFileMenuClick('question')"
        >
          문항 JSON 파일
        </button>
        <button
          class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700 hover:bg-blue-50"
          @click="handleFileMenuClick('feedback')"
        >
          피드백 JSON 파일
        </button>
      </div>
    </div>
    <!-- 숨겨진 file input (문항 / 피드백) -->
    <input
      ref="questionFileInput"
      type="file"
      accept=".json"
      class="hidden"
      @change="handleFileSelected"
    />
    <input
      ref="feedbackFileInput"
      type="file"
      accept=".json"
      class="hidden"
      @change="handleFileSelected"
    />

    <!-- 전체 저장 버튼 (우측 끝 정렬) -->
    <button
      class="btn btn-sm btn-secondary ml-auto"
      :disabled="!store.selectedExamKey || store.mergedItems.length === 0"
      @click="emit('save-all')"
    >
      전체 저장
    </button>
  </div>

  <!-- PDF 뷰어 팝업 -->
  <Teleport to="body">
    <div
      v-if="showPdfViewer"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click="showPdfViewer = false"
    >
      <div class="mx-4 flex h-[85vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-lg" @click.stop>
        <!-- 타이틀 바 -->
        <div class="flex shrink-0 items-center justify-between border-b border-gray-200 px-6 py-3">
          <h2 class="text-base font-semibold text-gray-800">{{ selectedFileName }}</h2>
          <button
            class="flex h-7 w-7 items-center justify-center rounded bg-gray-800 text-sm font-bold text-white hover:bg-gray-700"
            @click="showPdfViewer = false"
          >
            X
          </button>
        </div>
        <!-- PDF iframe -->
        <div class="min-h-0 flex-1">
          <iframe v-if="pdfViewerUrl" :src="pdfViewerUrl" class="h-full w-full border-0"></iframe>
          <div v-else class="flex h-full items-center justify-center text-gray-400">PDF 파일 없음</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
