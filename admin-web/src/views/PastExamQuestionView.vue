<!--
  기출문제 관리 페이지
  - 상단 조회조건: 기출문제 selectbox + 파일 selectbox + 파일 아이콘(JSON 변환 팝업) + 검수완료 버튼
  - 하단: 문제 목록(JSON → 화면) — 좌측 JSON 텍스트 + 우측 UI 렌더링
  - 마운트 시 기출문제 목록을 조회한다.
-->
<script setup>
import { onMounted, ref } from 'vue';
import { useExamQuestionStore } from '@/stores/examQuestion';
import { bulkSave } from '@/api/examQuestion';
import ExamConvertModal from '@/components/examQuestion/ExamConvertModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';

const store = useExamQuestionStore();

/* ========== JSON 변환 팝업 상태 ========== */
const showConvertModal = ref(false);

/* ========== 확인 다이얼로그 ========== */
const showConfirm = ref(false);
const confirmMessage = ref('');
const confirmCallback = ref(null);

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

/** 파일 아이콘 클릭 → JSON 변환 팝업 열기 */
function handleConvertClick() {
  if (!store.selectedExamKey || !store.selectedPdfKey) {
    alert('기출문제와 파일을 먼저 선택하세요.');
    return;
  }
  showConvertModal.value = true;
}

/** JSON 변환 완료 후 → 문제/지시문 목록 새로고침 */
async function handleConvertSaved() {
  showConvertModal.value = false;
  if (store.selectedExamKey) {
    await store.fetchQuestionsAndInstructions(store.selectedExamKey);
  }
}

/**
 * 개별 문제/지시문 저장 버튼
 * question_json 또는 ins_json 기반으로 단건 저장
 */
