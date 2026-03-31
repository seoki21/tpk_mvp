<!--
  locale 선택 다이얼로그 컴포넌트
  - 피드백 생성 전 생성할 언어를 선택하는 팝업
  - tb_code의 group_code='locale' 데이터를 API로 조회하여 체크박스 목록 표시
  - 전체 선택/해제 체크박스 + 개별 언어 체크박스
  - 기존 피드백 상태에 따라 기본 체크 결정:
    1. ko 피드백 있음 → ko 체크/언체크 가능
    2. ko 피드백 없음 → ko 필수 체크(비활성화)
    3. 일부 locale만 피드백 있음 → 피드백 없는 locale만 체크
    4. 그 외 → 전체 체크
-->
<script setup>
import { ref, computed, watch, onMounted } from 'vue';
import { getCodesByGroup } from '@/api/code';

const props = defineProps({
  /** 다이얼로그 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 이미 피드백이 존재하는 locale 코드 목록 (예: ['ko', 'en']) */
  existingLocales: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['confirm', 'cancel']);

/** locale 목록 (API 조회 결과) */
const localeList = ref([]);

/** 선택된 locale 코드 목록 */
const selectedLocales = ref([]);

/** 로딩 상태 */
const loading = ref(false);

/** ko 피드백 존재 여부 — true면 ko도 체크/언체크 가능 */
const hasKoFeedback = computed(() => props.existingLocales.includes('ko'));

/** locale 목록 조회 */
async function fetchLocales() {
  if (localeList.value.length > 0) return;
  loading.value = true;
  try {
    const res = await getCodesByGroup('locale');
    localeList.value = res.data || [];
  } catch (error) {
    console.error('[LocaleSelectDialog] locale 목록 조회 실패:', error);
  } finally {
    loading.value = false;
  }
}

/** 전체 locale 코드 목록 (ko 포함) */
const allLocaleCodes = computed(() =>
  localeList.value.map((loc) => loc.code_name)
);

/** 체크 가능한 locale 목록 (ko 피드백 없으면 ko 제외) */
const checkableLocales = computed(() =>
  hasKoFeedback.value
    ? localeList.value
    : localeList.value.filter((loc) => loc.code_name !== 'ko')
);

/** 전체 선택 상태 — 체크 가능한 locale이 모두 선택됐는지 */
const isAllSelected = computed(() =>
  checkableLocales.value.length > 0 &&
  checkableLocales.value.every((loc) => selectedLocales.value.includes(loc.code_name))
);

/** 전체 선택 토글 */
function toggleAll() {
  if (isAllSelected.value) {
    /* 전체 해제 — ko 피드백 없으면 ko만 남김, 있으면 전부 해제 */
    selectedLocales.value = hasKoFeedback.value ? [] : ['ko'];
  } else {
    /* 전체 선택 */
    const all = checkableLocales.value.map((loc) => loc.code_name);
    selectedLocales.value = hasKoFeedback.value ? [...all] : ['ko', ...all];
  }
}

/** 개별 locale 토글 */
function toggleLocale(codeName) {
  /* ko 피드백 없으면 ko는 토글 불가 */
  if (codeName === 'ko' && !hasKoFeedback.value) return;
  const idx = selectedLocales.value.indexOf(codeName);
  if (idx === -1) {
    selectedLocales.value.push(codeName);
  } else {
    selectedLocales.value.splice(idx, 1);
  }
}

/** 확인 버튼 클릭 */
function handleConfirm() {
  emit('confirm', [...selectedLocales.value]);
}

/**
 * 기존 피드백 상태에 따라 기본 체크 상태를 결정한다.
 * - ko 피드백 없음 → ko 필수 + 나머지 전체 체크
 * - 일부 locale만 피드백 있음 → 피드백 없는 locale만 체크
 * - 전체 피드백 있음 또는 피드백 없음 → 전체 체크
 */
function initSelectedLocales() {
  if (localeList.value.length === 0) return;

  const existing = props.existingLocales;
  const allCodes = allLocaleCodes.value;

  if (existing.length === 0) {
    /* 피드백 전혀 없음 → 전체 체크 */
    selectedLocales.value = ['ko', ...allCodes.filter((c) => c !== 'ko')];
  } else {
    /* 피드백이 있는 locale과 없는 locale 분리 */
    const missing = allCodes.filter((c) => !existing.includes(c));
    if (missing.length > 0) {
      /* 일부만 피드백 있음 → 피드백 없는 locale만 체크 */
      selectedLocales.value = [...missing];
    } else {
      /* 전체 피드백 있음 → 전체 체크 (재생성) */
      selectedLocales.value = hasKoFeedback.value
        ? [...allCodes]
        : ['ko', ...allCodes.filter((c) => c !== 'ko')];
    }
  }
}

/** 다이얼로그 열릴 때 locale 목록 조회 + 기본 체크 초기화 */
watch(
  () => props.visible,
  (val) => {
    if (val) {
      fetchLocales();
      initSelectedLocales();
    }
  }
);

/** 최초 locale 로드 완료 시 기본 체크 초기화 */
watch(localeList, () => {
  if (props.visible) {
    initSelectedLocales();
  }
});

onMounted(fetchLocales);
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
      <div class="mx-4 w-full max-w-sm rounded-lg bg-white shadow-lg">
        <!-- 헤더 -->
        <div class="border-b border-gray-200 px-5 py-3">
          <h3 class="text-sm font-bold text-gray-800">피드백 생성 언어 선택</h3>
        </div>

        <!-- 본문 -->
        <div class="px-5 py-4">
          <p v-if="loading" class="text-center text-sm text-gray-500">로딩 중...</p>

          <template v-else>
            <!-- 전체 선택 -->
            <label class="mb-3 flex cursor-pointer items-center gap-2 border-b border-gray-200 pb-3">
              <input
                type="checkbox"
                :checked="isAllSelected"
                class="h-4 w-4 rounded border-gray-300 text-blue-600"
                @change="toggleAll"
              />
              <span class="text-sm font-medium text-gray-800">전체</span>
            </label>

            <!-- 개별 locale 목록 -->
            <div class="grid grid-cols-2 gap-2">
              <!-- 한국어 — ko 피드백 유무에 따라 활성/비활성 분기 -->
              <label
                class="flex items-center gap-2"
                :class="hasKoFeedback ? 'cursor-pointer' : 'opacity-60'"
              >
                <input
                  type="checkbox"
                  :checked="selectedLocales.includes('ko')"
                  :disabled="!hasKoFeedback"
                  class="h-4 w-4 rounded border-gray-300 text-blue-600"
                  @change="toggleLocale('ko')"
                />
                <span class="text-sm text-gray-700">
                  한국어 (ko)
                  <span v-if="existingLocales.includes('ko')" class="text-xs text-green-600">*</span>
                </span>
              </label>

              <!-- 번역 대상 locale -->
              <label
                v-for="loc in localeList.filter((l) => l.code_name !== 'ko')"
                :key="loc.code_name"
                class="flex cursor-pointer items-center gap-2"
              >
                <input
                  type="checkbox"
                  :checked="selectedLocales.includes(loc.code_name)"
                  class="h-4 w-4 rounded border-gray-300 text-blue-600"
                  @change="toggleLocale(loc.code_name)"
                />
                <span class="text-sm text-gray-700">
                  {{ loc.code_desc }} ({{ loc.code_name }})
                  <span v-if="existingLocales.includes(loc.code_name)" class="text-xs text-green-600">*</span>
                </span>
              </label>
            </div>

            <!-- 범례 -->
            <p v-if="existingLocales.length > 0" class="mt-3 text-xs text-gray-400">
              <span class="text-green-600">*</span> 피드백 생성 완료
            </p>
          </template>
        </div>

        <!-- 하단 버튼 -->
        <div class="flex items-center justify-center gap-3 border-t border-gray-200 px-5 py-3">
          <button class="btn btn-sm btn-primary px-6" @click="handleConfirm">
            생성
          </button>
          <button class="btn btn-sm btn-secondary px-6" @click="emit('cancel')">
            취소
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
