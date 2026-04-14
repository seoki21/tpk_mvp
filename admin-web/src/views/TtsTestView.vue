<!--
  TTS 생성(테스트) 뷰
  GPT-SoVITS API를 통해 기출문항 JSON 텍스트를 음성으로 변환하는 테스트 화면.
  - 좌측: GPT-SoVITS 파라미터 설정 패널
  - 우측: JSON 파일 업로드 → 문항별 텍스트 추출 + 화자 자동 감지 표시 → TTS 생성/재생/다운로드
  - 백엔드(/api/v1/tts/generate)가 화자 분리 + GPT-SoVITS 호출 + WAV 병합을 처리한다.
  - 참조 음성: 남자(ref_male.wav) / 여자(ref_female.wav) 고정 (백엔드 하드코딩)
-->
<script setup>
import { ref, computed } from 'vue'
import api, { API_TIMEOUT_AI } from '@/api/index.js'

// ─── GPT-SoVITS 접속 설정 (고정값, UI 미노출) ──────────────────
const apiUrl = ref('http://211.55.172.19:9880')

// ─── 텍스트 언어 설정 ─────────────────────────────────────────
const textLang = ref('ko')

// ─── 출력 설정 ─────────────────────────────────────────────────
/** 스트리밍 모드 여부 — true 시 GPT-SoVITS가 청크 단위로 전송 */
const streamingMode = ref(false)
/** 스트리밍 전용: 의미 토큰 오버랩 길이 */
const overlapLength = ref(2)
/** 스트리밍 전용: 최소 청크 토큰 길이 */
const minChunkLength = ref(16)

// ─── 생성 파라미터 ─────────────────────────────────────────────
const topK = ref(15)
const topP = ref(1.0)
const temperature = ref(1.0)
const speedFactor = ref(1.0)
const textSplitMethod = ref('cut5')
const seed = ref(-1)
const batchSize = ref(1)
const fragmentInterval = ref(0.3)
const repetitionPenalty = ref(1.35)
const parallelInfer = ref(true)
const superSampling = ref(false)

// ─── JSON 파일 처리 ────────────────────────────────────────────
const fileName = ref('')
/** 파싱된 문항 목록 */
const parsedItems = ref([])
const fileInput = ref(null)

/**
 * 파일 선택 이벤트 처리 — JSON을 읽어 문항 목록을 추출한다.
 */
function onFileSelect(event) {
  const file = event.target.files[0]
  if (!file) return
  fileName.value = file.name
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const json = JSON.parse(e.target.result)
      parsedItems.value = parseJsonItems(json)
    } catch (err) {
      alert('JSON 파일 파싱 오류: ' + err.message)
      resetFile()
    }
  }
  reader.readAsText(file, 'utf-8')
}

/**
 * JSON 배열에서 TTS 대상 텍스트를 추출하고 화자 정보를 분석한다.
 * - item_type "I" (지시문): instruction + question_text
 * - item_type "Q" (문항): question_text
 * - 화자 접두사(남자:/여자:) 감지 → speakers 배열 반환
 *
 * @param {Array} jsonData - 파싱된 JSON 배열
 */
function parseJsonItems(jsonData) {
  const items = []
  let idCounter = 0
  for (const item of jsonData) {
    if (!item.item_type) continue
    let text
    let label

    if (item.item_type === 'I') {
      const parts = []
      if (item.instruction) parts.push(item.instruction)
      if (item.question_text) parts.push(item.question_text)
      text = parts.join('\n')
      if (!text.trim()) continue
      const noLabel = item.no_list ? `[${item.no_list[0]}~${item.no_list[item.no_list.length - 1]}]` : ''
      label = `지시문 ${noLabel}`
    } else if (item.item_type === 'Q') {
      if (!item.question_text?.trim()) continue
      text = item.question_text
      label = `Q${item.no}`
    } else {
      continue
    }

    // 화자 감지 — 정규식으로 접두사 추출 (남자:/여자:/남:/여: 등)
    const speakerMatches = [...text.matchAll(/^(남자|여자|남|여|가|나)\s*:/gm)]
    const speakerSet = new Set(
      speakerMatches.map((m) => {
        const raw = m[1]
        if (raw === '남' || raw === '남자') return '남자'
        if (raw === '여' || raw === '여자') return '여자'
        return raw
      }),
    )
    const speakers = [...speakerSet]

    items.push({
      id: idCounter++,
      label,
      text,
      speakers, // 감지된 화자 목록 ([] = 단일 화자)
      audioUrl: null,
      status: 'idle', // idle | generating | done | error
      errorMsg: '',
      selected: true,
    })
  }
  return items
}

