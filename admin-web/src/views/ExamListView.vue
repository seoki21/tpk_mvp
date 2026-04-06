<!--
  기출시험 목록 페이지
  - 서브 타이틀, 검색바(시험유형 셀렉트박스 + 토픽레벨 셀렉트박스 + 회차 텍스트), 데이터 테이블, 페이지네이션으로 구성
  - 행 클릭 시 수정 모달, 등록 버튼 클릭 시 등록 모달을 표시
  - FILE 컬럼 'Y' 클릭 시 파일 목록 팝업 → 파일 선택 시 하단 PDF 뷰어에 표시
  - 마운트 시 코드 옵션과 시험문항 페이징 목록을 조회한다.
-->
<script setup>
import { onMounted, ref } from 'vue';
import { useExamListStore } from '@/stores/examList';
import { getFiles, getInlineViewUrl } from '@/api/examFile';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';
import ExamListFormModal from '@/components/examList/ExamListFormModal.vue';
import FilePopupMenu from '@/components/examList/FilePopupMenu.vue';
import PdfViewer from '@/components/examList/PdfViewer.vue';

const store = useExamListStore();

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'exam_year_display', label: '년도', width: '100px' },
  { key: 'exam_type_name', label: '시험유형', width: '140px', align: 'left' },
  { key: 'tpk_level_name', label: '토픽레벨', width: '140px', align: 'left' },
  { key: 'round', label: '회차', width: '80px' },
  { key: 'section_name', label: '영역', width: '140px', align: 'left' },
  { key: 'has_pdf', label: '문제(PDF)', width: '80px', sortable: false },
  { key: 'has_json', label: '문제(JSON)', width: '80px', sortable: false },
  { key: 'mp3_count', label: '듣기(MP3)', width: '80px', sortable: false },
  { key: 'del_yn', label: '삭제여부', width: '100px' },
  { key: 'ins_user', label: '생성자', width: '120px' },
  { key: 'ins_date', label: '생성시간', width: '180px' }
];

/* ========== 모달 상태 ========== */
const showModal = ref(false);
const editData = ref(null);

/* ========== 파일 팝업 메뉴 상태 ========== */
const fileList = ref([]);
const fileMenuVisible = ref(false);
const fileMenuAnchorRect = ref(null);
const fileMenuExamKey = ref(null);
const fileMenuTypeLabel = ref('');

/* ========== PDF 뷰어 상태 ========== */
const pdfUrl = ref('');
const pdfFileName = ref('');

/** 조회 버튼 클릭 */
function handleSearch() {
  store.page = 1;
  store.fetchList();
}

/** 등록 버튼 클릭 */
function handleRegister() {
  editData.value = null;
  showModal.value = true;
}

/** 행 클릭 → 수정 모달 열기 + PDF 뷰어 초기화 */
function handleRowClick(row) {
  pdfUrl.value = '';
  pdfFileName.value = '';
  editData.value = { ...row };
  showModal.value = true;
}

/** 모달 닫기 */
function handleModalClose() {
  showModal.value = false;
  editData.value = null;
}

/** 저장/삭제 완료 후 모달 닫고 목록 새로고침 */
function handleSaved() {
  showModal.value = false;
  editData.value = null;
  store.fetchList();
}

/** 페이지 변경 */
function handlePageChange(newPage) {
  store.page = newPage;
  store.fetchList();
}

/** 페이지당 행 수 변경 */
function handlePageSizeChange(newSize) {
  store.size = newSize;
  store.page = 1;
  store.fetchList();
}

/**
 * 파일 컬럼 클릭 — 해당 file_type의 파일 목록만 팝업 표시
 * @param {Object} row - 테이블 행 데이터
 * @param {Event} event - 클릭 이벤트 (팝업 위치 계산용)
 * @param {string} fileType - 'pdf', 'json', 'mp3'
 */
async function handleFileClick(row, event, fileType) {
  try {
    const res = await getFiles(row.exam_key);
    const allFiles = res.data || [];
    /* file_type별 필터링 (NULL이면 pdf로 취급) */
    if (fileType === 'pdf') {
      fileList.value = allFiles.filter((f) => !f.file_type || f.file_type === 'pdf');
    } else {
      fileList.value = allFiles.filter((f) => f.file_type === fileType);
    }
  } catch (error) {
    console.error('[FILE] 파일 목록 조회 실패:', error);
    fileList.value = [];
  }

  fileMenuExamKey.value = row.exam_key;
  fileMenuTypeLabel.value = fileType.toUpperCase();
  fileMenuAnchorRect.value = event.target.getBoundingClientRect();
  fileMenuVisible.value = true;
}

