<!--
  기출시험 등록/수정 모달 컴포넌트
  - editData가 null이면 등록 모드, 객체이면 수정 모드
  - 시험유형이 '기출문제'(code=1)인 경우에만 PDF 업로드 활성화
  - 등록 모드: 파일을 pendingFiles에 보관 → 저장 시 시험정보 저장 후 파일 업로드
  - 수정 모드: 즉시 업로드 + 기존 파일 목록 표시
  - 드래그앤드롭 및 다중 파일 업로드 지원
-->
<script setup>
import { ref, watch, computed } from 'vue';
import FormModal from '@/components/common/FormModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import { useExamListStore } from '@/stores/examList';
import { getFiles, uploadFiles, deleteFile, getDownloadUrl } from '@/api/examFile';

const store = useExamListStore();

/* 기출문제 시험유형 code 값 */
const EXAM_TYPE_PAST = '1';

const props = defineProps({
  /** 모달 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 수정 대상 데이터 (null이면 등록 모드) */
  editData: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close', 'saved']);

/** 수정 모드 여부 판별 */
const isEditMode = computed(() => props.editData !== null);

/** 모달 타이틀 (등록/수정에 따라 변경) */
const modalTitle = computed(() => (isEditMode.value ? '시험(기출) 수정' : '시험(기출) 등록'));

/** 시험유형이 '기출문제'인지 여부 — PDF 업로드 활성화 조건 */
const isPastExamType = computed(() => String(form.value.exam_type) === EXAM_TYPE_PAST);

/* ========== 폼 데이터 ========== */
const form = ref({
  exam_key: '',
  exam_year: '',
  exam_type: '',
  tpk_level: '',
  round: '',
  section: '',
  del_yn: 'N'
});

/* ========== PDF 파일 관련 상태 ========== */
/** 서버에 업로드된 PDF 파일 목록 (수정 모드) */
const fileList = ref([]);
/** 등록 모드에서 대기 중인 PDF 파일 (저장 시 업로드) */
const pendingFiles = ref([]);
/** PDF 파일 업로드 로딩 상태 */
const fileLoading = ref(false);
/** PDF 파일 선택 input ref */
const fileInput = ref(null);
/** PDF 드래그 중 여부 (시각적 피드백용) */
const isDragging = ref(false);

/* ========== JSON 파일 관련 상태 ========== */
/** 서버에 업로드된 JSON 파일 목록 (수정 모드) */
const jsonFileList = ref([]);
/** 등록 모드에서 대기 중인 JSON 파일 (저장 시 업로드) */
const pendingJsonFiles = ref([]);
/** JSON 파일 업로드 로딩 상태 */
const jsonFileLoading = ref(false);
/** JSON 파일 선택 input ref */
const jsonFileInput = ref(null);
/** JSON 드래그 중 여부 */
const isJsonDragging = ref(false);

/** 모달이 열릴 때 폼 데이터를 초기화 */
watch(
  () => props.visible,
  async (newVal) => {
    if (newVal) {
      pendingFiles.value = [];
      pendingJsonFiles.value = [];
      isDragging.value = false;
      isJsonDragging.value = false;

      if (props.editData) {
        /* 수정 모드: 기존 데이터를 폼에 채움 */
        form.value = {
          exam_key: props.editData.exam_key || '',
          exam_year: props.editData.exam_year || '',
          exam_type: props.editData.exam_type || '',
          tpk_level: props.editData.tpk_level || '',
          round: props.editData.round ?? '',
          section: props.editData.section || '',
          del_yn: props.editData.del_yn || 'N'
        };
        /* 수정 모드에서 파일 목록 로드 (PDF + JSON) */
        await loadFiles();
      } else {
        /* 등록 모드: 빈 폼으로 초기화 */
        form.value = {
          exam_key: '',
          exam_year: '',
          exam_type: '',
          tpk_level: '',
          round: '',
          section: '',
          del_yn: 'N'
        };
        fileList.value = [];
        jsonFileList.value = [];
      }

      /* 코드 옵션이 비어 있으면 가져옴 */
      if (store.examTypeOptions.length === 0) {
        store.fetchCodeOptions();
      }
    }
  }
);

/* ========== 파일 함수 ========== */

/** 서버에서 파일 목록을 조회하고 file_type별로 분리한다 */
async function loadFiles() {
  if (!form.value.exam_key) return;
  try {
    const res = await getFiles(form.value.exam_key);
    const allFiles = res.data || [];
    /* file_type별 분리 (NULL이면 pdf로 취급) */
    fileList.value = allFiles.filter((f) => !f.file_type || f.file_type === 'pdf');
    jsonFileList.value = allFiles.filter((f) => f.file_type === 'json');
  } catch (error) {
    console.error('[FILE] 목록 조회 실패:', error);
    fileList.value = [];
    jsonFileList.value = [];
  }
}

/** PDF 파일 유효성 검증 — 실패 시 false 반환 */
function validatePdfFiles(files) {
  const invalidFiles = files.filter((f) => !f.name.toLowerCase().endsWith('.pdf'));
  if (invalidFiles.length > 0) {
    alert('기출문제 파일 형식이 PDF가 아닌 것 같으니 확인 바랍니다.');
    return false;
  }
  return true;
}

/** JSON 파일 유효성 검증 — 실패 시 false 반환 */
function validateJsonFiles(files) {
  const invalidFiles = files.filter((f) => !f.name.toLowerCase().endsWith('.json'));
  if (invalidFiles.length > 0) {
    alert('JSON 파일 형식이 아닌 것 같으니 확인 바랍니다.');
    return false;
  }
  return true;
}

/** PDF 파일 선택 버튼 클릭 */
function triggerFileInput() {
  fileInput.value?.click();
}

/** JSON 파일 선택 버튼 클릭 */
function triggerJsonFileInput() {
  jsonFileInput.value?.click();
}

/** JSON 파일 선택 후 처리 */
async function handleJsonFileChange(event) {
  const files = Array.from(event.target.files || []);
  if (files.length === 0) return;

  if (!validateJsonFiles(files)) {
    event.target.value = '';
    return;
  }

  if (isEditMode.value) {
    await doUpload(files, 'json');
  } else {
    pendingJsonFiles.value = [...pendingJsonFiles.value, ...files];
  }
  event.target.value = '';
}

/** JSON 드래그앤드롭 핸들러 */
function onJsonDragOver() {
  if (isPastExamType.value) isJsonDragging.value = true;
}
function onJsonDragLeave() {
  isJsonDragging.value = false;
}
async function onJsonDrop(e) {
  isJsonDragging.value = false;
  if (!isPastExamType.value) return;

  const files = Array.from(e.dataTransfer?.files || []);
  if (files.length === 0) return;
  if (!validateJsonFiles(files)) return;

  if (isEditMode.value) {
    await doUpload(files, 'json');
  } else {
    pendingJsonFiles.value = [...pendingJsonFiles.value, ...files];
  }
}

/** 대기 JSON 파일 삭제 (등록 모드) */
function removePendingJsonFile(index) {
  pendingJsonFiles.value.splice(index, 1);
}

/** 파일 선택 후 처리 (input change) */
async function handleFileChange(event) {
  const files = Array.from(event.target.files || []);
  if (files.length === 0) return;

  if (!validatePdfFiles(files)) {
    event.target.value = '';
    return;
  }

  if (isEditMode.value) {
    /* 수정 모드: 즉시 업로드 */
    await doUpload(files);
  } else {
    /* 등록 모드: pendingFiles에 추가 */
    pendingFiles.value = [...pendingFiles.value, ...files];
  }
  /* input 초기화 (같은 파일 재선택 가능하도록) */
  event.target.value = '';
}

/** 드래그앤드롭 이벤트 핸들러 — Vue .prevent 수식어로 preventDefault 처리 */
function onDragOver() {
  if (isPastExamType.value) {
    isDragging.value = true;
  }
}
function onDragLeave() {
  isDragging.value = false;
}
async function onDrop(e) {
  isDragging.value = false;

  if (!isPastExamType.value) return;

  const files = Array.from(e.dataTransfer?.files || []);
  if (files.length === 0) return;

  if (!validatePdfFiles(files)) return;

  if (isEditMode.value) {
    await doUpload(files);
  } else {
    pendingFiles.value = [...pendingFiles.value, ...files];
  }
}

/** 서버에 파일 업로드 실행 (수정 모드에서 사용) */
async function doUpload(files, fileType = 'pdf') {
  const loadingRef = fileType === 'json' ? jsonFileLoading : fileLoading;
  loadingRef.value = true;
  try {
    await uploadFiles(form.value.exam_key, files, fileType);
    await loadFiles();
  } catch (error) {
    alert(error.detail || '오류가 발생했습니다');
  } finally {
    loadingRef.value = false;
  }
}

/** 서버 파일 삭제 (수정 모드) */
async function handleFileDelete(file) {
  if (!confirm('이 파일을 삭제하시겠습니까?')) return;
  try {
    await deleteFile(form.value.exam_key, file.pdf_key);
    await loadFiles();
  } catch (error) {
    alert(error.detail || '오류가 발생했습니다');
  }
}

/** 대기 파일 삭제 (등록 모드) */
function removePendingFile(index) {
  pendingFiles.value.splice(index, 1);
}

/** 파일 다운로드 URL 반환 */
function getFileDownloadUrl(file) {
  return getDownloadUrl(form.value.exam_key, file.pdf_key);
}

/** 파일 크기를 읽기 쉬운 형식으로 변환 */
function formatFileSize(bytes) {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/* ========== 삭제 확인 다이얼로그 ========== */
const showConfirm = ref(false);

/** 저장 핸들러 */
async function handleSave() {
  try {
    let examKey;

    if (isEditMode.value) {
      await store.update(form.value.exam_key, {
        exam_year: form.value.exam_year,
        exam_type: form.value.exam_type,
        tpk_level: form.value.tpk_level,
        round: form.value.round,
        section: form.value.section,
        del_yn: form.value.del_yn
      });
      examKey = form.value.exam_key;
    } else {
      /* 등록: 시험 정보 저장 후 exam_key 획득 */
      const result = await store.create({
        exam_year: form.value.exam_year,
        exam_type: form.value.exam_type,
        tpk_level: form.value.tpk_level,
        round: form.value.round,
        section: form.value.section
      });
      examKey = result?.data?.exam_key;
    }

    /* 등록 모드에서 pendingFiles(PDF)가 있으면 업로드 */
    if (pendingFiles.value.length > 0 && examKey) {
      fileLoading.value = true;
      try {
        await uploadFiles(examKey, pendingFiles.value, 'pdf');
      } catch (uploadError) {
        alert(uploadError.detail || 'PDF 파일 업로드 중 오류가 발생했습니다');
      } finally {
        fileLoading.value = false;
      }
    }

    /* 등록 모드에서 pendingJsonFiles(JSON)가 있으면 업로드 */
    if (pendingJsonFiles.value.length > 0 && examKey) {
      jsonFileLoading.value = true;
      try {
        await uploadFiles(examKey, pendingJsonFiles.value, 'json');
      } catch (uploadError) {
        alert(uploadError.detail || 'JSON 파일 업로드 중 오류가 발생했습니다');
      } finally {
        jsonFileLoading.value = false;
      }
    }

    alert('저장되었습니다');
    emit('saved');
  } catch (error) {
    alert(error.detail || '오류가 발생했습니다');
  }
}

/** 삭제 버튼 클릭 → 확인 다이얼로그 표시 */
function handleDelete() {
  showConfirm.value = true;
}

/** 삭제 확인 후 실행 */
async function confirmDelete() {
  showConfirm.value = false;
  try {
    await store.remove(form.value.exam_key);
    alert('삭제되었습니다');
    emit('saved');
  } catch (error) {
    alert(error.detail || '오류가 발생했습니다');
  }
}

/** 삭제 취소 */
function cancelDelete() {
  showConfirm.value = false;
}
</script>

<template>
  <FormModal
    :visible="visible"
    :title="modalTitle"
    :show-delete="isEditMode"
    max-width="max-w-2xl"
    @close="emit('close')"
    @save="handleSave"
    @delete="handleDelete"
  >
    <div class="space-y-4">
      <!-- 시험키 (수정 모드에서만 읽기 전용 표시) -->
      <div v-if="isEditMode" class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">시험키</label>
        <input
          :value="form.exam_key"
          type="text"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <!-- 년도 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">년도</label>
        <input
          v-model="form.exam_year"
          type="text"
          maxlength="4"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <!-- 시험유형 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">시험유형</label>
        <select
          v-model="form.exam_type"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.examTypeOptions" :key="opt.code" :value="opt.code">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 토픽레벨 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">토픽레벨</label>
        <select
          v-model="form.tpk_level"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.tpkLevelOptions" :key="opt.code" :value="opt.code">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 회차 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">회차</label>
        <input
          v-model.number="form.round"
          type="number"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <!-- 영역 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">영역</label>
        <select
          v-model="form.section"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.sectionOptions" :key="opt.code" :value="opt.code">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 삭제여부 (수정 모드에서만 표시) -->
      <div v-if="isEditMode" class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">삭제여부</label>
        <select
          v-model="form.del_yn"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="N">N</option>
          <option value="Y">Y</option>
        </select>
      </div>

      <!-- ========== 문제(PDF) 파일 영역 ========== -->
      <div class="border-t border-gray-200 pt-4">
        <div class="mb-3 flex items-center justify-between">
          <label class="text-sm font-medium text-gray-700">문제(PDF)</label>
          <button
            type="button"
            class="rounded px-3 py-1.5 text-xs text-white"
            :class="
              isPastExamType ? 'bg-blue-500 hover:bg-blue-600' : 'cursor-not-allowed bg-gray-300'
            "
            :disabled="!isPastExamType || fileLoading"
            @click="triggerFileInput"
          >
            {{ fileLoading ? '업로드 중...' : '파일 선택' }}
          </button>
          <!-- 숨겨진 파일 input -->
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf"
            class="hidden"
            @change="handleFileChange"
          />
        </div>

        <!-- 드래그앤드롭 영역 -->
        <div
          class="flex min-h-[100px] items-center justify-center rounded-lg border-2 border-dashed p-4 text-center transition-colors"
          :class="
            !isPastExamType
              ? 'cursor-not-allowed border-gray-200 bg-gray-50 text-gray-300'
              : isDragging
                ? 'border-blue-400 bg-blue-50 text-blue-500'
                : 'border-gray-300 bg-white text-gray-400'
          "
          @dragenter.prevent
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
        >
          <!-- 업로드된 파일 목록 (수정 모드) -->
          <div v-if="isEditMode && fileList.length > 0" class="w-full space-y-2 text-left">
            <div
              v-for="file in fileList"
              :key="file.pdf_key"
              class="flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-3 py-2"
            >
              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="text-xs font-semibold text-red-500">PDF</span>
                <a
                  :href="getFileDownloadUrl(file)"
                  class="truncate text-sm text-blue-600 hover:underline"
                  target="_blank"
                >
                  {{ file.file_name }}
                </a>
                <span class="shrink-0 text-xs text-gray-400">
                  {{ formatFileSize(file.file_size) }}
                </span>
              </div>
              <button
                type="button"
                class="ml-2 shrink-0 text-sm text-red-500 hover:text-red-700"
                @click="handleFileDelete(file)"
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
                <span class="text-xs font-semibold text-red-500">PDF</span>
                <span class="truncate text-sm text-gray-700">{{ file.name }}</span>
                <span class="shrink-0 text-xs text-gray-400">
                  {{ formatFileSize(file.size) }}
                </span>
              </div>
              <button
                type="button"
                class="ml-2 shrink-0 text-sm text-red-500 hover:text-red-700"
                @click="removePendingFile(idx)"
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
            <p v-if="!isPastExamType" class="text-sm">
              시험유형을 '기출문제'로 선택하면 PDF 업로드가 활성화됩니다.
            </p>
            <p v-else class="text-sm">
              PDF 파일을 이곳에 드래그하거나, 파일 선택 버튼을 클릭하세요.
            </p>
          </div>
        </div>
      </div>

      <!-- ========== 문제(JSON) 파일 영역 ========== -->
      <div class="border-t border-gray-200 pt-4">
        <div class="mb-3 flex items-center justify-between">
          <label class="text-sm font-medium text-gray-700">문제(JSON)</label>
          <button
            type="button"
            class="rounded px-3 py-1.5 text-xs text-white"
            :class="
              isPastExamType ? 'bg-teal-500 hover:bg-teal-600' : 'cursor-not-allowed bg-gray-300'
            "
            :disabled="!isPastExamType || jsonFileLoading"
            @click="triggerJsonFileInput"
          >
            {{ jsonFileLoading ? '업로드 중...' : '파일 선택' }}
          </button>
          <input
            ref="jsonFileInput"
            type="file"
            multiple
            accept=".json"
            class="hidden"
            @change="handleJsonFileChange"
          />
        </div>

        <!-- 드래그앤드롭 영역 -->
        <div
          class="flex min-h-[100px] items-center justify-center rounded-lg border-2 border-dashed p-4 text-center transition-colors"
          :class="
            !isPastExamType
              ? 'cursor-not-allowed border-gray-200 bg-gray-50 text-gray-300'
              : isJsonDragging
                ? 'border-teal-400 bg-teal-50 text-teal-500'
                : 'border-gray-300 bg-white text-gray-400'
          "
          @dragenter.prevent
          @dragover.prevent="onJsonDragOver"
          @dragleave.prevent="onJsonDragLeave"
          @drop.prevent="onJsonDrop"
        >
          <!-- 업로드된 JSON 파일 목록 (수정 모드) -->
          <div v-if="isEditMode && jsonFileList.length > 0" class="w-full space-y-2 text-left">
            <div
              v-for="file in jsonFileList"
              :key="file.pdf_key"
              class="flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-3 py-2"
            >
              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="text-xs font-semibold text-teal-600">JSON</span>
                <a
                  :href="getFileDownloadUrl(file)"
                  class="truncate text-sm text-blue-600 hover:underline"
                  target="_blank"
                >
                  {{ file.file_name }}
                </a>
                <span class="shrink-0 text-xs text-gray-400">
                  {{ formatFileSize(file.file_size) }}
                </span>
              </div>
              <button
                type="button"
                class="ml-2 shrink-0 text-sm text-red-500 hover:text-red-700"
                @click="handleFileDelete(file)"
              >
                삭제
              </button>
            </div>
          </div>

          <!-- 대기 JSON 파일 목록 (등록 모드) -->
          <div
            v-if="!isEditMode && pendingJsonFiles.length > 0"
            class="w-full space-y-2 text-left"
          >
            <div
              v-for="(file, idx) in pendingJsonFiles"
              :key="idx"
              class="flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-3 py-2"
            >
              <div class="flex min-w-0 flex-1 items-center gap-2">
                <span class="text-xs font-semibold text-teal-600">JSON</span>
                <span class="truncate text-sm text-gray-700">{{ file.name }}</span>
                <span class="shrink-0 text-xs text-gray-400">
                  {{ formatFileSize(file.size) }}
                </span>
              </div>
              <button
                type="button"
                class="ml-2 shrink-0 text-sm text-red-500 hover:text-red-700"
                @click="removePendingJsonFile(idx)"
              >
                제거
              </button>
            </div>
          </div>

          <!-- 안내 문구 (파일이 없을 때) -->
          <div
            v-if="
              (isEditMode && jsonFileList.length === 0) ||
              (!isEditMode && pendingJsonFiles.length === 0)
            "
            class="py-4"
          >
            <p v-if="!isPastExamType" class="text-sm">
              시험유형을 '기출문제'로 선택하면 JSON 업로드가 활성화됩니다.
            </p>
            <p v-else class="text-sm">
              JSON 파일을 이곳에 드래그하거나, 파일 선택 버튼을 클릭하세요.
            </p>
          </div>
        </div>
      </div>
    </div>
  </FormModal>

  <!-- 삭제 확인 다이얼로그 -->
  <ConfirmDialog
    :visible="showConfirm"
    message="삭제하시겠습니까?"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