async function handleSaveItem(item) {
  if (!store.selectedExamKey) return;

  confirmMessage.value = '저장하시겠습니까?';
  confirmCallback.value = async () => {
    try {
      const payload = { questions: [], instructions: [] };

      if (item._type === 'question') {
        payload.questions.push({
          question_no: item.question_no,
          section: item.section,
          question_type: item.question_type,
          struct_type: item.struct_type,
          question_json: item.question_json,
          score: item.score,
          difficulty: item.difficulty
        });
      } else {
        payload.instructions.push({
          ins_no: item.ins_no,
          ins_json: item.ins_json
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
 * JSON 텍스트를 파싱하여 UI에 표시할 객체로 변환
 * 파싱 실패 시 null 반환
 */
function parseJson(jsonStr) {
  if (!jsonStr) return null;
  try {
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
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

        <!-- 파일 아이콘 — 클릭 시 JSON 변환 팝업 -->
        <button
          class="rounded p-1.5 text-blue-600 hover:bg-blue-50 hover:text-blue-800 disabled:text-gray-400 disabled:hover:bg-transparent"
          title="기출문항 변환(JSON)"
          :disabled="!store.selectedPdfKey"
          @click="handleConvertClick"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
        </button>
      </div>

      <!-- 검수완료 버튼 (향후 기능) -->
      <div class="ml-auto">
        <button
          class="rounded border border-gray-400 bg-gray-200 px-4 py-1.5 text-sm hover:bg-gray-300"
          :disabled="!store.selectedExamKey"
        >
          검수완료
        </button>
      </div>
    </div>

    <!-- 문제 목록(JSON → 화면) -->
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden rounded border border-gray-300">
      <div class="shrink-0 border-b border-gray-300 bg-gray-50 px-4 py-2">
        <span class="text-sm font-medium text-gray-700">문제 목록(JSON → 화면)</span>
      </div>

      <!-- 스크롤 영역 — 부모 flex-1로 남은 높이 전체 사용 -->
      <div class="flex-1 overflow-y-auto">
        <!-- 데이터 없음 -->
        <div
          v-if="!store.loading && store.mergedItems.length === 0"
          class="flex h-40 items-center justify-center text-gray-400"
        >
          {{ store.selectedExamKey ? '문제 데이터가 없습니다.' : '기출문제를 선택하세요.' }}
        </div>

        <!-- 로딩 -->
        <div v-if="store.loading" class="flex h-40 items-center justify-center text-gray-400">
          조회 중...
        </div>

        <!-- 항목 목록 -->
        <div v-if="!store.loading && store.mergedItems.length > 0" class="divide-y divide-gray-200">
          <div v-for="(item, index) in store.mergedItems" :key="index" class="flex gap-4 p-4">
            <!-- 좌측: JSON 텍스트 (40%, 세로 스크롤만) -->
            <div class="w-2/5 shrink-0">
              <pre
                class="max-h-[300px] overflow-y-auto overflow-x-hidden rounded border border-gray-200 bg-gray-50 p-2 text-xs leading-relaxed text-gray-600"
                >{{
                  item._type === 'question' ? item.question_json || '{}' : item.ins_json || '{}'
                }}</pre
              >
            </div>

            <!-- 우측: UI 렌더링 (60%) -->
            <div class="min-w-0 w-3/5">
              <!-- 지시문 렌더링 -->
              <template v-if="item._type === 'instruction'">
                <div class="flex items-start justify-between">
                  <h3 class="mb-2 text-base font-bold text-gray-800">지시문 {{ item.ins_no }}</h3>
                  <button
                    class="shrink-0 rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100"
                    @click="handleSaveItem(item)"
                  >
                    저장
                  </button>
                </div>
                <template v-if="parseJson(item.ins_json)">
                  <p class="mb-1 text-sm text-gray-700">
                    {{ parseJson(item.ins_json).full_sentence }}
                  </p>
                  <div
                    v-if="parseJson(item.ins_json).paragraph"
                    class="mt-2 rounded border border-gray-200 bg-white p-3 text-sm text-gray-600"
                  >
                    <div class="mb-1 text-center text-xs text-gray-400">&lt;보기&gt;</div>
                    {{ parseJson(item.ins_json).paragraph }}
                  </div>
                </template>
                <p v-else class="text-sm text-gray-400">JSON 파싱 불가</p>
              </template>

              <!-- 문제 렌더링 -->
              <template v-if="item._type === 'question'">
                <div class="flex items-start justify-between">
                  <h3 class="mb-2 text-base font-bold text-gray-800">
                    문제 {{ item.question_no }}
                    <span v-if="item.score" class="text-sm font-normal text-gray-500"
                      >, {{ item.score }}점</span
                    >
                    <span v-if="item.section" class="text-sm font-normal text-gray-500"
                      >, {{ item.section }}</span
                    >
                    <span v-if="item.question_type" class="text-sm font-normal text-gray-500"
                      >, {{ item.question_type }}</span
                    >
                    <span v-if="item.difficulty" class="text-sm font-normal text-gray-500"
                      >, 난이도 {{ item.difficulty }}</span
                    >
                  </h3>
                  <button
                    class="shrink-0 rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100"
                    @click="handleSaveItem(item)"
                  >
                    저장
                  </button>
                </div>
                <template v-if="parseJson(item.question_json)">
                  <div
                    v-if="parseJson(item.question_json).full_sentence"
                    class="mb-2 text-sm text-gray-600"
                  >
                    {{ parseJson(item.question_json).full_sentence }}
                  </div>
                  <div
                    v-if="parseJson(item.question_json).paragraph"
                    class="mb-2 rounded border border-gray-200 bg-white p-3 text-sm text-gray-600"
                  >
                    <div class="mb-1 text-center text-xs text-gray-400">&lt;보기&gt;</div>
                    {{ parseJson(item.question_json).paragraph }}
                  </div>
                  <p
                    v-if="parseJson(item.question_json).question_text"
                    class="mb-2 text-sm text-gray-700"
                  >
                    {{ parseJson(item.question_json).question_text }}
                  </p>
                  <!-- 선택지 -->
                  <div
                    v-if="parseJson(item.question_json).choices"
                    class="mt-2 grid grid-cols-2 gap-2 text-sm"
                  >
                    <span
                      v-for="(choice, ci) in parseJson(item.question_json).choices"
                      :key="ci"
                      class="text-gray-700"
                    >
                      {{ choice }}
                    </span>
                  </div>
                </template>
                <p v-else class="text-sm text-gray-400">JSON 파싱 불가</p>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 기출문항 변환(JSON) 팝업 -->
    <ExamConvertModal
      :visible="showConvertModal"
      :exam-key="store.selectedExamKey"
      :pdf-key="store.selectedPdfKey"
      :exam-info="store.selectedExam"
      :file-info="store.selectedFile"
      @close="showConvertModal = false"
      @saved="handleConvertSaved"
    />

    <!-- 확인 다이얼로그 -->
    <ConfirmDialog
      :visible="showConfirm"
      :message="confirmMessage"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    />
  </div>
</template>
