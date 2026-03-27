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
 * JSON 문자열을 들여쓰기 포매팅 후 구문 강조 HTML로 변환
 * 키(보라), 문자열 값(초록), 숫자(파랑), boolean/null(주황) 색상 적용
 */
function highlightJson(jsonStr) {
  if (!jsonStr) return '{}';
  let pretty;
  try {
    pretty = JSON.stringify(JSON.parse(jsonStr), null, 2);
  } catch {
    return jsonStr.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  return pretty
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"([^"]+)"(?=\s*:)/g, '<span class="text-purple-600">"$1"</span>')
    .replace(/:\s*"([^"]*)"/g, ': <span class="text-green-600">"$1"</span>')
    .replace(/:\s*(\d+\.?\d*)/g, ': <span class="text-blue-600">$1</span>')
    .replace(/:\s*(true|false|null)/g, ': <span class="text-orange-600">$1</span>');
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
            <!-- 좌측: JSON 텍스트 (40%, 구문 강조) -->
            <div class="w-2/5 shrink-0">
              <pre
                class="max-h-[300px] overflow-y-auto overflow-x-hidden whitespace-pre-wrap break-all rounded border border-gray-200 bg-gray-50 p-2 text-xs leading-relaxed text-gray-600"
                v-html="
                  highlightJson(
                    item._type === 'question' ? item.question_json || '{}' : item.ins_json || '{}'
                  )
                "
              ></pre>
            </div>

            <!-- 우측: 시험지 UI (60%) -->
            <div class="w-3/5 min-w-0">
              <!-- ===== 지시문 ===== -->
              <template v-if="item._type === 'instruction'">
                <!-- 상단: 지시문 {no} [{no_list}] {score}점 + 저장 -->
                <div class="mb-3 flex items-center justify-between border-b border-gray-200 pb-2">
                  <div class="flex items-baseline gap-2 text-sm">
                    <span class="font-bold text-gray-800">지시문 {{ item.ins_no }}</span>
                    <span
                      v-if="item._parsed && item._parsed.no_list && item._parsed.no_list.length"
                      class="text-gray-500"
                    >
                      [{{ item._parsed.no_list.join(', ') }}]
                    </span>
                    <span v-if="item._parsed && item._parsed.score" class="text-gray-500">
                      {{ item._parsed.score }}점
                    </span>
                  </div>
                  <button
                    class="shrink-0 rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100"
                    @click="handleSaveItem(item)"
                  >
                    저장
                  </button>
                </div>
                <!-- 본문 -->
                <template v-if="item._parsed">
                  <p
                    v-if="item._parsed.full_sentence"
                    class="mb-2 text-sm leading-relaxed text-gray-800"
                  >
                    {{ item._parsed.full_sentence }}
                  </p>
                  <div
                    v-if="item._parsed.paragraph"
                    class="mt-2 rounded border border-gray-300 bg-white p-3 text-sm leading-relaxed text-gray-700"
                  >
                    <p class="whitespace-pre-wrap">{{ item._parsed.paragraph }}</p>
                  </div>
                </template>
                <p v-else class="text-sm text-gray-400">JSON 파싱 불가</p>
              </template>

              <!-- ===== 문항 ===== -->
              <template v-if="item._type === 'question'">
                <!-- 상단: {no}번 {section} {type} {score}점 + 저장 -->
                <div class="mb-3 flex items-center justify-between border-b border-gray-200 pb-2">
                  <div class="flex items-baseline gap-2 text-sm">
                    <span class="font-bold text-gray-800">{{ item.question_no }}번</span>
                    <span
                      v-if="item.section"
                      class="rounded bg-blue-50 px-1.5 py-0.5 text-blue-700"
                    >
                      {{ item.section }}
                    </span>
                    <span
                      v-if="item.question_type"
                      class="rounded bg-green-50 px-1.5 py-0.5 text-green-700"
                    >
                      {{ item.question_type }}
                    </span>
                    <span
                      v-if="item.score"
                      class="rounded bg-amber-50 px-1.5 py-0.5 text-amber-700"
                    >
                      {{ item.score }}점
                    </span>
                  </div>
                  <button
                    class="shrink-0 rounded border border-gray-300 px-3 py-1 text-xs hover:bg-gray-100"
                    @click="handleSaveItem(item)"
                  >
                    저장
                  </button>
                </div>
                <!-- 본문 -->
                <template v-if="item._parsed">
                  <p
                    v-if="item._parsed.full_sentence"
                    class="mb-2 text-sm leading-relaxed text-gray-800"
                  >
                    {{ item._parsed.full_sentence }}
                  </p>
                  <div
                    v-if="item._parsed.paragraph"
                    class="mb-3 rounded border border-gray-300 bg-white p-3 text-sm leading-relaxed text-gray-700"
                  >
                    <p class="whitespace-pre-wrap">{{ item._parsed.paragraph }}</p>
                  </div>
                  <p
                    v-if="item._parsed.question_text"
                    class="mb-2 text-sm leading-relaxed text-gray-800"
                  >
                    {{ item.question_no }}. {{ item._parsed.question_text }}
                  </p>
                  <!-- 선택지 -->
                  <div
                    v-if="item._parsed.choices"
                    class="mb-2 grid grid-cols-2 gap-x-4 gap-y-1 text-sm"
                  >
                    <span
                      v-for="(choice, ci) in item._parsed.choices"
                      :key="ci"
                      class="text-gray-700"
                    >
                      {{ choice }}
                    </span>
                  </div>
                  <!-- 정답 / 해설 영역 -->
                  <div
                    v-if="item._parsed.correct_answer || (item._parsed.feedback && item._parsed.feedback.length)"
                    class="mt-3 rounded bg-gray-50 px-3 py-2"
                  >
                    <p v-if="item._parsed.correct_answer" class="mb-1 text-xs text-gray-600">
                      <span class="font-medium">정답:</span>
                      <span class="ml-1 font-bold text-blue-700">
                        {{ item._parsed.correct_answer }}번
                      </span>
                    </p>
                    <div
                      v-if="item._parsed.feedback && item._parsed.feedback.length"
                      class="space-y-0.5"
                    >
                      <div
                        v-for="(fb, fi) in item._parsed.feedback"
                        :key="fi"
                        class="text-xs"
                        :class="
                          parseFeedback(fb).isCorrect ? 'text-green-700' : 'text-gray-500'
                        "
                      >
                        <span class="font-medium">{{ parseFeedback(fb).label }}</span>
                        <span class="ml-1">{{ parseFeedback(fb).text }}</span>
                      </div>
                    </div>
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
