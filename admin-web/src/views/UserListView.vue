<!--
  사용자 관리 페이지 (조회 전용)
  - 좌측(4): 사용자 목록 (검색바 + 테이블 + 페이지네이션)
  - 우측(6): 사용자 이력 (추후 구현 예정, 현재 비어 있음)
  - 하나의 box로 감싸서 통일성 있게 구성
  - 브라우저 높이에 꽉 차는 레이아웃
-->
<script setup>
import { onMounted } from 'vue';
import { useUserStore } from '@/stores/user';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';

const store = useUserStore();

/* ========== 테이블 컬럼 정의 (생성시간 컬럼 제외) ========== */
const columns = [
  { key: 'user_key', label: '사용자키', width: '80px' },
  { key: 'email', label: '이메일', width: '200px', align: 'left' },
  { key: 'provider_type', label: '인증유형', width: '120px' },
  { key: 'del_yn', label: '삭제여부', width: '80px' }
];

/** 조회 버튼 클릭 */
function handleSearch() {
  store.page = 1;
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
  store.fetchList();
});
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 서브 타이틀 -->
    <h2 class="mb-4 shrink-0 text-xl font-bold text-gray-800">사용자 관리</h2>

    <!-- 좌우 2분할 박스 — 높이 꽉 채움 -->
    <div class="flex min-h-0 flex-1 gap-0 overflow-hidden rounded-lg border border-gray-300">
      <!-- 좌측: 사용자 목록 (4) -->
      <div class="flex w-2/5 flex-col overflow-hidden border-r border-gray-300">
        <!-- 섹션 헤더 -->
        <div class="shrink-0 border-b border-gray-300 bg-gray-50 px-4 py-3">
          <h3 class="text-sm font-semibold text-gray-500">사용자 목록</h3>
        </div>

        <!-- 컨텐츠 영역 — 스크롤 가능 -->
        <div class="flex-1 overflow-y-auto p-4">
          <!-- 검색바 (등록 버튼 없음) -->
          <SearchBar :hide-register="true" @search="handleSearch">
            <div class="flex items-center gap-2">
              <label class="whitespace-nowrap text-sm font-medium text-gray-700"> 이메일 </label>
              <input
                v-model="store.searchParams.email"
                type="text"
                class="min-w-[140px] rounded border border-gray-300 px-3 py-1.5 text-sm"
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
            @update:page-size="handlePageSizeChange"
          />

          <!-- 페이지네이션 -->
          <Pagination
            :page="store.page"
            :size="store.size"
            :total="store.total"
            @update:page="handlePageChange"
          />
        </div>
      </div>

      <!-- 우측: 사용자 이력 (6) -->
      <div class="flex w-3/5 flex-col overflow-hidden">
        <!-- 섹션 헤더 -->
        <div class="shrink-0 border-b border-gray-300 bg-gray-50 px-4 py-3">
          <h3 class="text-sm font-semibold text-gray-500">사용자 이력</h3>
        </div>

        <!-- 컨텐츠 영역 — 추후 구현 예정 -->
        <div class="flex flex-1 items-center justify-center overflow-y-auto p-4 text-gray-300">
          <!-- 추후 구현 예정 -->
        </div>
      </div>
    </div>
  </div>
</template>
