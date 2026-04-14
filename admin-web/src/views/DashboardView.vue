<!--
  관리자 대시보드 페이지
  - 상단: 요약 카드 4개 (사용자, 시험, 문항, API 호출)
  - 중단: 시험/문제 현황 (레벨별/영역별 분포, 피드백 생성률) + 학습 이력 (준비 중)
  - 하단: API 토큰 사용 이력 (일별/주별/월별 차트 + 최근 호출 테이블 + 관리 콘솔 링크)
-->
<script setup>
import { onMounted, ref } from 'vue';
import { Bar, Doughnut, Line } from 'vue-chartjs';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import * as dashboardApi from '@/api/dashboard';

/* Chart.js 컴포넌트 등록 */
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

/* ========== 상태 ========== */
const summary = ref(null);
const examStats = ref(null);
const apiUsage = ref(null);
const apiPeriod = ref('daily');
const loading = ref(true);

/* ========== 데이터 로드 ========== */
async function fetchAll() {
  loading.value = true;
  try {
    const [sumRes, examRes, apiRes] = await Promise.all([
      dashboardApi.getSummary(),
      dashboardApi.getExamStats(),
      dashboardApi.getApiUsage(apiPeriod.value)
    ]);
    summary.value = sumRes.data;
    examStats.value = examRes.data;
    apiUsage.value = apiRes.data;
  } catch (error) {
    console.error('[Dashboard] 데이터 로드 실패:', error);
  } finally {
    loading.value = false;
  }
}

/** API 사용량 기간 변경 */
async function changeApiPeriod(period) {
  apiPeriod.value = period;
  try {
    const res = await dashboardApi.getApiUsage(period);
    apiUsage.value = res.data;
  } catch (error) {
    console.error('[Dashboard] API 사용량 조회 실패:', error);
  }
}

/* ========== 차트 데이터 생성 ========== */

/** 레벨별 시험 수 바 차트 데이터 */
function getLevelChartData() {
  if (!examStats.value?.level_distribution?.length) return null;
  const dist = examStats.value.level_distribution;
  return {
    labels: dist.map((d) => d.label),
    datasets: [
      {
        label: '시험 수',
        data: dist.map((d) => d.count),
        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
      }
    ]
  };
}

/** 영역별 문항 수 도넛 차트 데이터 */
function getSectionChartData() {
  if (!examStats.value?.section_distribution?.length) return null;
  const dist = examStats.value.section_distribution;
  return {
    labels: dist.map((d) => d.label),
    datasets: [
      {
        data: dist.map((d) => d.count),
        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
      }
    ]
  };
}

/** API 토큰 사용량 라인 차트 데이터 */
function getApiChartData() {
  if (!apiUsage.value?.chart_data?.length) return null;
  const data = apiUsage.value.chart_data;
  /* 날짜별로 그룹핑 */
  const dateMap = {};
  data.forEach((d) => {
    if (!dateMap[d.date]) dateMap[d.date] = { input: 0, output: 0, cost: 0 };
    dateMap[d.date].input += d.input_tokens;
    dateMap[d.date].output += d.output_tokens;
    dateMap[d.date].cost += d.cost_usd;
  });
  const dates = Object.keys(dateMap).sort();
  return {
    labels: dates.map((d) => d.substring(5)) /* MM-DD 형식 */,
    datasets: [
      {
        label: 'Input Tokens',
        data: dates.map((d) => dateMap[d].input),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.1)',
        fill: true,
        tension: 0.3
      },
      {
        label: 'Output Tokens',
        data: dates.map((d) => dateMap[d].output),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16,185,129,0.1)',
        fill: true,
        tension: 0.3
      }
    ]
  };
}

/** 차트 공통 옵션 */
const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } }
};
const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'bottom' } }
};
const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'top' } },
  scales: { y: { beginAtZero: true } }
};

/** 기간별 총 비용 합계 */
function getTotalCost() {
  if (!apiUsage.value?.provider_summary?.length) return '0.000000';
  return apiUsage.value.provider_summary.reduce((sum, p) => sum + p.cost_usd, 0).toFixed(6);
}

