<!--
  연습문항 관리 목록 페이지
  - 상단: 검색바 (시험유형, 토픽레벨, 영역, 생성방법, 상태) + 조회/등록 버튼
  - 중단: 데이터 테이블 + 페이지네이션
  - 하단: 문제 목록 영역 (추후 연동)
  - 등록: 팝업 모달로 연습문제 생성 요청
-->
<script setup>
import { onMounted } from 'vue';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';
import PracticeRequestFormModal from '@/components/practiceQuestion/PracticeRequestFormModal.vue';
import { usePracticeRequestStore } from '@/stores/practiceRequest';
import { ref } from 'vue';

const store = usePracticeRequestStore();

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'request_key', label: '요청순번', width: '100px' },
  { key: 'status_name', label: '상태', width: '100px' },
  { key: 'exam_type_name', label: '시험유형', width: '140px', align: 'left' },
  { key: 'tpk_level_name', label: '토픽레벨', width: '120px', align: 'left' },
  { key: 'section_name', label: '영역', width: '120px', align: 'left' },
  { key: 'difficulty_name', label: '난이도', width: '100px' },
  { key: 'question_count', label: '문항수', width: '80px' },
  { key: 'gen_method_name', label: '생성방법', width: '100px' },
  { key: 'ins_user', label: '등록자', width: '120px' },
  { key: 'ins_date', label: '등록일시', width: '180px' }
];

/* ========== 등록/수정 팝업 ========== */
const showModal = ref(false);
const editData = ref(null);

/** 조회 버튼 */
function handleSearch() {
  store.page = 1;
  store.fetchList();
}

/** 등록 버튼 → 모달 팝업 (등록 모드) */
function handleRegister() {
  editData.value = null;
  showModal.value = true;
}

/** 행 클릭 → 모달 팝업 (수정 모드) */
function handleRowClick(row) {
  editData.value = row;
  showModal.value = true;
}

/** 모달 닫기 */
function handleModalClose() {
  showModal.value = false;
  editData.value = null;
}

/** 저장/삭제 완료 → 목록 새로고침 */
function handleModalSaved() {
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

/* ========== 초기 로드 ========== */
onMounted(() => {
  store.fetchCodeOptions();
  store.fetchList();
});
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">연습문항 관리</h2>

    <!-- 검색바 -->
    <SearchBar @search="handleSearch" @register="handleRegister">
      <!-- 시험유형 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">시험유형</label>
        <select
          v-model="store.searchParams.exam_type"
          class="min-w-[140px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.examTypeOptions" :key="opt.code" :value="opt.code">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 토픽레벨 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">토픽레벨</label>
        <select
          v-model="store.searchParams.tpk_level"
          class="min-w-[140px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.tpkLevelOptions" :key="opt.code" :value="opt.code">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 영역 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">영역</label>
        <select
          v-model="store.searchParams.section"
          class="min-w-[140px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.sectionOptions" :key="opt.code" :value="opt.code">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 생성방법 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">생성방법</label>
        <select
          v-model="store.searchParams.gen_method"
          class="min-w-[120px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.genMethodOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 상태 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">상태</label>
        <select
          v-model="store.searchParams.status"
          class="min-w-[120px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
          <option v-for="opt in store.statusOptions" :key="opt.code" :value="opt.code">
            {{ opt.code_name }}
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

    <!-- 문제 목록(JSON → 화면) — 추후 연동 -->
    <div class="mt-4 flex min-h-0 flex-1 flex-col overflow-hidden rounded border border-gray-300">
      <div
        class="flex shrink-0 items-center justify-between border-b border-gray-300 bg-gray-50 px-4 py-2"
      >
        <div>
          <span class="text-sm font-medium text-gray-700">문제 목록</span>
          <span class="ml-2 text-xs text-gray-400"
            >※ 상단 테이블에서 행을 선택하면 하단에 문제가 표시됩니다</span
          >
        </div>
      </div>
      <div class="flex-1 overflow-y-auto">
        <div class="flex h-40 items-center justify-center text-gray-400">
          문제 데이터가 없습니다.
        </div>
      </div>
    </div>

    <!-- 등록/수정 모달 -->
    <PracticeRequestFormModal
      :visible="showModal"
      :edit-data="editData"
      @close="handleModalClose"
      @saved="handleModalSaved"
    />
  </div>
</template>
