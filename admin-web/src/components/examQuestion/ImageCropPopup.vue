<!--
  이미지 크롭 팝업 컴포넌트
  - 기출문항 관리에서 '이미지 생성' 버튼 클릭 시 모달로 표시
  - 상단: 이미지 타입 버튼 5개 + 스크롤/크롭 모드 토글
  - 본문: PDF 뷰어 + crop 오버레이 (크롭 모드일 때만)
  - 모드 전환: 스크롤 모드(기본) — PDF 스크롤/확대 가능, 크롭 모드 — 드래그로 영역 선택
-->
<script setup>
import { ref, computed, watch } from 'vue';
import { getInlineViewUrl } from '@/api/examFile';

const props = defineProps({
  /** 팝업 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 시험키 */
  examKey: {
    type: Number,
    default: null
  },
  /** PDF 파일키 */
  pdfKey: {
    type: Number,
    default: null
  },
  /** 문항 정보 (question_no 등) */
  item: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close']);

/** 현재 선택된 이미지 타입 버튼 */
const selectedImageType = ref('question');

/** 이미지 타입 버튼 목록 */
const imageTypeButtons = [
  { key: 'question', label: '문항이미지' },
  { key: 'choice1', label: '1번이미지' },
  { key: 'choice2', label: '2번이미지' },
  { key: 'choice3', label: '3번이미지' },
  { key: 'choice4', label: '4번이미지' }
];

/** 모드: 'scroll' (PDF 스크롤/확대) | 'crop' (영역 선택) */
const mode = ref('scroll');

/** PDF 인라인 뷰어 URL */
const pdfUrl = computed(() => {
  if (props.examKey && props.pdfKey) {
    return getInlineViewUrl(props.examKey, props.pdfKey);
  }
  return '';
});

/** 문항 번호 표시 */
const questionLabel = computed(() => {
  if (!props.item) return '';
  return `${props.item.question_no}번`;
});

/* ========== crop 영역 드래그 (크롭 모드에서만 동작) ========== */

/** crop 오버레이 컨테이너 ref */
const cropContainer = ref(null);

/** 드래그 상태 */
const isDragging = ref(false);

/** 드래그 시작 좌표 */
const dragStart = ref({ x: 0, y: 0 });

/** 현재 crop 영역 (CSS용) */
const cropRect = ref({ left: 0, top: 0, width: 0, height: 0 });

/** crop 영역이 설정되었는지 여부 */
const hasCropArea = computed(() => cropRect.value.width > 5 && cropRect.value.height > 5);

/** 마우스 다운 — crop 드래그 시작 */
function handleMouseDown(e) {
  if (mode.value !== 'crop' || !cropContainer.value) return;
  const rect = cropContainer.value.getBoundingClientRect();
  isDragging.value = true;
  dragStart.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  };
  cropRect.value = {
    left: dragStart.value.x,
    top: dragStart.value.y,
    width: 0,
    height: 0
  };
}

/** 마우스 이동 — crop 영역 업데이트 */
function handleMouseMove(e) {
  if (!isDragging.value || !cropContainer.value) return;
  const rect = cropContainer.value.getBoundingClientRect();
  const currentX = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
  const currentY = Math.max(0, Math.min(e.clientY - rect.top, rect.height));

  cropRect.value = {
    left: Math.min(dragStart.value.x, currentX),
    top: Math.min(dragStart.value.y, currentY),
    width: Math.abs(currentX - dragStart.value.x),
    height: Math.abs(currentY - dragStart.value.y)
  };
}

/** 마우스 업 — crop 드래그 종료 */
function handleMouseUp() {
  isDragging.value = false;
}

/** crop 영역 CSS 스타일 */
const cropStyle = computed(() => ({
  left: cropRect.value.left + 'px',
  top: cropRect.value.top + 'px',
  width: cropRect.value.width + 'px',
  height: cropRect.value.height + 'px'
}));

/** crop 영역 초기화 */
function clearCrop() {
  cropRect.value = { left: 0, top: 0, width: 0, height: 0 };
}

/** 팝업 열릴 때 초기화 */
watch(
  () => props.visible,
  (val) => {
    if (val) {
      selectedImageType.value = 'question';
      mode.value = 'scroll';
      clearCrop();
      isDragging.value = false;
    }
  }
);
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="mx-4 flex h-[85vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-xl">
        <!-- 헤더 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <div>
            <h3 class="text-sm font-bold text-gray-800">이미지 생성</h3>
            <p class="mt-0.5 text-xs text-gray-500">{{ questionLabel }}</p>
          </div>
          <button
            class="flex h-7 w-7 items-center justify-center rounded text-gray-400 hover:bg-gray-100 hover:text-gray-600"
            @click="emit('close')"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- 이미지 타입 버튼 + 모드 토글 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-2">
          <!-- 이미지 타입 버튼 5개 -->
          <div class="flex items-center gap-2">
            <button
              v-for="btn in imageTypeButtons"
              :key="btn.key"
              class="btn btn-xs"
              :class="selectedImageType === btn.key ? 'btn-primary' : 'btn-secondary'"
              @click="selectedImageType = btn.key"
            >
              {{ btn.label }}
            </button>
          </div>

          <!-- 모드 토글: 스크롤 / 크롭 -->
          <div class="flex items-center gap-1 rounded-md border border-gray-300 bg-gray-50 p-0.5">
            <!-- 스크롤 모드 -->
            <button
              class="flex items-center gap-1 rounded px-2.5 py-1 text-xs transition-colors"
              :class="mode === 'scroll' ? 'bg-white font-medium text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
              @click="mode = 'scroll'"
            >
              <!-- 손바닥(pan) 아이콘 -->
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.05 4.575a1.575 1.575 0 10-3.15 0v3m3.15-3v-1.5a1.575 1.575 0 013.15 0v1.5m-3.15 0l.075 5.925m3.075-5.925v2.925m0-2.925a1.575 1.575 0 013.15 0V8.25m-3.15-2.175a1.575 1.575 0 013.15 0v5.4m-3.15-5.4v5.4m0 0v.9A6.075 6.075 0 016.9 20.55h-.45A6.075 6.075 0 010 14.475V8.25" />
              </svg>
              스크롤
            </button>
            <!-- 크롭 모드 -->
            <button
              class="flex items-center gap-1 rounded px-2.5 py-1 text-xs transition-colors"
              :class="mode === 'crop' ? 'bg-white font-medium text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
              @click="mode = 'crop'"
            >
              <!-- 크롭(가위) 아이콘 -->
              <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M7.848 8.25l1.536.887M7.848 8.25a3 3 0 11-5.196-3 3 3 0 015.196 3zm1.536.887a2.165 2.165 0 011.083-.313h5.533m-6.616.626L15 15.375m-6.616-6.238l-3.232 5.6a2.165 2.165 0 00.313 2.51l.052.052a2.165 2.165 0 002.51.313l5.6-3.232m0 0L15 15.375m0 0l3.232 5.6a2.165 2.165 0 002.51.313l.052-.052a2.165 2.165 0 00.313-2.51l-3.232-5.6" />
              </svg>
              크롭
            </button>
            <!-- crop 초기화 -->
            <button
              v-if="hasCropArea"
              class="rounded px-2 py-1 text-xs text-red-400 hover:bg-red-50 hover:text-red-600"
              title="선택 영역 초기화"
              @click="clearCrop"
            >
              초기화
            </button>
          </div>
        </div>

        <!-- PDF 뷰어 + crop 오버레이 -->
        <div class="relative min-h-0 flex-1 overflow-hidden">
          <!-- PDF iframe -->
          <iframe
            v-if="pdfUrl"
            :src="pdfUrl"
            class="h-full w-full border-0"
          ></iframe>
          <div v-else class="flex h-full items-center justify-center text-gray-400">
            PDF 파일 없음
          </div>

          <!-- crop 오버레이 — 크롭 모드에서만 표시 -->
          <div
            v-if="mode === 'crop'"
            ref="cropContainer"
            class="absolute inset-0 cursor-crosshair"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @mouseleave="handleMouseUp"
          >
            <!-- crop 선택 영역 표시 -->
            <div
              v-if="hasCropArea"
              class="absolute border-2 border-dashed border-blue-500 bg-blue-100/30"
              :style="cropStyle"
            >
              <span class="absolute -top-5 left-0 rounded bg-blue-500 px-1.5 py-0.5 text-[10px] text-white">
                {{ Math.round(cropRect.width) }} x {{ Math.round(cropRect.height) }}
              </span>
            </div>
          </div>

          <!-- 스크롤 모드일 때 crop 영역만 표시 (투명 오버레이 없이) -->
          <div
            v-if="mode === 'scroll' && hasCropArea"
            class="pointer-events-none absolute inset-0"
          >
            <div
              class="absolute border-2 border-dashed border-blue-500 bg-blue-100/20"
              :style="cropStyle"
            >
              <span class="absolute -top-5 left-0 rounded bg-blue-500 px-1.5 py-0.5 text-[10px] text-white">
                {{ Math.round(cropRect.width) }} x {{ Math.round(cropRect.height) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