onMounted(fetchAll);
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-xl font-bold text-gray-800">대시보드</h2>

    <!-- 로딩 -->
    <div v-if="loading" class="flex h-40 items-center justify-center text-gray-400">
      데이터 로딩 중...
    </div>

    <template v-else>
      <!-- ========== 상단 요약 카드 ========== -->
      <div class="grid grid-cols-4 gap-4">
        <div class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-gray-500">총 사용자</p>
          <p class="mt-1 text-2xl font-bold text-gray-800">{{ summary?.total_users ?? '-' }}</p>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-gray-500">등록 시험</p>
          <p class="mt-1 text-2xl font-bold text-gray-800">{{ summary?.total_exams ?? '-' }}</p>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-gray-500">등록 문항</p>
          <p class="mt-1 text-2xl font-bold text-gray-800">{{ summary?.total_questions ?? '-' }}</p>
        </div>
        <div class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <p class="text-sm text-gray-500">금월 API 호출</p>
          <p class="mt-1 text-2xl font-bold text-blue-600">
            {{ summary?.monthly_api_calls ?? '-' }}
          </p>
        </div>
      </div>

      <!-- ========== 중단: 시험/문제 현황 + 학습 이력 ========== -->
      <div class="grid grid-cols-2 gap-4">
        <!-- 시험/문제 현황 -->
        <div class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <h3 class="mb-4 font-medium text-gray-700">시험/문제 현황</h3>

          <div class="grid grid-cols-2 gap-4">
            <!-- 레벨별 시험 수 -->
            <div>
              <p class="mb-2 text-sm text-gray-500">레벨별 시험 수</p>
              <div v-if="getLevelChartData()" class="h-[160px]">
                <Bar :data="getLevelChartData()" :options="barOptions" />
              </div>
              <p v-else class="text-sm text-gray-300">데이터 없음</p>
            </div>

            <!-- 영역별 문항 수 -->
            <div>
              <p class="mb-2 text-sm text-gray-500">영역별 문항 수</p>
              <div v-if="getSectionChartData()" class="h-[160px]">
                <Doughnut :data="getSectionChartData()" :options="doughnutOptions" />
              </div>
              <p v-else class="text-sm text-gray-300">데이터 없음</p>
            </div>
          </div>

          <!-- 피드백 생성률 -->
          <div v-if="examStats" class="mt-4">
            <p class="mb-1 text-sm text-gray-500">
              피드백 생성률 ({{ examStats.feedback_done }}/{{ examStats.feedback_total }})
            </p>
            <div class="h-2.5 w-full rounded-full bg-gray-200">
              <div
                class="h-2.5 rounded-full bg-blue-500"
                :style="{ width: examStats.feedback_rate + '%' }"
              ></div>
            </div>
            <p class="mt-1 text-right text-xs text-gray-500">{{ examStats.feedback_rate }}%</p>
          </div>
        </div>

        <!-- 사용자 학습 이력 (준비 중) -->
        <div class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <h3 class="mb-4 font-medium text-gray-700">사용자 학습 이력</h3>
          <div class="flex h-[220px] items-center justify-center text-gray-300">준비 중</div>
        </div>
      </div>

      <!-- ========== 하단: API 토큰 사용 이력 ========== -->
      <div class="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-center justify-between">
          <h3 class="font-medium text-gray-700">API 토큰 사용 이력</h3>
          <div class="flex items-center gap-2">
            <!-- 기간 선택 -->
            <div class="flex gap-1">
              <button
                v-for="p in [
                  { key: 'daily', label: '일별' },
                  { key: 'weekly', label: '주별' },
                  { key: 'monthly', label: '월별' }
                ]"
                :key="p.key"
                class="rounded px-3 py-1 text-xs transition-colors"
                :class="
                  apiPeriod === p.key
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                "
                @click="changeApiPeriod(p.key)"
              >
                {{ p.label }}
              </button>
            </div>
            <!-- 관리 콘솔 링크 -->
            <div v-if="apiUsage?.console_links" class="ml-2 flex gap-1">
              <a
                :href="apiUsage.console_links.claude"
                target="_blank"
                class="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
              >
                Anthropic 콘솔
              </a>
              <a
                :href="apiUsage.console_links.gemini"
                target="_blank"
                class="rounded border border-gray-300 px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
              >
                Google AI Studio
              </a>
            </div>
          </div>
        </div>

        <!-- 프로바이더별 합계 카드 + 총 비용 -->
        <div class="mb-4 flex gap-3">
          <div
            v-for="ps in apiUsage?.provider_summary || []"
            :key="ps.ai_provider"
            class="flex-1 rounded border border-gray-100 bg-gray-50 px-4 py-3"
          >
            <p class="text-xs font-medium text-gray-500">{{ ps.ai_provider }}</p>
            <p class="text-sm">
              <span class="font-semibold text-gray-700">{{ ps.call_count }}회</span>
              <span class="ml-2 text-gray-400">
                In {{ (ps.input_tokens / 1000).toFixed(1) }}K / Out
                {{ (ps.output_tokens / 1000).toFixed(1) }}K
              </span>
            </p>
            <p class="text-xs text-green-600">${{ ps.cost_usd.toFixed(4) }}</p>
          </div>
          <div class="flex-1 rounded border border-blue-100 bg-blue-50 px-4 py-3">
            <p class="text-xs font-medium text-blue-500">총 비용 (USD)</p>
            <p class="text-lg font-bold text-blue-700">${{ getTotalCost() }}</p>
          </div>
        </div>

        <!-- 토큰 사용량 라인 차트 -->
        <div v-if="getApiChartData()" class="mb-4 h-[200px]">
          <Line :data="getApiChartData()" :options="lineOptions" />
        </div>
        <p v-else class="mb-4 text-center text-sm text-gray-300">API 사용 이력이 없습니다.</p>

        <!-- 최근 API 호출 테이블 -->
        <div v-if="apiUsage?.recent_calls?.length" class="overflow-x-auto">
          <table class="w-full text-left text-sm">
            <thead class="border-b border-gray-200 text-xs text-gray-500">
              <tr>
                <th class="pb-2">일시</th>
                <th class="pb-2">유형</th>
                <th class="pb-2">프로바이더</th>
                <th class="pb-2">모델</th>
                <th class="pb-2 text-right">Input</th>
                <th class="pb-2 text-right">Output</th>
                <th class="pb-2 text-right">비용(USD)</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in apiUsage.recent_calls"
                :key="c.usage_key"
                class="border-b border-gray-100"
              >
                <td class="py-1.5 text-gray-600">{{ c.ins_date }}</td>
                <td class="py-1.5">{{ c.api_type }}</td>
                <td class="py-1.5">{{ c.ai_provider }}</td>
                <td class="py-1.5 text-xs text-gray-400">{{ c.model_name }}</td>
                <td class="py-1.5 text-right">{{ c.input_tokens?.toLocaleString() }}</td>
                <td class="py-1.5 text-right">{{ c.output_tokens?.toLocaleString() }}</td>
                <td class="py-1.5 text-right text-green-600">${{ c.cost_usd.toFixed(6) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
