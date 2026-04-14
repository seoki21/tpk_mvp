<!--
  기출문항 관리 페이지 (듣기 영역)
  - 상단 조회조건: 통합 selectbox (시험+영역+파일) + API 호출 버튼 + 전체 저장 버튼
  - 하단: 문제 목록(JSON → 화면) — 좌측 JSON 텍스트 + 우측 듣기 문항 UI (MP3 플레이어 포함)
  - 마운트 시 기출문제 목록을 조회한다.
-->
<script setup>
import { onMounted } from 'vue';
import { useExamQuestionCommon } from '@/composables/useExamQuestionCommon';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import LocaleSelectDialog from '@/components/examQuestion/LocaleSelectDialog.vue';
import ExamConvertPopup from '@/components/examQuestion/ExamConvertPopup.vue';
import ExamQuestionHeader from '@/components/examQuestion/ExamQuestionHeader.vue';
import ExamInstructionCard from '@/components/examQuestion/ExamInstructionCard.vue';
import ExamListeningQuestionCard from '@/components/examQuestion/ExamListeningQuestionCard.vue';
import ImageCropPopup from '@/components/examQuestion/ImageCropPopup.vue';
import JsonEditorPanel from '@/components/examQuestion/JsonEditorPanel.vue';

const {
  store,
  /* 확인 다이얼로그 */
  showConfirm,
  confirmMessage,
  handleConfirm,
  handleCancel,
  /* JSON 편집 */
  getEditState,
  handleJsonEditFromPanel,
  setJsonTab,
  getActiveJsonText,
  getActiveJsonError,
  /* 통합 selectbox + API 호출 팝업 */
  showConvertPopup,
  handleCombinedChange,
  handleConvertClick,
  handleConvertPopupClose,
  handleConvertPopupSaved,
  /* 저장 */
  handleSaveAll,
  /* 데이터 추출 */
  getCorrectAnswer,
  getFeedbackData,
  /* 피드백 생성 (locale 선택 팝업) */
  feedbackGenerating,
  showLocaleDialog,
  existingFeedbackLocales,
  handleLocaleConfirm,
  handleLocaleCancel,
  handleGenerateFeedbackForItem,
  /* 단건 저장 */
  itemSaving,
  handleSaveItemSingle,
  /* 이미지 생성 */
  imageGenerating,
  handleGenerateImages,
  /* JSON 파일 임포트 */
  handleImportQuestionJson,
  handleImportFeedbackJson,
  /* 수동 이미지 생성 */
  showImageCropPopup,
  cropPopupImageItems,
  handleManualGenerateImages,
  handleCropApply,
  handleCropPopupClose,
  /* 코드 목록 (셀렉트박스) */
  sectionCodes,
  passageTypeCodes,
  questionTypeCodes,
  loadCodeOptions,
  handleCodeFieldChange,
  /* 기타 */
  handleToggleJsonFilter,
  handleRetryExamOptions
} = useExamQuestionCommon();

