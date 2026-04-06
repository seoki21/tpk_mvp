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
import FileUploadZone from '@/components/examList/FileUploadZone.vue';
import { useExamListStore } from '@/stores/examList';
import { getFiles, uploadFiles, deleteFile, getDownloadUrl } from '@/api/examFile';
import { useToast } from '@/composables/useToast';

const store = useExamListStore();
const toast = useToast();

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
});

/* ========== PDF 파일 관련 상태 ========== */
/** 서버에 업로드된 PDF 파일 목록 (수정 모드) */
const fileList = ref([]);
/** 등록 모드에서 대기 중인 PDF 파일 (저장 시 업로드) */
const pendingFiles = ref([]);
/** PDF 파일 업로드 로딩 상태 */
const fileLoading = ref(false);

/* ========== JSON 파일 관련 상태 ========== */
/** 서버에 업로드된 JSON 파일 목록 (수정 모드) */
const jsonFileList = ref([]);
/** 등록 모드에서 대기 중인 JSON 파일 (저장 시 업로드) */
const pendingJsonFiles = ref([]);
/** JSON 파일 업로드 로딩 상태 */
const jsonFileLoading = ref(false);

/* ========== MP3 파일 관련 상태 ========== */
/** 서버에 업로드된 MP3 파일 목록 (수정 모드) */
const mp3FileList = ref([]);
/** 등록 모드에서 대기 중인 MP3 파일 (저장 시 업로드) */
const pendingMp3Files = ref([]);
/** MP3 파일 업로드 로딩 상태 */
const mp3FileLoading = ref(false);