/** 팝업 메뉴에서 파일 선택 → PDF 뷰어에 표시 */
function handleFileSelect(file) {
  pdfUrl.value = getInlineViewUrl(fileMenuExamKey.value, file.pdf_key);
  pdfFileName.value = file.file_name;
  fileMenuVisible.value = false;
}

/** 팝업 메뉴 닫기 */
function handleFileMenuClose() {
  fileMenuVisible.value = false;
}

/* ========== 초기 데이터 로드 ========== */
onMounted(() => {
  store.fetchCodeOptions();
  store.fetchList();
});
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">시험 관리</h2>

    <!-- 검색바 -->
    <SearchBar @search="handleSearch" @register="handleRegister">
      <!-- 시험유형 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 시험유형 </label>
        <select
          v-model="store.searchParams.exam_type"
          class="min-w-[160px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.examTypeOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 토픽레벨 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 토픽레벨 </label>
        <select
          v-model="store.searchParams.tpk_level"
          class="min-w-[160px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.tpkLevelOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 영역 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 영역 </label>
        <select
          v-model="store.searchParams.section"
          class="min-w-[160px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.sectionOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 회차 텍스트 입력 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 회차 </label>
        <input
          v-model="store.searchParams.round"
          type="text"
          class="min-w-[160px] rounded border border-gray-300 px-3 py-1.5 text-sm"
          @keyup.enter="handleSearch"
        />
      </div>
    </SearchBar>

    <!-- 데이터 테이블 -->
    <DataTable
      :columns="columns"
      :data="store.list"
      :loading="store.loading"
      :page-size="store.size"
      :total="store.total"
      @row-click="handleRowClick"
      @update:page-size="handlePageSizeChange"
    >
      <!-- 문제(PDF) 컬럼: Y이면 파일 아이콘, 클릭 시 팝업 -->
      <template #cell-has_pdf="{ row, value }">
        <span
          v-if="value === 'Y'"
          class="cursor-pointer text-blue-600 hover:text-blue-800"
          title="PDF 파일 보기"
          @click.stop="handleFileClick(row, $event, 'pdf')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
        </span>
        <span v-else></span>
      </template>

      <!-- 문제(JSON) 컬럼: Y이면 파일 아이콘 -->
      <template #cell-has_json="{ row, value }">
        <span
          v-if="value === 'Y'"
          class="cursor-pointer text-teal-600 hover:text-teal-800"
          title="JSON 파일 보기"
          @click.stop="handleFileClick(row, $event, 'json')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="mx-auto h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
        </span>
        <span v-else></span>
      </template>

      <!-- 듣기(MP3) 컬럼: 건수 표시, 클릭 시 팝업 -->
      <template #cell-mp3_count="{ row, value }">
        <span
          v-if="value > 0"
          class="cursor-pointer text-sm text-purple-600 hover:text-purple-800 hover:underline"
          :title="`MP3 파일 ${value}건`"
          @click.stop="handleFileClick(row, $event, 'mp3')"
        >
          {{ value }}건
        </span>
        <span v-else></span>
      </template>
    </DataTable>

    <!-- 페이지네이션 -->
    <Pagination
      :page="store.page"
      :size="store.size"
      :total="store.total"
      @update:page="handlePageChange"
    />

    <!-- PDF 파일보기 영역 — 남은 높이를 모두 사용 -->
    <PdfViewer :url="pdfUrl" :file-name="pdfFileName" class="mt-4 min-h-0 flex-1" />

    <!-- 파일 목록 팝업 메뉴 -->
    <FilePopupMenu
      :visible="fileMenuVisible"
      :files="fileList"
      :file-type-label="fileMenuTypeLabel"
      :anchor-rect="fileMenuAnchorRect"
      @select="handleFileSelect"
      @close="handleFileMenuClose"
    />

    <!-- 등록/수정 모달 -->
    <ExamListFormModal
      :visible="showModal"
      :edit-data="editData"
      @close="handleModalClose"
      @saved="handleSaved"
    />
  </div>
</template>