/* ========== 초기 데이터 로드 ========== */
onMounted(() => {
  store.fetchExamOptions();
  loadCodeOptions();
});
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">기출문항 관리 (듣기)</h2>

    <!-- 상단 조회조건 (공통 컴포넌트) -->
    <ExamQuestionHeader
      :store="store"
      @combined-change="handleCombinedChange"
      @convert-click="handleConvertClick"
      @generate-images="handleGenerateImages"
      @manual-generate-images="handleManualGenerateImages"
      @import-question-json="handleImportQuestionJson"
      @import-feedback-json="handleImportFeedbackJson"
      @save-all="handleSaveAll"
      @toggle-json-filter="handleToggleJsonFilter"
      @retry-exam-options="handleRetryExamOptions"
    />

    <!-- 문제 목록(JSON → 화면) -->
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden rounded border border-gray-300">
      <div
        class="flex shrink-0 items-center justify-between border-b border-gray-300 bg-gray-50 px-4 py-2"
      >
        <div>
          <span class="text-sm font-medium text-gray-700">문제 목록 (듣기)</span>
          <span class="ml-2 text-xs text-gray-400"
            >※ JSON 데이터를 수정하면 우측 화면에서 실시간으로 결과를 확인할 수 있습니다</span
          >
        </div>
      </div>

      <!-- 스크롤 영역 -->
      <div class="flex-1 overflow-y-auto">
        <!-- 데이터 없음 -->
        <div
          v-if="!store.loading && store.mergedItems.length === 0"
          class="flex h-40 items-center justify-center text-gray-400"
        >
          {{ !store.selectedExamKey ? '기출문제를 선택하세요.' : '문제 데이터가 없습니다.' }}
        </div>

        <!-- 로딩 -->
        <div v-if="store.loading" class="flex h-40 items-center justify-center text-gray-400">
          조회 중...
        </div>

        <!-- 항목 목록 -->
        <div v-if="!store.loading && store.mergedItems.length > 0" class="divide-y divide-gray-200">
          <div
            v-for="item in store.mergedItems"
            :key="item._type + '_' + (item._type === 'question' ? item.question_no : item.ins_no)"
            class="flex gap-4 p-4"
          >
            <!-- 좌측: JSON 편집 영역 (40%) -->
            <JsonEditorPanel
              :item-type="item._type"
              :json-text="getActiveJsonText(item)"
              :has-error="getActiveJsonError(item)"
              :active-tab="item._type === 'question' ? getEditState(item).activeTab : 'question'"
              :feedback-generating="feedbackGenerating"
              :item-saving="itemSaving"
              @update:json-text="(val) => handleJsonEditFromPanel(item, val)"
              @update:active-tab="(tab) => setJsonTab(item, tab)"
              @generate-feedback="handleGenerateFeedbackForItem(item)"
              @save-item="handleSaveItemSingle(item)"
            />

            <!-- 우측: 시험지 UI (60%) — 듣기 문항 카드 -->
            <div class="w-3/5 min-w-0">
              <!-- 지시문 렌더링 (공통) -->
              <ExamInstructionCard
                v-if="item._type === 'instruction'"
                :item="item"
                :parsed="getEditState(item).parsed"
              />
              <!-- 듣기 문항 렌더링 (MP3 플레이어 포함) -->
              <ExamListeningQuestionCard
                v-if="item._type === 'question'"
                :item="item"
                :parsed="getEditState(item).parsed"
                :correct-answer="getCorrectAnswer(item)"
                :feedback-data="getFeedbackData(item)"
                :mp3-file="store.mp3FileMap[item.question_no] || null"
                :exam-key="store.selectedExamKey"
                :section-codes="sectionCodes"
                :passage-type-codes="passageTypeCodes"
                :question-type-codes="questionTypeCodes"
                @code-change="handleCodeFieldChange"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 확인 다이얼로그 -->
    <ConfirmDialog
      :visible="showConfirm"
      :message="confirmMessage"
      @confirm="handleConfirm"
      @cancel="handleCancel"
    />

    <!-- locale 선택 다이얼로그 (피드백 생성용) -->
    <LocaleSelectDialog
      :visible="showLocaleDialog"
      :existing-locales="existingFeedbackLocales"
      @confirm="handleLocaleConfirm"
      @cancel="handleLocaleCancel"
    />

    <!-- API 호출 팝업 -->
    <ExamConvertPopup
      :visible="showConvertPopup"
      :exam-key="store.selectedExamKey"
      :pdf-key="store.selectedPdfKey"
      @close="handleConvertPopupClose"
      @saved="handleConvertPopupSaved"
    />

    <!-- 수동 이미지 생성 팝업 -->
    <ImageCropPopup
      :visible="showImageCropPopup"
      :exam-key="store.selectedExamKey"
      :pdf-key="store.selectedPdfKey"
      :image-items="cropPopupImageItems"
      @apply="handleCropApply"
      @close="handleCropPopupClose"
    />
  </div>
</template>
