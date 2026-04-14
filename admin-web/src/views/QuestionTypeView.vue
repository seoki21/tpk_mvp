<!--
  문항유형 관리 페이지 — 시험 템플릿 (tb_exam_template) 관리
  - 기존 관리 화면과 동일한 패턴: SearchBar + DataTable + Pagination + FormModal
  - 검색 조건: 시험종류 / 토픽레벨 / 영역 셀렉트박스
  - 행 클릭 시 수정 모달, 등록 버튼 클릭 시 등록 모달을 표시
  - 마운트 시 전체 목록 조회
-->
<script setup>
import { onMounted, ref } from 'vue';
import { useExamTemplateStore } from '@/stores/examTemplate';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';
import ExamTemplateFormModal from '@/components/examTemplate/ExamTemplateFormModal.vue';
import * as codeApi from '@/api/code';

const store = useExamTemplateStore();

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'tpk_type_name', label: '시험종류', width: '100px' },
  { key: 'tpk_level_name', label: '토픽레벨', width: '100px' },
  { key: 'section_name', label: '영역', width: '80px' },
  { key: 'question_no', label: '문항번호', width: '90px' },
  { key: 'passage_type_name', label: '지문유형', width: '200px', align: 'left' },
  { key: 'question_type_name', label: '문항유형', width: '280px', align: 'left' },
  { key: 'del_yn', label: '삭제여부', width: '90px' },
  { key: 'ins_user', label: '등록자', width: '100px' },
  { key: 'ins_date', label: '등록일시', width: '180px' }
];

/* ========== 검색 셀렉트박스용 코드 목록 ========== */
const tpkTypeCodes = ref([]);
const tpkLevelCodes = ref([]);
const sectionCodes = ref([]);

/** 셀렉트박스용 코드 목록 로드 */
async function loadSearchCodes() {
  try {
    const [tpkTypeRes, tpkLevelRes, sectionRes] = await Promise.all([
      codeApi.getCodesByGroup('topik_type'),
      codeApi.getCodesByGroup('tpk_level'),
      codeApi.getCodesByGroup('section')
    ]);
    tpkTypeCodes.value = tpkTypeRes.data || [];
    tpkLevelCodes.value = tpkLevelRes.data || [];
    sectionCodes.value = sectionRes.data || [];
  } catch (error) {
    console.error('[QuestionTypeView] 코드 목록 로드 실패:', error);
  }
}

/* ========== 모달 상태 ========== */
const showModal = ref(false);
const editData = ref(null);

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

/** 행 클릭 → 수정 모달 열기 */
function handleRowClick(row) {
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

/* ========== 초기 데이터 로드 ========== */
onMounted(() => {
  loadSearchCodes();
  store.fetchList();
});
</script>

<template>
  <div>
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">문항유형 관리</h2>

    <!-- 검색바 -->
    <SearchBar @search="handleSearch" @register="handleRegister">
      <!-- 시험종류 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">시험종류</label>
        <select
          v-model="store.searchParams.tpk_type"
          class="min-w-[120px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="c in tpkTypeCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
      </div>

      <!-- 토픽레벨 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">토픽레벨</label>
        <select
          v-model="store.searchParams.tpk_level"
          class="min-w-[120px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="c in tpkLevelCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
      </div>

      <!-- 영역 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">영역</label>
        <select
          v-model="store.searchParams.section"
          class="min-w-[100px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="c in sectionCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
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
    />

    <!-- 페이지네이션 -->
    <Pagination
      :page="store.page"
      :size="store.size"
      :total="store.total"
      @update:page="handlePageChange"
    />

    <!-- 등록/수정 모달 -->
    <ExamTemplateFormModal
      :visible="showModal"
      :edit-data="editData"
      @close="handleModalClose"
      @saved="handleSaved"
    />
  </div>
</template>
