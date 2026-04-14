<!--
  수동 이미지 생성 팝업 컴포넌트 (다중 문항 지원)
  - PDF 페이지를 이미지(PNG)로 렌더링하여 표시
  - 상단 문항 선택 탭으로 여러 문항을 전환하며 작업
  - 이미지 타입(문항이미지/선택지1~4) 별로 독립적인 crop 영역 관리
  - cropDataMap 키: "{문항번호}_{이미지타입}" (예: "15_question", "15_choice1")
  - 페이지 네비게이션(이전/다음/직접입력)
  - "적용" 버튼으로 모든 문항의 crop 데이터를 부모에게 전달
-->
<script setup>
import { ref, reactive, computed, watch } from 'vue';
import { fetchPdfPageImage, getPdfPageCount } from '@/api/examQuestion';

const props = defineProps({
  /** 팝업 표시 여부 */
  visible: { type: Boolean, required: true },
  /** 시험키 PK */
  examKey: { type: Number, default: null },
  /** PDF 파일키 PK */
  pdfKey: { type: Number, default: null },
  /** 이미지가 필요한 문항 목록 (composable에서 전달) */
  imageItems: { type: Array, default: () => [] }
});

const emit = defineEmits(['close', 'apply']);

/* ========== 문항 선택 탭 ========== */

/** 현재 선택된 문항 인덱스 */
const selectedItemIdx = ref(0);

/** 현재 선택된 문항 정보 */
const selectedItem = computed(() => props.imageItems[selectedItemIdx.value] || null);

/** 현재 선택된 문항 번호 */
const selectedNo = computed(() => selectedItem.value?.no || 0);

/** 현재 문항에 필요한 이미지 타입 버튼 목록 (동적 생성) */
const activeImageTypeButtons = computed(() => {
  const item = selectedItem.value;
  if (!item) return [];
  const buttons = [];
  if (item.hasQuestionImg) {
    buttons.push({ key: 'question', label: '문항이미지' });
  }
  if (item.hasChoicesImg) {
    const choiceCount = item.parsed?.choices?.length || 4;
    for (let i = 1; i <= choiceCount; i++) {
      buttons.push({ key: `choice${i}`, label: `${i}번이미지` });
    }
  }
  return buttons;
});

/* ========== 이미지 타입 선택 ========== */
const selectedImageType = ref('question');

/* ========== 모드: 스크롤 / 크롭 ========== */
const mode = ref('crop');

/* ========== 페이지 네비게이션 ========== */
const currentPage = ref(1);
const totalPages = ref(0);
const pageLoading = ref(false);
const pageImageUrl = ref('');

/* ========== crop 영역 (문항번호_이미지타입별 독립 관리) ========== */
/** 키: "{no}_{imageType}" → { page, left, top, width, height } */
const cropDataMap = reactive({});

/** cropDataMap 키 생성 헬퍼 */
function cropKey(no, imageType) {
  return `${no}_${imageType}`;
}

/** 현재 선택된 문항+이미지타입의 cropDataMap 키 */
const currentCropKey = computed(() => cropKey(selectedNo.value, selectedImageType.value));

/** 현재 드래그 중인 crop rect (화면 표시용) */
const cropRect = ref({ left: 0, top: 0, width: 0, height: 0 });
const isDragging = ref(false);
const dragStart = ref({ x: 0, y: 0 });

/** crop 오버레이 + 이미지 wrapper ref */
const imageWrapperRef = ref(null);
/** 실제 <img> 요소 ref — naturalWidth 계산용 */
const imgRef = ref(null);

/** crop 영역이 유효한지 (5px 이상) */
const hasCropArea = computed(() => cropRect.value.width > 5 && cropRect.value.height > 5);

/** 정의된 crop 총 개수 (적용 버튼 활성화 조건) */
const definedCropCount = computed(() => Object.keys(cropDataMap).length);

/* ========== 페이지 이미지 로드 ========== */

async function loadPageImage() {
  if (!props.examKey || !props.pdfKey || !currentPage.value) return;
  pageLoading.value = true;

  if (pageImageUrl.value) {
    URL.revokeObjectURL(pageImageUrl.value);
    pageImageUrl.value = '';
  }

  try {
    const blob = await fetchPdfPageImage(props.examKey, props.pdfKey, currentPage.value, 150);
    pageImageUrl.value = URL.createObjectURL(new Blob([blob], { type: 'image/png' }));
  } catch (err) {
    console.error('[ImageCropPopup] 페이지 이미지 로드 실패:', err);
    pageImageUrl.value = '';
  } finally {
    pageLoading.value = false;
  }
}

