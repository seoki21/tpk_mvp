<!--
  파일 목록 팝업 메뉴 컴포넌트
  - 테이블의 FILE 컬럼 'Y' 클릭 시 해당 위치에 파일 목록을 팝업으로 표시
  - 파일 선택 시 select 이벤트를 emit하여 PDF 뷰어에 연동
  - 바깥 영역 클릭 시 자동 닫힘
-->
<script setup>
import { ref, watch, onBeforeUnmount } from 'vue';

const props = defineProps({
  /** 팝업 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 파일 목록 배열 [{ pdf_key, file_name, file_size, ... }] */
  files: {
    type: Array,
    default: () => []
  },
  /** 앵커 요소의 위치 정보 (getBoundingClientRect 결과) */
  anchorRect: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['select', 'close']);

/** 팝업 메뉴 DOM ref */
const menuRef = ref(null);

/** 바깥 클릭 감지 핸들러 */
function onDocumentClick(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    emit('close');
  }
}

/** visible 변경 시 document click 리스너 등록/해제 */
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      /* 현재 이벤트 루프가 끝난 후 리스너 등록 (클릭 이벤트 전파 방지) */
      setTimeout(() => {
        document.addEventListener('click', onDocumentClick);
      }, 0);
    } else {
      document.removeEventListener('click', onDocumentClick);
    }
  }
);

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick);
});

/** 파일 선택 핸들러 */
function handleSelect(file) {
  emit('select', file);
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible && anchorRect"
      ref="menuRef"
      class="fixed z-[70] min-w-[200px] max-w-[360px] rounded-lg border border-gray-300 bg-white py-1 shadow-lg"
      :style="{
        top: anchorRect.bottom + 4 + 'px',
        left: anchorRect.left + 'px'
      }"
    >
      <!-- 파일 목록 -->
      <div v-if="files.length > 0">
        <button
          v-for="file in files"
          :key="file.pdf_key"
          class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-gray-700 hover:bg-blue-50"
          @click="handleSelect(file)"
        >
          <span class="shrink-0 text-xs text-red-500">PDF</span>
          <span class="truncate">{{ file.file_name }}</span>
        </button>
      </div>

      <!-- 파일 없음 -->
      <div v-else class="px-3 py-2 text-sm text-gray-400">파일이 없습니다</div>
    </div>
  </Teleport>
</template>
