<!--
  공통 데이터 테이블 컴포넌트
  - columns 배열로 컬럼 정의 (key, label, width, align, sortable)
  - data 배열로 행 데이터를 표시
  - 컬럼 헤더 클릭 시 오름차순/내림차순 정렬 (클라이언트 사이드)
  - 로딩 상태 및 빈 데이터 처리 포함
  - 행 클릭 시 row-click 이벤트를 emit 한다.
  - 테이블 상단: 좌측 조회목록(총 N건), 우측 엑셀 다운로드 아이콘 + 페이지당 행 수 selectbox
  - excelFileName prop이 지정되면 엑셀 다운로드 아이콘을 표시한다.
-->
<script setup>
import { ref, computed, watch } from 'vue';
import * as XLSX from 'xlsx-js-style';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';

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
  },
  /** 엑셀 다운로드 파일명 (지정 시 엑셀 아이콘 표시, 미지정 시 숨김) */
  excelFileName: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['row-click', 'update:pageSize', 'excel-download']);

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

/* ========== 엑셀 다운로드 ========== */

/** 엑셀 다운로드 확인 다이얼로그 표시 여부 */
const showExcelConfirm = ref(false);

/** 얇은 테두리 스타일 (셀 공통) */
const thinBorder = {
  top: { style: 'thin', color: { rgb: 'D0D0D0' } },
  bottom: { style: 'thin', color: { rgb: 'D0D0D0' } },
  left: { style: 'thin', color: { rgb: 'D0D0D0' } },
  right: { style: 'thin', color: { rgb: 'D0D0D0' } }
};

/** 헤더 셀 스타일 — 진한 파랑 배경 + 흰색 볼드 텍스트 + 가운데 정렬 */
const headerStyle = {
  font: { bold: true, color: { rgb: 'FFFFFF' }, sz: 10 },
  fill: { fgColor: { rgb: '4472C4' } },
  alignment: { horizontal: 'center', vertical: 'center' },
  border: thinBorder
};

/**
 * 컬럼 정렬 방향에 맞는 데이터 셀 스타일 반환
 * - 짝수/홀수 행 교차 배경색으로 가독성 향상
 */
function getDataStyle(col, rowIdx) {
  const isEven = rowIdx % 2 === 0;
  return {
    font: { sz: 10, color: { rgb: '333333' } },
    fill: { fgColor: { rgb: isEven ? 'FFFFFF' : 'F2F6FC' } },
    alignment: {
      horizontal: col.align === 'left' ? 'left' : col.align === 'right' ? 'right' : 'center',
      vertical: 'center'
    },
    border: thinBorder
  };
}

/**
 * 확인 다이얼로그에서 '확인' 클릭 시 호출
 * - excel-download 이벤트 리스너가 있으면 부모에게 위임 (부모가 전체 데이터를 조회하여 generateExcel 호출)
 * - 리스너가 없으면 현재 페이지 데이터(sortedData)로 즉시 엑셀 생성
 */
function handleExcelConfirm() {
  showExcelConfirm.value = false;
  emit('excel-download');
}

/**
 * 엑셀 파일 생성 및 다운로드 (외부에서 호출 가능)
 * - 전달받은 데이터 배열을 엑셀로 변환하여 다운로드
 * - excelData가 없으면 현재 테이블의 sortedData를 사용 (폴백)
 * - del_yn 컬럼은 화면 표시와 동일하게 변환 (Y→삭제, N→공백)
 * - 스타일: 헤더(파랑 배경+흰색 볼드), 홀짝 행 교차 배경, 얇은 테두리, 컬럼 너비 자동 맞춤
 * @param {Array} excelData - 엑셀로 내보낼 데이터 배열 (미전달 시 현재 페이지 데이터 사용)
 */