/** 모달이 열릴 때 폼 데이터를 초기화 */
watch(
  () => props.visible,
  async (newVal) => {
    if (newVal) {
      pendingFiles.value = [];
      pendingJsonFiles.value = [];
      pendingMp3Files.value = [];

      if (props.editData) {
        /* 수정 모드: 기존 데이터를 폼에 채움 */
        form.value = {
          exam_key: props.editData.exam_key || '',
          exam_year: props.editData.exam_year || '',
          exam_type: props.editData.exam_type || '',
          tpk_level: props.editData.tpk_level || '',
          round: props.editData.round ?? '',
          section: props.editData.section || ''
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
          section: ''
        };
        fileList.value = [];
        jsonFileList.value = [];
        mp3FileList.value = [];
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
    mp3FileList.value = allFiles.filter((f) => f.file_type === 'mp3');
  } catch (error) {
    console.error('[FILE] 목록 조회 실패:', error);
    fileList.value = [];
    jsonFileList.value = [];
    mp3FileList.value = [];
  }
}

/** PDF 파일 유효성 검증 — 실패 시 false 반환 */
function validatePdfFiles(files) {
  const invalidFiles = files.filter((f) => !f.name.toLowerCase().endsWith('.pdf'));
  if (invalidFiles.length > 0) {
    toast.warning('기출문제 파일 형식이 PDF가 아닌 것 같으니 확인 바랍니다.');
    return false;
  }
  return true;
}

/** JSON 파일 유효성 검증 — 확장자 체크 없이 항상 통과 */
function validateJsonFiles() {
  return true;
}

/** MP3 파일 유효성 검증 — 실패 시 false 반환 */
function validateMp3Files(files) {
  const invalidFiles = files.filter((f) => !f.name.toLowerCase().endsWith('.mp3'));
  if (invalidFiles.length > 0) {
    toast.warning('듣기 파일 형식이 MP3가 아닌 것 같으니 확인 바랍니다.');
    return false;
  }
  return true;
}

/**
 * FileUploadZone에서 파일 선택/드롭 시 호출되는 핸들러
 * @param {File[]} files - 선택된 파일 목록
 * @param {'pdf'|'json'} fileType - 파일 유형
 * @param {Function} validateFn - 유효성 검증 함수
 * @param {import('vue').Ref<File[]>} pendingRef - 대기 파일 ref
 */
async function handleFileSelect(files, fileType, validateFn, pendingRef) {
  if (!validateFn(files)) return;
  if (isEditMode.value) {
    await doUpload(files, fileType);
  } else {
    pendingRef.value = [...pendingRef.value, ...files];
  }
}

/** PDF 파일 선택/드롭 핸들러 */
async function handlePdfFileSelect(files) {
  await handleFileSelect(files, 'pdf', validatePdfFiles, pendingFiles);
}

/** JSON 파일 선택/드롭 핸들러 */
async function handleJsonFileSelect(files) {
  await handleFileSelect(files, 'json', validateJsonFiles, pendingJsonFiles);
}

/** MP3 파일 선택/드롭 핸들러 */
async function handleMp3FileSelect(files) {
  await handleFileSelect(files, 'mp3', validateMp3Files, pendingMp3Files);
}

/** 대기 PDF 파일 제거 (등록 모드) */
function removePendingFile(index) {
  pendingFiles.value.splice(index, 1);
}

/** 대기 JSON 파일 제거 (등록 모드) */
function removePendingJsonFile(index) {
  pendingJsonFiles.value.splice(index, 1);
}

/** 대기 MP3 파일 제거 (등록 모드) */
function removePendingMp3File(index) {
  pendingMp3Files.value.splice(index, 1);
}

/** 파일 유형별 로딩 ref 반환 */
function getLoadingRef(fileType) {
  if (fileType === 'json') return jsonFileLoading;
  if (fileType === 'mp3') return mp3FileLoading;
  return fileLoading;
}

/** 서버에 파일 업로드 실행 (수정 모드에서 사용) */
async function doUpload(files, fileType = 'pdf') {
  const loadingRef = getLoadingRef(fileType);
  loadingRef.value = true;
  try {
    await uploadFiles(form.value.exam_key, files, fileType);
    await loadFiles();
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다');
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
    toast.error(error.detail || '오류가 발생했습니다');
  }
}

/** 파일 다운로드 URL 반환 */
function getFileDownloadUrl(file) {
  return getDownloadUrl(form.value.exam_key, file.pdf_key);
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
        section: form.value.section
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
        toast.error(uploadError.detail || 'PDF 파일 업로드 중 오류가 발생했습니다');
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
        toast.error(uploadError.detail || 'JSON 파일 업로드 중 오류가 발생했습니다');
      } finally {
        jsonFileLoading.value = false;
      }
    }

    /* 등록 모드에서 pendingMp3Files(MP3)가 있으면 업로드 */
    if (pendingMp3Files.value.length > 0 && examKey) {
      mp3FileLoading.value = true;
      try {
        await uploadFiles(examKey, pendingMp3Files.value, 'mp3');
      } catch (uploadError) {
        toast.error(uploadError.detail || 'MP3 파일 업로드 중 오류가 발생했습니다');
      } finally {
        mp3FileLoading.value = false;
      }
    }

    toast.success('저장되었습니다');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다');
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
    toast.success('삭제되었습니다');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다');
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
          <option v-for="opt in store.examTypeOptions" :key="opt.code" :value="String(opt.code)">
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
          <option v-for="opt in store.tpkLevelOptions" :key="opt.code" :value="String(opt.code)">
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
          <option v-for="opt in store.sectionOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 문제(PDF) 파일 영역 -->
      <FileUploadZone
        file-type-label="PDF"
        accept=".pdf"
        accent-color="blue"
        :is-edit-mode="isEditMode"
        :enabled="isPastExamType"
        :file-list="fileList"
        :pending-files="pendingFiles"
        :loading="fileLoading"
        @file-select="handlePdfFileSelect"
        @file-delete="handleFileDelete"
        @pending-remove="removePendingFile"
      >
        <template #file-link="{ file }">
          <a
            :href="getFileDownloadUrl(file)"
            class="truncate text-sm text-blue-600 hover:underline"
            target="_blank"
          >
            {{ file.file_name }}
          </a>
        </template>
      </FileUploadZone>

      <!-- 문제(JSON) 파일 영역 -->
      <FileUploadZone
        file-type-label="JSON"
        accept="*/*"
        accent-color="teal"
        :is-edit-mode="isEditMode"
        :enabled="isPastExamType"
        :file-list="jsonFileList"
        :pending-files="pendingJsonFiles"
        :loading="jsonFileLoading"
        @file-select="handleJsonFileSelect"
        @file-delete="handleFileDelete"
        @pending-remove="removePendingJsonFile"
      >
        <template #file-link="{ file }">
          <a
            :href="getFileDownloadUrl(file)"
            class="truncate text-sm text-blue-600 hover:underline"
            target="_blank"
          >
            {{ file.file_name }}
          </a>
        </template>
      </FileUploadZone>

      <!-- 듣기(MP3) 파일 영역 -->
      <FileUploadZone
        file-type-label="MP3"
        section-label="듣기(MP3)"
        accept=".mp3"
        accent-color="purple"
        :is-edit-mode="isEditMode"
        :enabled="isPastExamType"
        :file-list="mp3FileList"
        :pending-files="pendingMp3Files"
        :loading="mp3FileLoading"
        @file-select="handleMp3FileSelect"
        @file-delete="handleFileDelete"
        @pending-remove="removePendingMp3File"
      >
        <template #file-link="{ file }">
          <a
            :href="getFileDownloadUrl(file)"
            class="truncate text-sm text-blue-600 hover:underline"
            target="_blank"
          >
            {{ file.file_name }}
          </a>
        </template>
      </FileUploadZone>
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
