<!--
  AI 프로바이더 선택 드롭다운 버튼 컴포넌트
  - Claude/Gemini 중 선택하여 변환을 실행할 수 있는 드롭다운 버튼
  - 기출문항 변환(JSON) 화면에서 문제 변환, 피드백 변환 등에 재사용한다.
-->
<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

defineProps({
  /** 버튼 라벨 텍스트 */
  label: {
    type: String,
    default: 'JSON 변환'
  },
  /** 로딩 중 라벨 텍스트 */
  loadingLabel: {
    type: String,
    default: '변환 중...'
  },
  /** 비활성화 여부 */
  disabled: {
    type: Boolean,
    default: false
  },
  /** 로딩 상태 */
  loading: {
    type: Boolean,
    default: false
  },
  /** 버튼 색상 테마 ('blue' | 'purple') */
  theme: {
    type: String,
    default: 'blue'
  }
});

const emit = defineEmits(['select']);

const showMenu = ref(false);

/** 테마별 버튼 스타일 (soft blue 톤 통일) */
const themeStyles = {
  blue: 'border-blue-300 bg-blue-50 text-blue-600 hover:border-blue-400 hover:bg-blue-100 disabled:border-gray-200 disabled:bg-gray-50 disabled:text-gray-400',
  purple: 'border-blue-300 bg-blue-50 text-blue-600 hover:border-blue-400 hover:bg-blue-100 disabled:border-gray-200 disabled:bg-gray-50 disabled:text-gray-400'
};

/** 테마별 드롭다운 호버 스타일 */
const hoverStyles = {
  blue: 'hover:bg-blue-50',
  purple: 'hover:bg-blue-50'
};

function handleSelect(provider) {
  showMenu.value = false;
  emit('select', provider);
}

/** 외부 클릭 시 드롭다운 닫기 */
function handleOutsideClick() {
  showMenu.value = false;
}

onMounted(() => document.addEventListener('click', handleOutsideClick));
onUnmounted(() => document.removeEventListener('click', handleOutsideClick));
</script>

<template>
  <div class="relative">
    <button
      class="inline-flex items-center gap-1 rounded-md border px-4 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed"
      :class="themeStyles[theme]"
      :disabled="disabled || loading"
      @click.stop="showMenu = !showMenu"
    >
      {{ loading ? loadingLabel : label }}
      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>
    <!-- 드롭다운 메뉴 -->
    <div
      v-if="showMenu"
      class="absolute right-0 z-10 mt-1 w-44 rounded-md border border-gray-200 bg-white py-1 shadow-lg"
    >
      <button
        class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700"
        :class="hoverStyles[theme]"
        @click="handleSelect('claude')"
      >
        <span class="inline-block h-2 w-2 rounded-full bg-orange-400"></span>
        Claude
      </button>
      <button
        class="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-gray-700"
        :class="hoverStyles[theme]"
        @click="handleSelect('gemini')"
      >
        <span class="inline-block h-2 w-2 rounded-full bg-blue-400"></span>
        Gemini
      </button>
    </div>
  </div>
</template>
