<!--
  기출문제 관리 상단 조회조건 공통 컴포넌트
  - 기출문제 selectbox, 영역 selectbox, 파일(PDF) selectbox, 변환/저장 버튼
  - 읽기(PastExamQuestionView)와 듣기(PastExamListeningView) 화면에서 공유한다.
-->
<script setup>
defineProps({
  /** store 인스턴스 */
  store: { type: Object, required: true },
  /** 영역 옵션 목록 [{ code, name }] */
  sectionOptions: { type: Array, default: () => [] },
  /** 기출문제 라벨 생성 함수 */
  getExamLabel: { type: Function, required: true },
});

const emit = defineEmits([
  'exam-change',
  'section-change',
  'file-change',
  'convert-click',
  'json-upload',
  'save-all',
  'retry-exam-options',
]);
</script>

<template>
  <div class="mb-4 flex items-center gap-4 rounded border border-gray-300 bg-gray-50 px-4 py-3">
    <!-- 기출문제 selectbox -->
    <div class="flex items-center gap-2">
      <label class="whitespace-nowrap text-sm font-medium text-gray-700">기출문제</label>
      <select
        :value="store.selectedExamKey || ''"
        class="min-w-[260px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        :disabled="store.examOptionsLoading"
        @change="emit('exam-change', $event)"
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
          @click="emit('retry-exam-options')"
        >
          재조회
        </button>
      </template>
    </div>

    <!-- 영역 selectbox -->
    <div class="flex items-center gap-2">
      <label class="whitespace-nowrap text-sm font-medium text-gray-700">영역</label>
      <select
        :value="store.selectedExam?.section || ''"
        class="min-w-[120px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        :disabled="!store.selectedExamKey"
        @change="emit('section-change', $event)"
      >
        <option value="">선택하세요</option>
        <option v-for="sec in sectionOptions" :key="sec.code" :value="sec.code">
          {{ sec.name }}
        </option>
      </select>
    </div>

    <!-- 파일(PDF) selectbox + 버튼들 -->
    <div class="flex items-center gap-2">
      <label class="whitespace-nowrap text-sm font-medium text-gray-700">파일(PDF)</label>
      <select
        :value="store.selectedPdfKey || ''"
        class="min-w-[200px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        :disabled="!store.selectedExamKey"
        @change="emit('file-change', $event)"
      >
        <option value="">선택하세요</option>
        <option v-for="file in store.fileOptions" :key="file.pdf_key" :value="file.pdf_key">
          {{ file.file_name }}
        </option>
      </select>

      <!-- 전체 변환(API) 화면 버튼 -->
      <button
        class="inline-flex items-center gap-1 rounded border border-blue-400 bg-blue-50 px-3 py-1.5 text-sm text-blue-700 hover:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="!store.selectedPdfKey"
        @click="emit('convert-click')"
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
        @change="emit('json-upload', $event)"
      />

      <!-- 전체 저장 버튼 -->
      <button
        class="rounded border border-gray-300 bg-gray-100 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="!store.selectedExamKey || store.mergedItems.length === 0"
        @click="emit('save-all')"
      >
        전체 저장
      </button>
    </div>
  </div>
</template>
