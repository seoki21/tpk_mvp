<!--
  연습문제 생성(API) 페이지
  - 좌측: 생성 조건 폼 (시험종류, 레벨, 영역, 문항구조, 난이도, 문항수, 생성방법)
  - 우측: AI API 응답 JSON 출력 영역
  - 하단 중앙: 생성(API) 버튼
  - 우상단: 저장 버튼
  - ※ 현재 UI 껍데기만 구현 (API 미연동)
-->
<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useToast } from '@/composables/useToast';

const router = useRouter();
const toast = useToast();

/* ========== 폼 데이터 ========== */
const form = ref({
  exam_type: '',
  tpk_level: '',
  section: '',
  struct_type: '',
  difficulty: '',
  question_count: '',
  generate_method: 'realtime'
});

/** JSON 출력 텍스트 */
const jsonText = ref('');

/** pre 요소 참조 (스크롤 동기화용) */
const preRef = ref(null);

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

/** textarea 스크롤 시 pre 오버레이의 스크롤을 동기화한다. */
function syncScroll(event) {
  if (preRef.value) {
    preRef.value.scrollTop = event.target.scrollTop;
    preRef.value.scrollLeft = event.target.scrollLeft;
  }
}

/** 뒤로가기 → 연습문제 관리 목록 */
function goBack() {
  router.push({ name: 'practiceQuestions' });
}

/** 생성(API) 버튼 클릭 — 추후 구현 */
function handleGenerate() {
  toast.info('생성(API) 기능은 추후 구현 예정입니다.');
}

/** 저장 버튼 클릭 — 추후 구현 */
function handleSave() {
  toast.info('저장 기능은 추후 구현 예정입니다.');
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- 서브 타이틀 + 뒤로가기 -->
    <div class="mb-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <button
          class="flex h-8 w-8 items-center justify-center rounded-full text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
          title="연습문제 관리로 돌아가기"
          @click="goBack"
        >
          <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h2 class="text-xl font-bold text-gray-800">연습문제 생성(API)</h2>
      </div>
      <button
        class="rounded-md border border-gray-300 bg-gray-100 px-5 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200"
        @click="handleSave"
      >
        저장
      </button>
    </div>

    <!-- 본문: 좌측 폼 + 우측 JSON 출력 -->
    <div class="flex min-h-0 flex-1 overflow-hidden rounded border border-gray-300">
      <!-- 좌측: 생성 조건 폼 -->
      <div class="w-2/5 overflow-y-auto border-r border-gray-200 p-6">
        <div class="space-y-5">
          <!-- 시험종류 -->
          <div class="flex items-center">
            <label class="w-24 shrink-0 text-sm font-bold text-gray-700">시험종류</label>
            <select
              v-model="form.exam_type"
              class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
            >
              <option value=""></option>
            </select>
          </div>

          <!-- 레벨 -->
          <div class="flex items-center">
            <label class="w-24 shrink-0 text-sm font-bold text-gray-700">레벨</label>
            <select
              v-model="form.tpk_level"
              class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
            >
              <option value=""></option>
            </select>
          </div>

          <!-- 영역 -->
          <div class="flex items-center">
            <label class="w-24 shrink-0 text-sm font-bold text-gray-700">영역</label>
            <select
              v-model="form.section"
              class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
            >
              <option value=""></option>
            </select>
          </div>

          <!-- 문항구조 -->
          <div class="flex items-center">
            <label class="w-24 shrink-0 text-sm font-bold text-gray-700">문항구조</label>
            <select
              v-model="form.struct_type"
              class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
            >
              <option value=""></option>
            </select>
          </div>

          <!-- 난이도 -->
          <div class="flex items-center">
            <label class="w-24 shrink-0 text-sm font-bold text-gray-700">난이도</label>
            <input
              v-model="form.difficulty"
              type="text"
              class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          <!-- 구분선 -->
          <div class="border-t border-gray-200 pt-5">
            <!-- 문항수 -->
            <div class="mb-5 flex items-center">
              <label class="w-24 shrink-0 text-sm font-bold text-gray-700">문항수</label>
              <input
                v-model.number="form.question_count"
                type="number"
                min="1"
                class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
              />
            </div>

            <!-- 생성방법 -->
            <div class="flex items-center">
              <label class="w-24 shrink-0 text-sm font-bold text-gray-700">생성방법</label>
              <div class="flex gap-4">
                <label class="flex items-center gap-1.5 text-sm text-gray-700">
                  <input
                    v-model="form.generate_method"
                    type="radio"
                    value="realtime"
                    class="text-blue-600"
                  />
                  실시간
                </label>
                <label class="flex items-center gap-1.5 text-sm text-gray-700">
                  <input
                    v-model="form.generate_method"
                    type="radio"
                    value="batch"
                    class="text-blue-600"
                  />
                  배치(batch)
                </label>
              </div>
            </div>
          </div>

          <!-- 생성(API) 버튼 -->
          <div class="flex justify-center pt-4">
            <button
              class="rounded-md border border-blue-300 bg-blue-50 px-6 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100"
              @click="handleGenerate"
            >
              생성(API)
            </button>
          </div>
        </div>
      </div>

      <!-- 우측: JSON 출력 영역 (구문 강조 오버레이 방식 — 기출문제 관리와 동일) -->
      <div class="flex w-3/5 flex-col">
        <div class="flex items-center border-b border-gray-700 bg-gray-800 px-4 py-2">
          <span class="text-sm text-gray-300">JSON format 출력</span>
        </div>
        <div class="relative flex-1 overflow-hidden bg-gray-50">
          <template v-if="jsonText">
            <!-- 구문 강조 표시 레이어 (시각적 표시만) -->
            <pre
              ref="preRef"
              class="pointer-events-none absolute inset-0 overflow-hidden whitespace-pre-wrap break-all p-4 font-mono text-xs leading-relaxed"
              v-html="highlightJson(jsonText)"
            ></pre>
            <!-- 투명 입력 레이어 (편집 수신) -->
            <textarea
              :value="jsonText"
              spellcheck="false"
              class="absolute inset-0 h-full w-full resize-none whitespace-pre-wrap break-all bg-transparent p-4 font-mono text-xs leading-relaxed text-transparent caret-gray-800 outline-none"
              @input="jsonText = $event.target.value"
              @scroll="syncScroll"
            ></textarea>
          </template>
          <div v-else class="flex h-full items-center justify-center text-gray-400">
            '생성(API)' 버튼을 클릭하면 결과가 표시됩니다.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
