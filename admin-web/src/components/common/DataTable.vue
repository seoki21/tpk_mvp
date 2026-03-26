<!--
  공통 데이터 테이블 컴포넌트
  - columns 배열로 컬럼 정의 (key, label, width, align, sortable)
  - data 배열로 행 데이터를 표시
  - 컬럼 헤더 클릭 시 오름차순/내림차순 정렬 (클라이언트 사이드)
  - 로딩 상태 및 빈 데이터 처리 포함
  - 행 클릭 시 row-click 이벤트를 emit 한다.
  - 테이블 상단: 좌측 조회목록(총 N건), 우측 페이지당 행 수 selectbox
-->
<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  /** 컬럼 정의 배열 — { key: string, label: string, width?: string, align?: string, sortable?: boolean } */
  columns: {
    type: Array,
    required: true
  },
  /** 테이블에 표시할 데이터 배열 */
  data: {
    type: Array,
    default: () => []
  },
  /** 로딩 상태 여부 */
  loading: {
    type: Boolean,
    default: false
  },
  /** 페이지당 행 수 (selectbox 표시용, 미지정 시 selectbox 숨김) */
  pageSize: {
    type: Number,
    default: 0
  },
  /** 전체 건수 (조회목록 헤더 표시용) */
  total: {
    type: Number,
    default: -1
  }
});

const emit = defineEmits(['row-click', 'update:pageSize']);

/** 페이지당 행 수 선택 옵션 */
const pageSizeOptions = [10, 20, 50];

/** 페이지 크기 변경 핸들러 */
function handlePageSizeChange(event) {
  emit('update:pageSize', Number(event.target.value));
}

/* ========== 컬럼 클릭 정렬 ========== */

/** 현재 정렬 기준 컬럼 키 */
const sortKey = ref(null);

/** 현재 정렬 방향 ('asc' | 'desc') */
const sortOrder = ref('asc');

/** 데이터가 변경되면(새 조회 시) 클라이언트 정렬을 초기화하여 서버 정렬 순서를 유지 */
watch(
  () => props.data,
  () => {
    sortKey.value = null;
    sortOrder.value = 'asc';
  }
);

/**
 * 컬럼 헤더 클릭 시 정렬 토글
 * - 같은 컬럼 클릭: asc → desc → 정렬 해제(null)
 * - 다른 컬럼 클릭: asc로 시작
 */
function handleSort(col) {
  /* sortable이 명시적으로 false인 컬럼은 정렬 불가 */
  if (col.sortable === false) return;

  if (sortKey.value === col.key) {
    if (sortOrder.value === 'asc') {
      sortOrder.value = 'desc';
    } else {
      /* 정렬 해제 */
      sortKey.value = null;
      sortOrder.value = 'asc';
    }
  } else {
    sortKey.value = col.key;
    sortOrder.value = 'asc';
  }
}

/**
 * 정렬된 데이터 — sortKey가 있으면 해당 컬럼 기준 정렬, 없으면 원본 순서
 */
const sortedData = computed(() => {
  if (!sortKey.value || props.data.length === 0) return props.data;

  const key = sortKey.value;
  const order = sortOrder.value === 'asc' ? 1 : -1;

  return [...props.data].sort((a, b) => {
    const valA = a[key] ?? '';
    const valB = b[key] ?? '';

    /* 숫자 비교 */
    if (typeof valA === 'number' && typeof valB === 'number') {
      return (valA - valB) * order;
    }

    /* 문자열 비교 (한글 포함 로케일 정렬) */
    return String(valA).localeCompare(String(valB), 'ko') * order;
  });
});

/**
 * 정렬 아이콘 반환 — 현재 정렬 중인 컬럼에 ▲ 또는 ▼ 표시
 */
function getSortIcon(colKey) {
  if (sortKey.value !== colKey) return '';
  return sortOrder.value === 'asc' ? ' ▲' : ' ▼';
}
</script>

<template>
  <div class="overflow-x-auto rounded border border-gray-300">
    <!-- 테이블 상단: 좌측 조회목록(총 N건) / 우측 페이지당 행 수 선택 -->
    <div
      v-if="pageSize > 0 || total >= 0"
      class="flex items-center justify-between border-b border-gray-300 bg-gray-50 px-4 py-2"
    >
      <!-- 좌측: 조회목록(총 N건) -->
      <span v-if="total >= 0" class="text-sm font-medium text-gray-700">
        조회목록(총 {{ total }}건)
      </span>
      <span v-else></span>

      <!-- 우측: 페이지당 행 수 선택 -->
      <select
        v-if="pageSize > 0"
        :value="pageSize"
        class="rounded border border-gray-300 px-2 py-1 text-sm"
        @change="handlePageSizeChange"
      >
        <option v-for="opt in pageSizeOptions" :key="opt" :value="opt">{{ opt }}개씩 보기</option>
      </select>
    </div>

    <table class="w-full text-left text-sm">
      <!-- 테이블 헤더 — 클릭 시 정렬 -->
      <thead class="border-b border-gray-300 bg-gray-100">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            class="select-none px-4 py-2 font-medium text-gray-700"
            :class="[
              col.align === 'left'
                ? 'text-left'
                : col.align === 'right'
                  ? 'text-right'
                  : 'text-center',
              col.sortable !== false ? 'cursor-pointer hover:bg-gray-200' : ''
            ]"
            :style="col.width ? { width: col.width } : {}"
            @click="handleSort(col)"
          >
            {{ col.label }}{{ getSortIcon(col.key) }}
          </th>
        </tr>
      </thead>

      <!-- 테이블 바디 -->
      <tbody>
        <!-- 로딩 상태 -->
        <tr v-if="loading">
          <td :colspan="columns.length" class="px-4 py-8 text-center text-gray-500">로딩 중...</td>
        </tr>

        <!-- 데이터 없음 -->
        <tr v-else-if="data.length === 0">
          <td :colspan="columns.length" class="px-4 py-8 text-center text-gray-500">
            데이터가 없습니다
          </td>
        </tr>

        <!-- 데이터 행 — sortedData 사용 -->
        <tr
          v-for="(row, index) in sortedData"
          v-else
          :key="index"
          class="cursor-pointer border-b border-gray-200 hover:bg-blue-50"
          @click="emit('row-click', row)"
        >
          <td
            v-for="col in columns"
            :key="col.key"
            class="px-4 py-2"
            :class="
              col.align === 'left'
                ? 'text-left'
                : col.align === 'right'
                  ? 'text-right'
                  : 'text-center'
            "
          >
            <!-- 셀 커스텀 렌더링 슬롯 — 부모에서 #cell-{key}로 오버라이드 가능 -->
            <slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">
              <!-- 기본 렌더링: 삭제여부 컬럼은 N→공백, Y→빨간색 '삭제' -->
              <span
                v-if="col.key === 'del_yn' && row[col.key] === 'Y'"
                class="font-medium text-red-600"
                >삭제</span
              >
              <span v-else-if="col.key === 'del_yn'"></span>
              <span v-else>{{ row[col.key] }}</span>
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