function generateExcel(excelData) {
  const sourceData = excelData || sortedData.value;

  /* 헤더 행 생성 */
  const headers = props.columns.map((col) => col.label);

  /* 데이터 행 생성 — 화면에 표시되는 값과 동일하게 변환 */
  const rows = sourceData.map((row) =>
    props.columns.map((col) => {
      const val = row[col.key];
      if (col.key === 'del_yn') return val === 'Y' ? '삭제' : '';
      return val ?? '';
    })
  );

  /* 워크시트 생성 */
  const wsData = [headers, ...rows];
  const ws = XLSX.utils.aoa_to_sheet(wsData);

  /* 헤더 행 스타일 적용 */
  props.columns.forEach((_col, i) => {
    const cellRef = XLSX.utils.encode_cell({ r: 0, c: i });
    if (ws[cellRef]) ws[cellRef].s = headerStyle;
  });

  /* 데이터 행 스타일 적용 */
  rows.forEach((row, rowIdx) => {
    row.forEach((_val, colIdx) => {
      const cellRef = XLSX.utils.encode_cell({ r: rowIdx + 1, c: colIdx });
      if (ws[cellRef]) ws[cellRef].s = getDataStyle(props.columns[colIdx], rowIdx);
    });
  });

  /* 행 높이 설정 — 헤더 약간 높게 */
  ws['!rows'] = [{ hpx: 28 }, ...rows.map(() => ({ hpx: 22 }))];

  /* 컬럼 너비 자동 맞춤 — 헤더와 데이터 중 최대 길이 기준 */
  ws['!cols'] = props.columns.map((col, i) => {
    let maxLen = col.label.length;
    rows.forEach((row) => {
      const cellLen = String(row[i]).length;
      if (cellLen > maxLen) maxLen = cellLen;
    });
    /* 한글은 2바이트 폭 고려, 최소 10, 최대 40 */
    const width = Math.min(Math.max(maxLen * 2 + 2, 10), 40);
    return { wch: width };
  });

  /* 워크북 생성 및 다운로드 */
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, '데이터');

  /* 파일명: {excelFileName}_{YYYYMMDD}.xlsx */
  const today = new Date();
  const dateStr =
    today.getFullYear() +
    String(today.getMonth() + 1).padStart(2, '0') +
    String(today.getDate()).padStart(2, '0');
  const fileName = `${props.excelFileName}_${dateStr}.xlsx`;

  XLSX.writeFile(wb, fileName);
}

/** 부모 컴포넌트에서 ref로 호출할 수 있도록 generateExcel을 노출 */
defineExpose({ generateExcel });
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

      <!-- 우측: 엑셀 다운로드 아이콘 + 페이지당 행 수 선택 -->
      <div class="flex items-center gap-2">
        <!-- 엑셀 다운로드 아이콘 버튼 -->
        <button
          v-if="excelFileName"
          title="엑셀 다운로드"
          class="flex h-7 items-center gap-1 rounded border border-green-300 bg-white px-1.5 text-green-700 hover:bg-green-50"
          @click="showExcelConfirm = true"
        >
          <!-- 스프레드시트 아이콘 (가로로 살짝 넓은 형태) -->
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-5">
            <path fill-rule="evenodd" d="M1 3.5A1.5 1.5 0 0 1 2.5 2h15A1.5 1.5 0 0 1 19 3.5v13a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 1 16.5v-13ZM3 5v2h4V5H3Zm6 0v2h4V5H9Zm6 0v2h2V5h-2ZM3 9v2h4V9H3Zm6 0v2h4V9H9Zm6 0v2h2V9h-2ZM3 13v2h4v-2H3Zm6 0v2h4v-2H9Zm6 0v2h2v-2h-2Z" clip-rule="evenodd" />
          </svg>
          <span class="text-xs font-medium">XLS</span>
        </button>

        <select
          v-if="pageSize > 0"
          :value="pageSize"
          class="rounded border border-gray-300 px-2 py-1 text-sm"
          @change="handlePageSizeChange"
        >
          <option v-for="opt in pageSizeOptions" :key="opt" :value="opt">{{ opt }}개씩 보기</option>
        </select>
      </div>
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

    <!-- 엑셀 다운로드 확인 다이얼로그 -->
    <ConfirmDialog
      :visible="showExcelConfirm"
      message="엑셀파일을 생성하시겠습니까?"
      @confirm="handleExcelConfirm"
      @cancel="showExcelConfirm = false"
    />
  </div>
</template>