async function initPopup() {
  selectedItemIdx.value = 0;
  currentPage.value = 1;
  totalPages.value = 0;
  mode.value = 'crop';
  clearAllCrops();
  cropRect.value = { left: 0, top: 0, width: 0, height: 0 };

  // 첫 문항의 첫 이미지 타입 선택
  if (activeImageTypeButtons.value.length > 0) {
    selectedImageType.value = activeImageTypeButtons.value[0].key;
  } else {
    selectedImageType.value = 'question';
  }

  if (!props.examKey || !props.pdfKey) return;

  try {
    const res = await getPdfPageCount(props.examKey, props.pdfKey);
    totalPages.value = res.data?.page_count || 0;
  } catch (err) {
    console.error('[ImageCropPopup] 페이지 수 조회 실패:', err);
  }

  if (totalPages.value > 0) {
    await loadPageImage();
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    loadPageImage();
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    loadPageImage();
  }
}

function onPageInput(e) {
  const val = parseInt(e.target.value, 10);
  if (val >= 1 && val <= totalPages.value) {
    currentPage.value = val;
    loadPageImage();
  }
}

/* ========== 문항 탭 전환 ========== */

function selectItemTab(idx) {
  selectedItemIdx.value = idx;
  // 해당 문항의 첫 이미지타입 선택
  if (activeImageTypeButtons.value.length > 0) {
    selectedImageType.value = activeImageTypeButtons.value[0].key;
    restoreCropForCurrentKey();
  }
}

/* ========== crop 드래그 로직 ========== */

