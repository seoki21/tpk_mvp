<!--
  등급 관리 페이지 — tb_grade_score 관리
  - 검색 조건: 시험종류 셀렉트박스
  - 전체 목록 조회 (페이징 없음, 데이터 건수가 적음)
  - 행 클릭 시 수정 모달, 등록 버튼 클릭 시 등록 모달을 표시
-->
<script setup>
import { onMounted, ref } from 'vue';
import { useGradeScoreStore } from '@/stores/gradeScore';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import GradeScoreFormModal from '@/components/gradeScore/GradeScoreFormModal.vue';
import * as codeApi from '@/api/code';

const store = useGradeScoreStore();

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'tpk_type_name', label: '시험종류', width: '100px' },
  { key: 'tpk_level_name', label: '토픽레벨', width: '100px' },
  { key: 'tpk_grade_name', label: '등급', width: '70px' },
  { key: 'min_score', label: '최소점수', width: '90px' },
  { key: 'max_score', label: '최대점수', width: '90px' },
  { key: 'total_score', label: '총점', width: '80px' },
  { key: 'del_yn', label: '삭제여부', width: '90px' },
  { key: 'ins_user', label: '등록자', width: '100px' },
  { key: 'ins_date', label: '등록일시', width: '180px' }
];

/* ========== 검색 셀렉트박스용 코드 목록 ========== */
const tpkTypeCodes = ref([]);

/** 셀렉트박스용 시험종류 코드 목록 로드 */
async function loadSearchCodes() {
  try {
    const res = await codeApi.getCodesByGroup('topik_type');
    tpkTypeCodes.value = res.data || [];
  } catch (error) {
    console.error('[GradeScoreView] 코드 목록 로드 실패:', error);
  }
}

/* ========== 모달 상태 ========== */
const showModal = ref(false);
const editData = ref(null);

/** 조회 버튼 클릭 */
function handleSearch() {
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

/* ========== 초기 데이터 로드 ========== */
onMounted(() => {
  loadSearchCodes();
  store.fetchList();
});
</script>

<template>
  <div>
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">등급 관리</h2>

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
    </SearchBar>

    <!-- 데이터 테이블 (페이징 없음) -->
    <DataTable
      :columns="columns"
      :data="store.list"
      :loading="store.loading"
      @row-click="handleRowClick"
    />

    <!-- 등록/수정 모달 -->
    <GradeScoreFormModal
      :visible="showModal"
      :edit-data="editData"
      @close="handleModalClose"
      @saved="handleSaved"
    />
  </div>
</template>