/** 파일 및 파싱 결과 초기화 */
function resetFile() {
  fileName.value = ''
  parsedItems.value.forEach((i) => {
    if (i.audioUrl) URL.revokeObjectURL(i.audioUrl)
  })
  parsedItems.value = []
  if (fileInput.value) fileInput.value.value = ''
}

// ─── 전체 선택 ────────────────────────────────────────────────
const allSelected = computed({
  get: () => parsedItems.value.length > 0 && parsedItems.value.every((i) => i.selected),
  set: (val) => parsedItems.value.forEach((i) => (i.selected = val)),
})

// ─── TTS 생성 ────────────────────────────────────────────────

/**
 * 단일 문항에 대해 백엔드 TTS API를 호출한다.
 * 백엔드가 화자 감지 → GPT-SoVITS 호출 → WAV 병합을 처리한다.
 * @param {Object} item - 문항 객체
 */
async function generateTts(item) {
  if (!apiUrl.value.trim()) {
    alert('API URL을 입력해주세요.')
    return
  }
  item.status = 'generating'
  item.errorMsg = ''
  if (item.audioUrl) {
    URL.revokeObjectURL(item.audioUrl)
    item.audioUrl = null
  }

  try {
    const payload = {
      text: item.text,
      gpt_sovits_url: apiUrl.value.trim(),
      text_lang: textLang.value,
      top_k: topK.value,
      top_p: topP.value,
      temperature: temperature.value,
      speed_factor: speedFactor.value,
      text_split_method: textSplitMethod.value,
      seed: seed.value,
      batch_size: batchSize.value,
      fragment_interval: fragmentInterval.value,
      repetition_penalty: repetitionPenalty.value,
      parallel_infer: parallelInfer.value,
      super_sampling: superSampling.value,
      streaming_mode: streamingMode.value,
      overlap_length: overlapLength.value,
      min_chunk_length: minChunkLength.value,
    }

    // 백엔드가 WAV 바이너리를 직접 반환 — responseType: 'blob'으로 수신
    const blob = await api.post('/api/v1/tts/generate', payload, {
      responseType: 'blob',
      timeout: API_TIMEOUT_AI,
    })

    item.audioUrl = URL.createObjectURL(new Blob([blob], { type: 'audio/wav' }))
    item.status = 'done'
  } catch (err) {
    item.status = 'error'
    item.errorMsg = err.detail || err.message || 'TTS 생성 실패'
  }
}

/**
 * 선택된 문항을 순차적으로 일괄 생성한다.
 */
async function generateSelected() {
  const targets = parsedItems.value.filter((i) => i.selected)
  if (!targets.length) {
    alert('선택된 항목이 없습니다.')
    return
  }
  for (const item of targets) {
    await generateTts(item)
  }
}

/** 생성된 오디오를 WAV 파일로 다운로드한다. */
function downloadAudio(item) {
  if (!item.audioUrl) return
  const a = document.createElement('a')
  a.href = item.audioUrl
  a.download = `${item.label}.wav`
  a.click()
}

// ─── 셀렉트 옵션 ─────────────────────────────────────────────
const langOptions = [
  { value: 'ko', label: '한국어 (ko)' },
  { value: 'zh', label: '중국어 (zh)' },
  { value: 'en', label: '영어 (en)' },
  { value: 'ja', label: '일본어 (ja)' },
  { value: 'auto', label: '자동감지 (auto)' },
]

