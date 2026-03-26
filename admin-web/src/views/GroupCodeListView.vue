<!--
  그룹코드 목록 페이지
  - 서브 타이틀, 검색바(그룹코드 셀렉트박스 + 코드명 텍스트), 데이터 테이블, 페이지네이션으로 구성
  - 행 클릭 시 수정 모달, 등록 버튼 클릭 시 등록 모달을 표시
  - 마운트 시 전체 그룹코드 목록과 페이징 목록을 조회한다.
-->
<script setup>
import { onMounted } from 'vue';
import { ref } from 'vue';
import { useGroupCodeStore } from '@/stores/groupCode';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';
import GroupCodeFormModal from '@/components/groupCode/GroupCodeFormModal.vue';

const store = useGroupCodeStore();

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'group_code', label: '그룹코드', width: '180px' },
  { key: 'group_name', label: '코드명', width: '200px', align: 'left' },
  { key: 'group_desc', label: '코드설명', width: '280px', align: 'left' },
  { key: 'del_yn', label: '삭제여부', width: '100px' },
  { key: 'ins_user', label: '생성자', width: '120px' },
  { key: 'ins_date', label: '생성시간', width: '180px' }
];

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
  store.fetchAllGroupCodes();
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
  store.fetchAllGroupCodes();
  store.fetchList();
});
</script>

<template>
  <div>
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">그룹코드관리</h2>

    <!-- 검색바 -->
    <SearchBar @search="handleSearch" @register="handleRegister">
      <!-- 그룹코드 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 그룹코드 </label>
        <select
          v-model="store.searchParams.group_code"
          class="min-w-[160px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="gc in store.allGroupCodes" :key="gc.group_code" :value="gc.group_code">
            {{ gc.group_code }} - {{ gc.group_name }}
          </option>
        </select>
      </div>

      <!-- 코드명 텍스트 입력 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 코드명 </label>
        <input
          v-model="store.searchParams.group_name"
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
    />

    <!-- 페이지네이션 -->
    <Pagination
      :page="store.page"
      :size="store.size"
      :total="store.total"
      @update:page="handlePageChange"
    />

    <!-- 등록/수정 모달 -->
    <GroupCodeFormModal
      :visible="showModal"
      :edit-data="editData"
      @close="handleModalClose"
      @saved="handleSaved"
    />
  </div>
</template>
