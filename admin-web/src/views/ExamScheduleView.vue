<!--
  시험일정 관리 페이지 — tb_exam_schedule + tb_exam_location 관리
  - 검색 조건: 시험종류 셀렉트박스
  - 목록: 회차별 1행, 지역 수 및 지역명 요약 표시
  - 행 클릭 시 수정 모달, 등록 버튼 클릭 시 등록 모달 표시
-->
<script setup>
import { onMounted, ref } from 'vue';
import { useExamScheduleStore } from '@/stores/examSchedule';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';
import ExamScheduleFormModal from '@/components/examSchedule/ExamScheduleFormModal.vue';
import * as codeApi from '@/api/code';

const store = useExamScheduleStore();

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'tpk_type_name', label: '시험종류', width: '100px' },
  { key: 'round', label: '회차', width: '110px' },
  { key: 'region_names', label: '지역', width: '160px', align: 'left', sortable: false },
  { key: 'test_dates', label: '시험일', width: '130px', align: 'left', sortable: false },
  { key: 'ins_date', label: '등록일시', width: '180px' }
];

/* ========== 검색 셀렉트박스용 코드 목록 ========== */
const tpkTypeCodes = ref([]);

async function loadSearchCodes() {
  try {
    const res = await codeApi.getCodesByGroup('topik_type');
    tpkTypeCodes.value = res.data || [];
  } catch (error) {
    console.error('[ExamScheduleView] 코드 목록 로드 실패:', error);
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

/** 저장/삭제 완료 후 목록 새로고침 */
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
    <h2 class="mb-4 text-xl font-bold text-gray-800">시험일정 관리</h2>

    <!-- 검색바 -->
    <SearchBar @search="handleSearch" @register="handleRegister">
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
      <!-- 회차 셀 — 숫자를 "제N회" 형식으로 표시 -->
      <template #cell-round="{ value }">
        <span>제{{ value }}회</span>
      </template>

      <!-- 지역 셀 — 줄바꿈(\n)으로 분리하여 각 지역명을 행으로 표시 -->
      <template #cell-region_names="{ value }">
        <div v-if="value" class="space-y-1 py-0.5">
          <div v-for="(name, idx) in value.split('\n')" :key="idx" class="text-sm text-gray-700">
            {{ name }}
          </div>
        </div>
        <span v-else class="text-gray-400">-</span>
      </template>

      <!-- 시험일 셀 — 줄바꿈(\n)으로 분리하여 각 날짜를 행으로 표시 -->
      <template #cell-test_dates="{ value }">
        <div v-if="value" class="space-y-1 py-0.5">
          <div v-for="(date, idx) in value.split('\n')" :key="idx" class="text-sm text-gray-500">
            {{ date }}
          </div>
        </div>
        <span v-else class="text-gray-400">-</span>
      </template>
    </DataTable>

    <!-- 페이지네이션 -->
    <Pagination
      :page="store.page"
      :size="store.size"
      :total="store.total"
      @update:page="handlePageChange"
    />

    <!-- 등록/수정 모달 -->
    <ExamScheduleFormModal
      :visible="showModal"
      :edit-data="editData"
      @close="handleModalClose"
      @saved="handleSaved"
    />
  </div>
</template>
