<!--
  코드 목록 페이지
  - 서브 타이틀, 검색바(그룹코드 셀렉트박스 + 코드명 텍스트), 데이터 테이블, 페이지네이션으로 구성
  - 행 클릭 시 수정 모달, 등록 버튼 클릭 시 등록 모달을 표시
  - 마운트 시 그룹코드 전체 목록과 코드 페이징 목록을 조회한다.
-->
<script setup>
import { computed, onMounted, ref } from 'vue';
import { useCodeStore } from '@/stores/code';
import { useGroupCodeStore } from '@/stores/groupCode';
import * as codeApi from '@/api/code';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';
import CodeFormModal from '@/components/code/CodeFormModal.vue';

const codeStore = useCodeStore();
const groupCodeStore = useGroupCodeStore();

/** DataTable 컴포넌트 ref (generateExcel 호출용) */
const dataTableRef = ref(null);

/** 그룹코드 셀렉트박스용 — group_code 오름차순 정렬 */
const sortedGroupCodes = computed(() =>
  [...groupCodeStore.allGroupCodes].sort((a, b) => a.group_code.localeCompare(b.group_code, 'ko'))
);

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'group_code', label: '그룹코드', width: '140px' },
  { key: 'group_name', label: '그룹코드명', width: '150px', align: 'left' },
  { key: 'code', label: '코드', width: '100px' },
  { key: 'code_name', label: '코드명', width: '190px', align: 'left' },
  { key: 'code_desc', label: '코드설명', width: '250px', align: 'left' },
  { key: 'sort_order', label: '소팅순서', width: '90px' },
  { key: 'del_yn', label: '삭제여부', width: '90px' },
  { key: 'ins_user', label: '생성자', width: '120px' },
  { key: 'ins_date', label: '생성시간', width: '180px' }
];

/* ========== 모달 상태 ========== */
const showModal = ref(false);
const editData = ref(null);

/** 조회 버튼 클릭 */
function handleSearch() {
  codeStore.page = 1;
  codeStore.fetchList();
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
  codeStore.fetchList();
}

/** 페이지 변경 */
function handlePageChange(newPage) {
  codeStore.page = newPage;
  codeStore.fetchList();
}

/** 페이지당 행 수 변경 */
function handlePageSizeChange(newSize) {
  codeStore.size = newSize;
  codeStore.page = 1;
  codeStore.fetchList();
}

/**
 * 엑셀 다운로드 — 전체 코드 목록 조회(삭제 제외) 후 엑셀 생성
 * API size 최대값이 100이므로 페이지 반복 조회하여 전체 데이터를 수집한다.
 */
async function handleExcelDownload() {
  try {
    const maxSize = 100;
    let currentPage = 1;
    let allData = [];
    let totalCount = 0;

    /* 첫 페이지 조회로 전체 건수 파악 후 나머지 페이지 반복 조회 */
    do {
      const res = await codeApi.getList({ page: currentPage, size: maxSize });
      const rows = res.list || res.data || [];
      allData = allData.concat(rows);
      totalCount = res.total || 0;
      currentPage++;
    } while (allData.length < totalCount);

    /* 삭제 코드 제외 */
    allData = allData.filter((row) => row.del_yn !== 'Y');
    dataTableRef.value?.generateExcel(allData);
  } catch (error) {
    console.error('[CodeListView] 엑셀 다운로드 실패:', error);
    alert(error.detail || '엑셀 다운로드 중 오류가 발생했습니다.');
  }
}

/* ========== 초기 데이터 로드 ========== */
onMounted(() => {
  groupCodeStore.fetchAllGroupCodes();
  codeStore.fetchList();
});
</script>

<template>
  <div>
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">코드관리</h2>

    <!-- 검색바 -->
    <SearchBar @search="handleSearch" @register="handleRegister">
      <!-- 그룹코드 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 그룹코드 </label>
        <select
          v-model="codeStore.searchParams.group_code"
          class="min-w-[160px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="gc in sortedGroupCodes" :key="gc.group_code" :value="gc.group_code">
            {{ gc.group_code }} - {{ gc.group_name }}
          </option>
        </select>
      </div>

      <!-- 코드명 텍스트 입력 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 코드명 </label>
        <input
          v-model="codeStore.searchParams.code_name"
          type="text"
          class="min-w-[160px] rounded border border-gray-300 px-3 py-1.5 text-sm"
          @keyup.enter="handleSearch"
        />
      </div>
    </SearchBar>

    <!-- 데이터 테이블 -->
    <DataTable
      ref="dataTableRef"
      :columns="columns"
      :data="codeStore.list"
      :loading="codeStore.loading"
      :page-size="codeStore.size"
      :total="codeStore.total"
      excel-file-name="코드목록"
      @row-click="handleRowClick"
      @update:page-size="handlePageSizeChange"
      @excel-download="handleExcelDownload"
    />

    <!-- 페이지네이션 -->
    <Pagination
      :page="codeStore.page"
      :size="codeStore.size"
      :total="codeStore.total"
      @update:page="handlePageChange"
    />

    <!-- 등록/수정 모달 -->
    <CodeFormModal
      :visible="showModal"
      :edit-data="editData"
      @close="handleModalClose"
      @saved="handleSaved"
    />
  </div>
</template>