const splitMethods = [
  { value: 'cut0', label: 'cut0 — 분할 없음' },
  { value: 'cut1', label: 'cut1 — 마침표/물음표' },
  { value: 'cut2', label: 'cut2 — 50자마다' },
  { value: 'cut3', label: 'cut3 — 중국어마다' },
  { value: 'cut4', label: 'cut4 — 영어마다' },
  { value: 'cut5', label: 'cut5 — 구두점마다' },
]

/** 생성 중인 항목이 있으면 일괄 생성 버튼 비활성화 */
const isAnyGenerating = computed(() => parsedItems.value.some((i) => i.status === 'generating'))
</script>

<template>
  <div class="flex h-full flex-col overflow-hidden">
    <!-- 페이지 헤더 -->
    <div class="shrink-0 border-b border-gray-200 bg-white px-6 py-4">
      <h1 class="text-xl font-bold text-gray-800">🔊 TTS 생성 (테스트)</h1>
      <p class="mt-0.5 text-sm text-gray-500">
        GPT-SoVITS API를 사용하여 기출문항 JSON의 텍스트를 음성으로 변환합니다. 화자 접두사(남자:/여자:) 감지
        시 자동으로 복수 화자 처리 후 병합합니다.
      </p>
    </div>

    <!-- 메인 컨텐츠 -->
    <div class="flex min-h-0 flex-1 gap-0">
      <!-- ─────────────────────────────────────────────────
           좌측: 설정 패널
           ───────────────────────────────────────────────── -->
      <aside class="flex w-72 shrink-0 flex-col overflow-y-auto border-r border-gray-200 bg-gray-50">
        <div class="space-y-1 p-4">
          <!-- 고정 화자 설정 (읽기 전용 표시) -->
          <section class="rounded-lg border border-blue-200 bg-blue-50">
            <div class="border-b border-blue-100 px-3 py-2">
              <h2 class="text-xs font-semibold uppercase tracking-wide text-blue-600">참조 음성 (고정)</h2>
            </div>
            <div class="space-y-2 p-3">
              <div class="rounded bg-white px-2.5 py-2 ring-1 ring-pink-200">
                <div class="mb-1 flex items-center gap-1.5">
                  <span class="rounded bg-pink-100 px-1.5 py-0.5 text-xs font-bold text-pink-700">여자</span>
                  <span class="text-xs text-gray-500">ref_female.wav</span>
                </div>
                <p class="text-xs italic text-gray-500">"저, 책상을 사러 왔는데요."</p>
              </div>
              <div class="rounded bg-white px-2.5 py-2 ring-1 ring-blue-200">
                <div class="mb-1 flex items-center gap-1.5">
                  <span class="rounded bg-blue-100 px-1.5 py-0.5 text-xs font-bold text-blue-700">남자</span>
                  <span class="text-xs text-gray-500">ref_male.wav</span>
                </div>
                <p class="text-xs italic text-gray-500">"네, 책상은 이쪽에 있습니다."</p>
              </div>
              <p class="text-xs text-blue-500">백엔드에서 화자 자동 감지 후 매핑됩니다.</p>
            </div>
          </section>

          <!-- 출력 설정 -->
          <section class="rounded-lg border border-gray-200 bg-white">
            <div class="border-b border-gray-100 px-3 py-2">
              <h2 class="text-xs font-semibold uppercase tracking-wide text-gray-500">출력 설정</h2>
            </div>
            <div class="space-y-3 p-3">
              <div class="flex items-center justify-between rounded bg-gray-50 px-2 py-1.5">
                <span class="text-xs text-gray-600">출력 포맷</span>
                <span class="rounded bg-gray-200 px-2 py-0.5 text-xs font-bold text-gray-700">WAV</span>
              </div>
              <div class="flex items-center justify-between">
                <div>
                  <span class="text-xs font-medium text-gray-700">스트리밍 모드</span>
                  <p class="text-xs text-gray-400">(streaming_mode)</p>
                </div>
                <button
                  class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors"
                  :class="streamingMode ? 'bg-blue-500' : 'bg-gray-300'"
                  @click="streamingMode = !streamingMode"
                >
                  <span
                    class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                    :class="streamingMode ? 'translate-x-4' : 'translate-x-0.5'"
                  ></span>
                </button>
              </div>
              <template v-if="streamingMode">
                <div class="rounded bg-blue-50 px-2 py-1.5 text-xs text-blue-600">스트리밍 전용 파라미터</div>
                <div>
                  <label class="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
                    <span>overlap_length</span>
                    <span class="font-bold text-blue-600">{{ overlapLength }}</span>
                  </label>
                  <input
                    v-model.number="overlapLength"
                    type="range"
                    min="0"
                    max="20"
                    step="1"
                    class="w-full accent-blue-500"
                  />
                  <div class="flex justify-between text-xs text-gray-400"><span>0</span><span>20</span></div>
                </div>
                <div>
                  <label class="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
                    <span>min_chunk_length</span>
                    <span class="font-bold text-blue-600">{{ minChunkLength }}</span>
                  </label>
                  <input
                    v-model.number="minChunkLength"
                    type="range"
                    min="1"
                    max="100"
                    step="1"
                    class="w-full accent-blue-500"
                  />
                  <div class="flex justify-between text-xs text-gray-400"><span>1</span><span>100</span></div>
                </div>
              </template>
            </div>
          </section>

          <!-- 생성 파라미터 -->
          <section class="rounded-lg border border-gray-200 bg-white">
            <div class="border-b border-gray-100 px-3 py-2">
              <h2 class="text-xs font-semibold uppercase tracking-wide text-gray-500">생성 파라미터</h2>
            </div>
            <div class="space-y-3 p-3">
              <div>
                <label class="mb-1 block text-xs font-medium text-gray-700">텍스트 언어</label>
                <select
                  v-model="textLang"
                  class="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
                >
                  <option v-for="o in langOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
                </select>
              </div>
              <div>
                <label class="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
                  <span>top_k</span><span class="font-bold text-blue-600">{{ topK }}</span>
                </label>
                <input v-model.number="topK" type="range" min="1" max="50" step="1" class="w-full accent-blue-500" />
                <div class="flex justify-between text-xs text-gray-400"><span>1</span><span>50</span></div>
              </div>
              <div>
                <label class="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
                  <span>top_p</span><span class="font-bold text-blue-600">{{ topP.toFixed(2) }}</span>
                </label>
                <input
                  v-model.number="topP"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  class="w-full accent-blue-500"
                />
                <div class="flex justify-between text-xs text-gray-400"><span>0</span><span>1</span></div>
              </div>
              <div>
                <label class="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
                  <span>temperature</span><span class="font-bold text-blue-600">{{ temperature.toFixed(2) }}</span>
                </label>
                <input
                  v-model.number="temperature"
                  type="range"
                  min="0"
                  max="2"
                  step="0.05"
                  class="w-full accent-blue-500"
                />
                <div class="flex justify-between text-xs text-gray-400"><span>0</span><span>2</span></div>
              </div>
              <div>
                <label class="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
                  <span>speed_factor</span><span class="font-bold text-blue-600">{{ speedFactor.toFixed(2) }}</span>
                </label>
                <input
                  v-model.number="speedFactor"
                  type="range"
                  min="0.5"
                  max="2.0"
                  step="0.05"
                  class="w-full accent-blue-500"
                />
                <div class="flex justify-between text-xs text-gray-400"><span>0.5</span><span>2.0</span></div>
              </div>
              <div>
                <label class="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
                  <span>fragment_interval</span
                  ><span class="font-bold text-blue-600">{{ fragmentInterval.toFixed(2) }}</span>
                </label>
                <input
                  v-model.number="fragmentInterval"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  class="w-full accent-blue-500"
                />
                <div class="flex justify-between text-xs text-gray-400"><span>0</span><span>1</span></div>
              </div>
              <div>
                <label class="mb-1 flex items-center justify-between text-xs font-medium text-gray-700">
                  <span>repetition_penalty</span
                  ><span class="font-bold text-blue-600">{{ repetitionPenalty.toFixed(2) }}</span>
                </label>
                <input
                  v-model.number="repetitionPenalty"
                  type="range"
                  min="1.0"
                  max="2.0"
                  step="0.05"
                  class="w-full accent-blue-500"
                />
                <div class="flex justify-between text-xs text-gray-400"><span>1.0</span><span>2.0</span></div>
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-gray-700">text_split_method</label>
                <select
                  v-model="textSplitMethod"
                  class="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
                >
                  <option v-for="m in splitMethods" :key="m.value" :value="m.value">{{ m.label }}</option>
                </select>
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-gray-700">batch_size</label>
                <input
                  v-model.number="batchSize"
                  type="number"
                  min="1"
                  max="10"
                  class="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label class="mb-1 block text-xs font-medium text-gray-700"
                  >seed <span class="text-gray-400">(-1 = 랜덤)</span></label
                >
                <input
                  v-model.number="seed"
                  type="number"
                  class="w-full rounded border border-gray-300 px-2 py-1.5 text-xs focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div class="space-y-2 border-t border-gray-100 pt-2">
                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-xs font-medium text-gray-700">parallel_infer</span>
                    <p class="text-xs text-gray-400">병렬 추론</p>
                  </div>
                  <button
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors"
                    :class="parallelInfer ? 'bg-blue-500' : 'bg-gray-300'"
                    @click="parallelInfer = !parallelInfer"
                  >
                    <span
                      class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                      :class="parallelInfer ? 'translate-x-4' : 'translate-x-0.5'"
                    ></span>
                  </button>
                </div>
                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-xs font-medium text-gray-700">super_sampling</span>
                    <p class="text-xs text-gray-400">슈퍼 샘플링 (품질↑)</p>
                  </div>
                  <button
                    class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors"
                    :class="superSampling ? 'bg-blue-500' : 'bg-gray-300'"
                    @click="superSampling = !superSampling"
                  >
                    <span
                      class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                      :class="superSampling ? 'translate-x-4' : 'translate-x-0.5'"
                    ></span>
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      </aside>

      <!-- ─────────────────────────────────────────────────
           우측: JSON 업로드 + 문항 목록
           ───────────────────────────────────────────────── -->
      <main class="flex min-w-0 flex-1 flex-col overflow-hidden bg-white">
        <!-- 툴바 -->
        <div class="shrink-0 border-b border-gray-200 bg-gray-50 px-5 py-3">
          <div class="flex flex-wrap items-center gap-3">
            <input ref="fileInput" type="file" accept=".json" class="hidden" @change="onFileSelect" />
            <button
              class="flex items-center gap-1.5 rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
              @click="fileInput.click()"
            >
              📂 JSON 파일 선택
            </button>
            <span
              v-if="fileName"
              class="flex items-center gap-1.5 rounded bg-white px-2 py-1 text-sm text-gray-700 ring-1 ring-gray-200"
            >
              📄 {{ fileName }}
              <span class="text-xs text-gray-400">({{ parsedItems.length }}개 항목)</span>
            </span>
            <button
              v-if="fileName"
              class="rounded px-2 py-1.5 text-sm text-gray-500 hover:bg-gray-200 hover:text-gray-700"
              @click="resetFile"
            >
              ✕ 초기화
            </button>
            <div v-if="parsedItems.length" class="ml-auto flex items-center gap-2">
              <label class="flex cursor-pointer items-center gap-1.5 text-sm text-gray-600">
                <input v-model="allSelected" type="checkbox" class="h-4 w-4 accent-blue-500" />
                전체선택
              </label>
              <button
                :disabled="isAnyGenerating"
                class="flex items-center gap-1.5 rounded bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
                @click="generateSelected"
              >
                {{ isAnyGenerating ? '⏳ 생성 중...' : '🔊 선택 항목 일괄 생성' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 빈 상태 -->
        <div v-if="!parsedItems.length" class="flex flex-1 flex-col items-center justify-center gap-3 text-gray-400">
          <span class="text-5xl">📂</span>
          <p class="text-base font-medium">JSON 파일을 선택하면 문항 목록이 표시됩니다.</p>
          <p class="text-sm">기출문항 변환 결과 JSON 파일을 업로드하세요.</p>
        </div>

        <!-- 문항 목록 -->
        <div v-else class="flex-1 overflow-y-auto p-5">
          <div class="space-y-3">
            <div
              v-for="item in parsedItems"
              :key="item.id"
              class="overflow-hidden rounded-lg border shadow-sm transition-all"
              :class="{
                'border-green-300 bg-green-50': item.status === 'done',
                'border-red-300 bg-red-50': item.status === 'error',
                'border-blue-300 bg-blue-50': item.status === 'generating',
                'border-gray-200 bg-white': item.status === 'idle',
              }"
            >
              <!-- 카드 헤더 -->
              <div
                class="flex items-center gap-3 px-4 py-2.5"
                :class="{
                  'bg-green-100/60': item.status === 'done',
                  'bg-red-100/60': item.status === 'error',
                  'bg-blue-100/60': item.status === 'generating',
                  'bg-gray-50': item.status === 'idle',
                }"
              >
                <input
                  v-model="item.selected"
                  type="checkbox"
                  class="h-4 w-4 shrink-0 accent-blue-500"
                  :disabled="item.status === 'generating'"
                />
                <!-- 항목 라벨 -->
                <span
                  class="shrink-0 rounded px-2 py-0.5 text-xs font-bold"
                  :class="
                    item.label.startsWith('지시문') ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                  "
                >
                  {{ item.label }}
                </span>

                <!-- 화자 감지 배지 -->
                <div class="flex items-center gap-1">
                  <template v-if="item.speakers.length === 0">
                    <span class="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">단일화자</span>
                  </template>
                  <template v-else>
                    <span
                      v-for="sp in item.speakers"
                      :key="sp"
                      class="rounded px-1.5 py-0.5 text-xs font-medium"
                      :class="sp === '남자' ? 'bg-blue-100 text-blue-600' : 'bg-pink-100 text-pink-600'"
                    >
                      {{ sp }}
                    </span>
                    <span class="text-xs text-gray-400">→ 병합</span>
                  </template>
                </div>

                <!-- 상태 표시 -->
                <span v-if="item.status === 'generating'" class="text-xs text-blue-600">⏳ 생성 중...</span>
                <span v-else-if="item.status === 'done'" class="text-xs text-green-600">✅ 완료</span>
                <span v-else-if="item.status === 'error'" class="text-xs text-red-600">❌ 오류</span>

                <!-- 액션 버튼 -->
                <div class="ml-auto flex items-center gap-2">
                  <button
                    :disabled="item.status === 'generating'"
                    class="rounded px-2.5 py-1 text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50"
                    :class="
                      item.status === 'done'
                        ? 'bg-green-600 text-white hover:bg-green-700'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    "
                    @click="generateTts(item)"
                  >
                    {{ item.status === 'done' ? '🔄 재생성' : '🔊 생성' }}
                  </button>
                  <button
                    v-if="item.audioUrl"
                    class="rounded bg-gray-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-gray-700"
                    @click="downloadAudio(item)"
                  >
                    ⬇ 다운로드
                  </button>
                </div>
              </div>

              <!-- 카드 바디 -->
              <div class="px-4 py-3">
                <p class="whitespace-pre-wrap text-xs leading-relaxed text-gray-700">{{ item.text }}</p>
                <div v-if="item.status === 'error'" class="mt-2 rounded bg-red-100 px-3 py-2 text-xs text-red-700">
                  {{ item.errorMsg }}
                </div>
                <div v-if="item.audioUrl" class="mt-3">
                  <audio :key="item.audioUrl" :src="item.audioUrl" controls class="h-8 w-full"></audio>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>
