<!--
  JSON 편집기 패널 컴포넌트
  - 좌측 40% 영역에서 JSON 텍스트를 편집하고 구문 강조를 표시한다.
  - textarea(투명)와 pre(구문강조) 오버레이 방식으로 구현.
  - 문제 항목의 경우 문제/피드백 탭 전환을 지원한다.
-->
<script setup>
import { ref } from 'vue';

const props = defineProps({
  /** 항목 타입: 'question' 또는 'instruction' */
  itemType: {
    type: String,
    required: true
  },
  /** 현재 활성 JSON 텍스트 */
  jsonText: {
    type: String,
    default: '{}'
  },
  /** JSON 파싱 에러 여부 */
  hasError: {
    type: Boolean,
    default: false
  },
  /** 활성 탭: 'question' | 'feedback' (문제 항목 전용) */
  activeTab: {
    type: String,
    default: 'question'
  },
  /** 피드백 생성 중 여부 */
  feedbackGenerating: {
    type: Boolean,
    default: false
  },
  /** 단건 저장 중 여부 */
  itemSaving: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits([
  'update:jsonText',
  'update:activeTab',
  'generate-feedback',
  'save-item'
]);

/** pre 요소 참조 (스크롤 동기화용) */
const preRef = ref(null);

/** 마지막 저장 이후 내용이 수정되었는지 여부 */
const isDirty = ref(false);

/** blur 시 저장 안내 문구 표시 여부 (수정됨 + JSON 오류 없음 + 포커스 이탈) */
const showSaveHint = ref(false);

/**
 * JSON 텍스트에 구문 강조 HTML을 적용한다.
 * 키(보라), 문자열 값(초록), 숫자(파랑), boolean/null(주황) 색상 적용.
 */
function highlightJson(text) {
  if (!text) return '{}';
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return (
    escaped
      .replace(/"([^"]+)"(?=\s*:)/g, '<span class="text-purple-600">"$1"</span>')
      .replace(/:\s*"([^"]*)"/g, ': <span class="text-green-600">"$1"</span>')
      .replace(/:\s*(\d+\.?\d*)/g, ': <span class="text-blue-600">$1</span>')
      .replace(/:\s*(true|false|null)/g, ': <span class="text-orange-600">$1</span>') + '\n'
  );
}

/** 입력 핸들러 — 부모에게 변경된 텍스트 전달 및 dirty 상태 활성화 */
function handleInput(event) {
  isDirty.value = true;
  showSaveHint.value = false; // 입력 중에는 힌트 숨김
  emit('update:jsonText', event.target.value);
}

/** blur 핸들러 — 수정된 내용이 있고 JSON 오류가 없을 때 저장 안내 문구 표시 */
function handleBlur() {
  if (isDirty.value && !props.hasError) {
    showSaveHint.value = true;
  }
}

/** 저장 버튼 클릭 — dirty 상태 초기화 후 부모에게 save-item 이벤트 전달 */
function handleSaveClick() {
  isDirty.value = false;
  showSaveHint.value = false;
  emit('save-item');
}

/** textarea 스크롤 시 pre 오버레이의 스크롤을 동기화 */
function syncScroll(event) {
  if (preRef.value) {
    preRef.value.scrollTop = event.target.scrollTop;
    preRef.value.scrollLeft = event.target.scrollLeft;
  }
}
</script>

<template>
  <div class="flex w-2/5 shrink-0 flex-col">
    <!-- 탭바 (문제 항목만 — 문제/피드백 전환) -->
    <div
      v-if="itemType === 'question'"
      class="mb-1 flex items-center gap-1 border-b border-gray-200 pb-1"
    >
      <button
        class="rounded-t px-2.5 py-1 text-xs transition-colors"
        :class="
          activeTab === 'question'
            ? 'border-b-2 border-blue-500 font-medium text-blue-700'
            : 'text-gray-400 hover:text-gray-600'
        "
        @click="emit('update:activeTab', 'question')"
      >
        문제
      </button>
      <button
        class="rounded-t px-2.5 py-1 text-xs transition-colors"
        :class="
          activeTab === 'feedback'
            ? 'border-b-2 border-blue-500 font-medium text-blue-700'
            : 'text-gray-400 hover:text-gray-600'
        "
        @click="emit('update:activeTab', 'feedback')"
      >
        피드백
      </button>
      <button
        class="btn btn-xs btn-primary ml-auto"
        :disabled="feedbackGenerating"
        @click="emit('generate-feedback')"
      >
        {{ feedbackGenerating ? '생성 중...' : '피드백 생성(API)' }}
      </button>
      <button
        class="btn btn-xs btn-secondary"
        :disabled="itemSaving"
        @click="handleSaveClick"
      >
        {{ itemSaving ? '저장 중...' : '저장' }}
      </button>
    </div>
    <!-- JSON 편집기 -->
    <div
      class="relative min-h-[80px] flex-1 overflow-hidden rounded border bg-gray-50"
      :class="hasError ? 'border-red-400' : 'border-gray-200'"
    >
      <!-- 구문 강조 표시 레이어 (시각적 표시만, 클릭 투과) -->
      <pre
        ref="preRef"
        class="pointer-events-none absolute inset-0 overflow-hidden whitespace-pre-wrap break-all p-2 font-mono text-xs leading-relaxed"
        v-html="highlightJson(jsonText)"
      ></pre>
      <!-- 투명 입력 레이어 (실제 편집 수신, 컨테이너 꽉 채움) -->
      <textarea
        :value="jsonText"
        spellcheck="false"
        class="absolute inset-0 h-full w-full resize-none whitespace-pre-wrap break-all bg-transparent p-2 font-mono text-xs leading-relaxed text-transparent caret-gray-800 outline-none"
        @input="handleInput"
        @blur="handleBlur"
        @scroll="syncScroll"
      ></textarea>
    </div>
    <!-- JSON 에러 / 저장 안내 문구 (동시 표시 안 함) -->
    <span v-if="hasError" class="mt-1 block text-xs text-red-500">
      JSON 형식 오류
    </span>
    <span v-else-if="showSaveHint" class="mt-1 block text-xs text-amber-500">
      수정사항을 반영하려면 저장이 필요합니다
    </span>
  </div>
</template>
