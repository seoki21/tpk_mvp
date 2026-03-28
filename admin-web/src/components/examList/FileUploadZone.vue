<!--
  파일 업로드 영역 공통 컴포넌트
  - 드래그앤드롭 + 파일 선택 버튼을 지원하는 파일 업로드 영역
  - PDF/JSON 등 파일 타입에 맞게 색상과 라벨을 변경할 수 있다.
  - 수정 모드: 서버 파일 목록 + 삭제, 등록 모드: 대기 파일 목록 + 제거
-->
<script setup>
import { ref } from 'vue';

const props = defineProps({
  /** 파일 타입 라벨 (예: 'PDF', 'JSON') */
  fileTypeLabel: {
    type: String,
    default: 'PDF'
  },
  /** 파일 accept 속성 (예: '.pdf', '.json') */
  accept: {
    type: String,
    default: '.pdf'
  },
  /** 수정 모드 여부 */
  isEditMode: {
    type: Boolean,
    default: false
  },
  /** 활성화 여부 (시험유형 조건) */
  enabled: {
    type: Boolean,
    default: false
  },
  /** 서버 파일 목록 (수정 모드) */
  fileList: {
    type: Array,
    default: () => []
  },
  /** 대기 파일 목록 (등록 모드) */
  pendingFiles: {
    type: Array,
    default: () => []
  },
  /** 업로드 로딩 상태 */
  loading: {
    type: Boolean,
    default: false
  },
  /** 드래그 중 테두리 색상 클래스 */
  accentColor: {
    type: String,
    default: 'blue'
  }
});

const emit = defineEmits([
  'file-select',
  'file-delete',
  'pending-remove'
]);

/** 파일 선택 input ref */
const fileInput = ref(null);

/** 드래그 중 여부 */
const isDragging = ref(false);

/** 파일 선택 버튼 클릭 */
function triggerFileInput() {
  fileInput.value?.click();
}

/** 파일 선택 후 처리 */
function handleFileChange(event) {
  const files = Array.from(event.target.files || []);
  if (files.length === 0) return;
  emit('file-select', files);
  event.target.value = '';
}

/** 드래그앤드롭 핸들러 */
function onDragOver() {
  if (props.enabled) isDragging.value = true;
}
function onDragLeave() {
  isDragging.value = false;
}
function onDrop(e) {
  isDragging.value = false;
  if (!props.enabled) return;
  const files = Array.from(e.dataTransfer?.files || []);
  if (files.length === 0) return;
  emit('file-select', files);
}

/**
 * 파일 크기를 읽기 쉬운 형식으로 변환한다.
 * @param {number} bytes - 바이트 크기
 */
function formatFileSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** 라벨 색상 클래스 */
const labelColorClass = {
  blue: 'text-red-500',
  teal: 'text-teal-600'
};

/** 버튼 색상 클래스 */
const btnColorClass = {
  blue: 'bg-blue-500 hover:bg-blue-600',
  teal: 'bg-teal-500 hover:bg-teal-600'
};

/** 드래그 활성 색상 클래스 */
const dragColorClass = {
  blue: 'border-blue-400 bg-blue-50 text-blue-500',
  teal: 'border-teal-400 bg-teal-50 text-teal-500'
};
</script>

<template>
  <div class="border-t border-gray-200 pt-4">
    <div class="mb-3 flex items-center justify-between">
      <label class="text-sm font-medium text-gray-700">문제({{ fileTypeLabel }})</label>
      <button
        type="button"
        class="rounded px-3 py-1.5 text-xs text-white"
        :class="enabled ? btnColorClass[accentColor] : 'cursor-not-allowed bg-gray-300'"
        :disabled="!enabled || loading"
        @click="triggerFileInput"
      >
        {{ loading ? '업로드 중...' : '파일 선택' }}
      </button>
      <input
        ref="fileInput"
        type="file"
        multiple
        :accept="accept"
        class="hidden"
        @change="handleFileChange"
      />
    </div>

    <!-- 드래그앤드롭 영역 -->
    <div
      class="flex min-h-[100px] items-center justify-center rounded-lg border-2 border-dashed p-4 text-center transition-colors"
      :class="
        !enabled
          ? 'cursor-not-allowed border-gray-200 bg-gray-50 text-gray-300'
          : isDragging
            ? dragColorClass[accentColor]
            : 'border-gray-300 bg-white text-gray-400'
      "
      @dragenter.prevent
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onDrop"
    >
      <!-- 서버 파일 목록 (수정 모드) -->
      <div v-if="isEditMode && fileList.length > 0" class="w-full space-y-2 text-left">
        <div
          v-for="file in fileList"
          :key="file.pdf_key"
          class="flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-3 py-2"
        >
          <div class="flex min-w-0 flex-1 items-center gap-2">
            <span class="text-xs font-semibold" :class="labelColorClass[accentColor]">{{ fileTypeLabel }}</span>
            <slot name="file-link" :file="file">
              <span class="truncate text-sm text-gray-700">{{ file.file_name }}</span>
            </slot>
            <span class="shrink-0 text-xs text-gray-400">
              {{ formatFileSize(file.file_size) }}
            </span>
          </div>
          <button
            type="button"
            class="ml-2 shrink-0 text-sm text-red-500 hover:text-red-700"
            @click="emit('file-delete', file)"
          >
            삭제
          </button>
        </div>
      </div>

      <!-- 대기 파일 목록 (등록 모드) -->
      <div v-if="!isEditMode && pendingFiles.length > 0" class="w-full space-y-2 text-left">
        <div
          v-for="(file, idx) in pendingFiles"
          :key="idx"
          class="flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-3 py-2"
        >
          <div class="flex min-w-0 flex-1 items-center gap-2">
            <span class="text-xs font-semibold" :class="labelColorClass[accentColor]">{{ fileTypeLabel }}</span>
            <span class="truncate text-sm text-gray-700">{{ file.name }}</span>
            <span class="shrink-0 text-xs text-gray-400">
              {{ formatFileSize(file.size) }}
            </span>
          </div>
          <button
            type="button"
            class="ml-2 shrink-0 text-sm text-red-500 hover:text-red-700"
            @click="emit('pending-remove', idx)"
          >
            제거
          </button>
        </div>
      </div>

      <!-- 안내 문구 (파일이 없을 때) -->
      <div
        v-if="
          (isEditMode && fileList.length === 0) || (!isEditMode && pendingFiles.length === 0)
        "
        class="py-4"
      >
        <p v-if="!enabled" class="text-sm">
          시험유형을 '기출문제'로 선택하면 {{ fileTypeLabel }} 업로드가 활성화됩니다.
        </p>
        <p v-else class="text-sm">
          {{ fileTypeLabel }} 파일을 이곳에 드래그하거나, 파일 선택 버튼을 클릭하세요.
        </p>
      </div>
    </div>
  </div>
</template>
