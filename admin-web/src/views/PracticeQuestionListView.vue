<!--
  연습문제 관리 목록 페이지
  - 상단: 검색바 (시험종류, 레벨, 영역, 상태 selectbox) + 조회/등록 버튼
  - 중단: 데이터 테이블 + 페이지네이션
  - 하단: 행 클릭 시 좌측(40%) JSON 텍스트 + 우측(60%) 문제 렌더링
  - ※ 현재 UI 껍데기만 구현 (API 미연동, 데이터 없음)
-->
<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';
import { useToast } from '@/composables/useToast';

const router = useRouter();
const toast = useToast();

/* ========== 검색 조건 ========== */
const searchParams = ref({
  exam_type: '',
  tpk_level: '',
  section: '',
  status: ''
});

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'status', label: '상태', width: '100px' },
  { key: 'ins_date', label: '생성 요청일시', width: '180px' },
  { key: 'exam_type_name', label: '시험종류', width: '140px', align: 'left' },
  { key: 'tpk_level_name', label: '레벨', width: '120px', align: 'left' },
  { key: 'section_name', label: '영역', width: '140px', align: 'left' }
];

/* ========== 목록 상태 (빈 데이터) ========== */
const list = ref([]);
const total = ref(0);
const page = ref(1);
const size = ref(20);
const loading = ref(false);

/** 조회 버튼 — 추후 API 연동 */
function handleSearch() {
  toast.info('조회 기능은 추후 구현 예정입니다.');
}

/** 등록 버튼 → 연습문제 생성 페이지로 이동 */
function handleRegister() {
  router.push({ name: 'practiceQuestionCreate' });
}

/** 행 클릭 — 추후 하단 상세 영역에 표시 */
function handleRowClick(_row) {
  /* 추후 데이터 연동 시 구현 */
}

/** 페이지 변경 — 추후 API 연동 */
function handlePageChange(newPage) {
  page.value = newPage;
}

/** 페이지당 행 수 변경 — 추후 API 연동 */
function handlePageSizeChange(newSize) {
  size.value = newSize;
  page.value = 1;
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 text-xl font-bold text-gray-800">연습문제 관리</h2>

    <!-- 검색바 -->
    <SearchBar @search="handleSearch" @register="handleRegister">
      <!-- 시험종류 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">시험종류</label>
        <select
          v-model="searchParams.exam_type"
          class="min-w-[140px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
        </select>
      </div>

      <!-- 레벨 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">레벨</label>
        <select
          v-model="searchParams.tpk_level"
          class="min-w-[140px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
        </select>
      </div>

      <!-- 영역 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">영역</label>
        <select
          v-model="searchParams.section"
          class="min-w-[140px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
        </select>
      </div>

      <!-- 상태 -->
      <div class="flex items-center gap-2">
        <label class="whitespace-nowrap text-sm font-medium text-gray-700">상태</label>
        <select
          v-model="searchParams.status"
          class="min-w-[140px] rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value=""></option>
        </select>
      </div>
    </SearchBar>

    <!-- 데이터 테이블 -->
    <DataTable
      :columns="columns"
      :data="list"
      :loading="loading"
      :page-size="size"
      :total="total"
      @row-click="handleRowClick"
      @update:page-size="handlePageSizeChange"
    />

    <!-- 페이지네이션 -->
    <Pagination
      :page="page"
      :size="size"
      :total="total"
      @update:page="handlePageChange"
    />

    <!-- 문제 목록(JSON → 화면) — 기출문제 관리와 동일 구조 -->
    <div class="mt-4 flex min-h-0 flex-1 flex-col overflow-hidden rounded border border-gray-300">
      <div class="flex shrink-0 items-center justify-between border-b border-gray-300 bg-gray-50 px-4 py-2">
        <div>
          <span class="text-sm font-medium text-gray-700">문제 목록</span>
          <span class="ml-2 text-xs text-gray-400">※ JSON 데이터를 수정하면 우측 화면에서 실시간으로 결과를 확인할 수 있습니다</span>
        </div>
      </div>

      <!-- 스크롤 영역 -->
      <div class="flex-1 overflow-y-auto">
        <!-- 데이터 없음 안내 -->
        <div class="flex h-40 items-center justify-center text-gray-400">
          문제 데이터가 없습니다.
        </div>

        <!--
          항목 목록 (추후 데이터 연동 시 활성화)
          기출문제 관리와 동일 패턴: divide-y → 항목별 좌측 40% JSON 편집 + 우측 60% 시험지 렌더링
          <div class="divide-y divide-gray-200">
            <div v-for="(item, index) in items" :key="index" class="flex gap-4 p-4">
              <JsonEditorPanel ... />    (좌측 40%)
              <div class="w-3/5 min-w-0">
                <ExamQuestionCard ... /> (우측 60%)
              </div>
            </div>
          </div>
        -->
      </div>
    </div>
  </div>
</template>