function handleMouseDown(e) {
  if (mode.value !== 'crop' || !imageWrapperRef.value) return;
  const rect = imageWrapperRef.value.getBoundingClientRect();
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

function handleMouseMove(e) {
  if (!isDragging.value || !imageWrapperRef.value) return;
  const rect = imageWrapperRef.value.getBoundingClientRect();
  const currentX = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
  const currentY = Math.max(0, Math.min(e.clientY - rect.top, rect.height));

  cropRect.value = {
    left: Math.min(dragStart.value.x, currentX),
    top: Math.min(dragStart.value.y, currentY),
    width: Math.abs(currentX - dragStart.value.x),
    height: Math.abs(currentY - dragStart.value.y)
  };
}

function handleMouseUp() {
  if (!isDragging.value) return;
  isDragging.value = false;

  // 유효한 crop 영역이면 현재 문항+이미지타입에 저장
  if (hasCropArea.value) {
    cropDataMap[currentCropKey.value] = {
      no: selectedNo.value,
      imageType: selectedImageType.value,
      page: currentPage.value,
      left: cropRect.value.left,
      top: cropRect.value.top,
      width: cropRect.value.width,
      height: cropRect.value.height
    };
  }
}

/** crop 영역 CSS 스타일 */
const cropStyle = computed(() => ({
  left: cropRect.value.left + 'px',
  top: cropRect.value.top + 'px',
  width: cropRect.value.width + 'px',
  height: cropRect.value.height + 'px'
}));

/** 현재 키의 저장된 crop 복원 */
function restoreCropForCurrentKey() {
  const saved = cropDataMap[currentCropKey.value];
  if (saved) {
    cropRect.value = {
      left: saved.left,
      top: saved.top,
      width: saved.width,
      height: saved.height
    };
    if (saved.page !== currentPage.value) {
      currentPage.value = saved.page;
      loadPageImage();
    }
  } else {
    cropRect.value = { left: 0, top: 0, width: 0, height: 0 };
  }
}

/** 이미지타입 버튼 클릭 핸들러 */
function selectImageType(key) {
  selectedImageType.value = key;
  restoreCropForCurrentKey();
}

/** 현재 선택의 crop 초기화 */
function clearCurrentCrop() {
  delete cropDataMap[currentCropKey.value];
  cropRect.value = { left: 0, top: 0, width: 0, height: 0 };
}

/** 전체 crop 초기화 */
function clearAllCrops() {
  Object.keys(cropDataMap).forEach((k) => delete cropDataMap[k]);
  cropRect.value = { left: 0, top: 0, width: 0, height: 0 };
}

/** 특정 문항의 crop 완료 개수 */
function getItemCropCount(no) {
  return Object.keys(cropDataMap).filter((k) => k.startsWith(`${no}_`)).length;
}

/** 특정 문항+이미지타입의 crop 상태 텍스트 */
function getCropStatusForKey(no, imageType) {
  const saved = cropDataMap[cropKey(no, imageType)];
  if (!saved) return '미지정';
  return `p${saved.page} (${Math.round(saved.width)}x${Math.round(saved.height)})`;
}

/* ========== 적용 ========== */

function handleApply() {
  if (!imgRef.value) return;

  const displayScale = imgRef.value.naturalWidth / imgRef.value.clientWidth;
  const dpiScale = 2;
  const totalScale = displayScale * dpiScale;

  const crops = [];
  for (const [key, data] of Object.entries(cropDataMap)) {
    crops.push({
      no: data.no,
      imageType: data.imageType,
      page: data.page,
      x: Math.round(data.left * totalScale),
      y: Math.round(data.top * totalScale),
      w: Math.round(data.width * totalScale),
      h: Math.round(data.height * totalScale)
    });
  }

  emit('apply', { crops });
}

/* ========== 팝업 열림/닫힘 ========== */

watch(
  () => props.visible,
  (val) => {
    if (val) {
      initPopup();
    } else {
      if (pageImageUrl.value) {
        URL.revokeObjectURL(pageImageUrl.value);
        pageImageUrl.value = '';
      }
    }
  }
);
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-y-0 right-0 z-50 flex items-center justify-center overflow-auto bg-black/50" style="left: var(--sidebar-w, 224px); min-width: calc(1200px - var(--sidebar-w, 224px))"
      <div class="mx-4 flex h-[90vh] w-full max-w-5xl flex-col rounded-lg bg-white shadow-xl">
        <!-- 헤더 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-3">
          <div>
            <h3 class="text-sm font-bold text-gray-800">수동 이미지 생성</h3>
            <p class="mt-0.5 text-xs text-gray-500">
              PDF에서 드래그하여 이미지 영역을 직접 선택합니다.
            </p>
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

        <!-- 문항 선택 탭 -->
        <div v-if="imageItems.length > 1" class="flex items-center gap-1 border-b border-gray-200 bg-gray-50 px-5 py-2">
          <span class="mr-2 text-xs font-medium text-gray-500">문항:</span>
          <button
            v-for="(imgItem, idx) in imageItems"
            :key="imgItem.no"
            class="relative rounded px-3 py-1 text-xs font-medium transition-colors"
            :class="
              selectedItemIdx === idx
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-600 ring-1 ring-gray-300 hover:bg-gray-100'
            "
            @click="selectItemTab(idx)"
          >
            {{ imgItem.no }}번
            <!-- 해당 문항의 crop 완료 개수 표시 -->
            <span
              v-if="getItemCropCount(imgItem.no) > 0"
              class="absolute -right-1.5 -top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-green-500 text-[9px] text-white ring-1 ring-white"
            >
              {{ getItemCropCount(imgItem.no) }}
            </span>
          </button>
        </div>

        <!-- 이미지 타입 버튼 + 모드 토글 + 페이지 네비게이션 -->
        <div class="flex items-center justify-between border-b border-gray-200 px-5 py-2">
          <!-- 이미지 타입 버튼 (현재 문항에 필요한 타입만 표시) -->
          <div class="flex items-center gap-1.5">
            <button
              v-for="btn in activeImageTypeButtons"
              :key="btn.key"
              class="relative rounded px-2.5 py-1 text-xs font-medium transition-colors"
              :class="
                selectedImageType === btn.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              "
              @click="selectImageType(btn.key)"
            >
              {{ btn.label }}
              <span
                v-if="cropDataMap[cropKey(selectedNo, btn.key)]"
                class="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-green-500 ring-1 ring-white"
              ></span>
            </button>
          </div>

          <!-- 페이지 네비게이션 -->
          <div class="flex items-center gap-2">
            <button
              :disabled="currentPage <= 1"
              class="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 disabled:text-gray-300"
              @click="prevPage"
            >
              ◀
            </button>
            <div class="flex items-center gap-1 text-xs text-gray-600">
              <input
                :value="currentPage"
                type="number"
                min="1"
                :max="totalPages"
                class="w-10 rounded border border-gray-300 px-1 py-0.5 text-center text-xs"
                @change="onPageInput"
              />
              <span>/ {{ totalPages }} 페이지</span>
            </div>
            <button
              :disabled="currentPage >= totalPages"
              class="rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 disabled:text-gray-300"
              @click="nextPage"
            >
              ▶
            </button>

            <div class="ml-3 flex items-center gap-1 rounded-md border border-gray-300 bg-gray-50 p-0.5">
              <button
                class="rounded px-2 py-1 text-xs transition-colors"
                :class="mode === 'scroll' ? 'bg-white font-medium text-gray-800 shadow-sm' : 'text-gray-500'"
                @click="mode = 'scroll'"
              >
                스크롤
              </button>
              <button
                class="rounded px-2 py-1 text-xs transition-colors"
                :class="mode === 'crop' ? 'bg-white font-medium text-gray-800 shadow-sm' : 'text-gray-500'"
                @click="mode = 'crop'"
              >
                크롭
              </button>
            </div>

            <button
              v-if="cropDataMap[currentCropKey]"
              class="rounded px-2 py-1 text-xs text-red-400 hover:bg-red-50 hover:text-red-600"
              @click="clearCurrentCrop"
            >
              초기화
            </button>
          </div>
        </div>

        <!-- PDF 이미지 + crop 오버레이 -->
        <div class="relative min-h-0 flex-1 overflow-auto bg-gray-100">
          <div v-if="pageLoading" class="flex h-full items-center justify-center">
            <div class="text-sm text-gray-500">페이지 로딩 중...</div>
          </div>

          <div v-else-if="!pageImageUrl" class="flex h-full items-center justify-center text-gray-400">
            PDF 파일을 선택해주세요.
          </div>

          <div
            v-else
            ref="imageWrapperRef"
            class="relative inline-block"
            :class="mode === 'crop' ? 'cursor-crosshair' : ''"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @mouseleave="handleMouseUp"
          >
            <img
              ref="imgRef"
              :src="pageImageUrl"
              class="block max-w-full"
              draggable="false"
              @dragstart.prevent
            />

            <!-- 현재 드래그 중인 crop 영역 -->
            <div
              v-if="(mode === 'crop' || mode === 'scroll') && hasCropArea"
              class="pointer-events-none absolute border-2 border-dashed border-blue-500 bg-blue-100/30"
              :style="cropStyle"
            >
              <span class="absolute -top-5 left-0 rounded bg-blue-500 px-1.5 py-0.5 text-[10px] text-white">
                {{ Math.round(cropRect.width) }} x {{ Math.round(cropRect.height) }}
              </span>
            </div>

            <!-- 다른 키의 저장된 crop 영역 (현재 페이지에 해당하는 것만, 반투명 표시) -->
            <template v-for="(data, key) in cropDataMap" :key="key">
              <div
                v-if="key !== currentCropKey && data.page === currentPage"
                class="pointer-events-none absolute border-2 border-dashed border-gray-400 bg-gray-200/20"
                :style="{
                  left: data.left + 'px',
                  top: data.top + 'px',
                  width: data.width + 'px',
                  height: data.height + 'px'
                }"
              >
                <span class="absolute -top-5 left-0 rounded bg-gray-500 px-1.5 py-0.5 text-[10px] text-white">
                  {{ data.no }}번-{{ data.imageType === 'question' ? '문항' : data.imageType.replace('choice', '') + '번' }}
                </span>
              </div>
            </template>
          </div>
        </div>

        <!-- 하단: crop 상태 요약 + 적용/취소 버튼 -->
        <div class="flex items-center justify-between border-t border-gray-200 px-5 py-3">
          <!-- crop 상태 요약 (현재 선택 문항 기준) -->
          <div class="flex flex-wrap gap-2">
            <span
              v-for="btn in activeImageTypeButtons"
              :key="btn.key"
              class="rounded px-2 py-0.5 text-xs"
              :class="cropDataMap[cropKey(selectedNo, btn.key)] ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'"
            >
              {{ btn.label }}: {{ getCropStatusForKey(selectedNo, btn.key) }}
            </span>
            <span class="ml-2 text-xs text-gray-400">
              (전체 {{ definedCropCount }}개 지정)
            </span>
          </div>

          <div class="flex items-center gap-2">
            <button
              class="rounded border border-gray-300 px-4 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
              @click="emit('close')"
            >
              취소
            </button>
            <button
              :disabled="definedCropCount === 0"
              class="rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              @click="handleApply"
            >
              적용 ({{ definedCropCount }}개)
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
