<!--
  시험일정 등록/수정 모달 컴포넌트
  - editData가 null이면 등록 모드, 객체이면 수정 모드
  - 등록 모드: 시험종류/회차 입력 + 지역별 시험일 행 추가
  - 수정 모드: 시험종류/회차는 읽기전용, 지역별 시험일만 수정 가능
  - [+ 지역 추가] 버튼으로 location 행을 동적으로 추가/삭제한다.
-->
<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import FormModal from '@/components/common/FormModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import { useExamScheduleStore } from '@/stores/examSchedule';
import { useToast } from '@/composables/useToast';
import * as codeApi from '@/api/code';

const store = useExamScheduleStore();
const toast = useToast();

const props = defineProps({
  /** 모달 표시 여부 */
  visible: { type: Boolean, required: true },
  /** 수정 대상 데이터 (null이면 등록 모드) */
  editData: { type: Object, default: null }
});

const emit = defineEmits(['close', 'saved']);

/** 수정 모드 여부 */
const isEditMode = computed(() => props.editData !== null);

/** 모달 타이틀 */
const modalTitle = computed(() => (isEditMode.value ? '시험일정 수정' : '시험일정 등록'));

/* ========== 코드 목록 ========== */
const tpkTypeCodes = ref([]); // 시험종류 코드 목록
const examRegionCodes = ref([]); // 지역 코드 목록

/** 코드 목록 로드 */
async function loadCodes() {
  try {
    const [tpkTypeRes, regionRes] = await Promise.all([
      codeApi.getCodesByGroup('topik_type'),
      codeApi.getCodesByGroup('exam_region')
    ]);
    tpkTypeCodes.value = tpkTypeRes.data || [];
    examRegionCodes.value = regionRes.data || [];
  } catch (error) {
    console.error('[ExamScheduleFormModal] 코드 목록 로드 실패:', error);
  }
}

/* ========== 폼 데이터 ========== */
const form = ref({
  tpk_type: '',
  round: ''
});

/** 지역별 시험일 행 목록 */
const locationRows = ref([]);

/** 빈 location 행 생성 */
function newLocationRow() {
  return { exam_region: '', test_date: '' };
}

/** location 행 추가 */
function addLocationRow() {
  locationRows.value.push(newLocationRow());
}

/** location 행 삭제 */
function removeLocationRow(index) {
  locationRows.value.splice(index, 1);
}

/** 모달이 열릴 때 폼 초기화 */
watch(
  () => props.visible,
  async (newVal) => {
    if (newVal) {
      await loadCodes();

      if (props.editData) {
        /* 수정 모드: 기존 데이터 채움 */
        form.value = {
          tpk_type: props.editData.tpk_type ?? '',
          round: props.editData.round ?? ''
        };
        /* location 목록을 단건 조회로 재로드 */
        try {
          const res = await store.fetchDetail(props.editData.exam_key);
          locationRows.value = (res.data?.locations || []).map((l) => ({
            exam_region: l.exam_region,
            test_date: l.test_date || ''
          }));
        } catch {
          locationRows.value = [];
        }
      } else {
        /* 등록 모드: 초기화 */
        form.value = { tpk_type: '', round: '' };
        locationRows.value = [newLocationRow()];
      }
    }
  }
);

onMounted(() => {
  loadCodes();
});

/* ========== 삭제 확인 다이얼로그 ========== */
const showConfirm = ref(false);

/** 저장 핸들러 */
async function handleSave() {
  if (!isEditMode.value && (!form.value.tpk_type || form.value.round === '')) {
    toast.error('시험종류와 회차는 필수 입력입니다.');
    return;
  }
  /* 지역이 하나도 없으면 경고 */
  const validLocs = locationRows.value.filter((r) => r.exam_region !== '');
  if (validLocs.length === 0) {
    toast.error('지역별 시험일을 최소 1개 이상 입력해주세요.');
    return;
  }

  try {
    if (isEditMode.value) {
      await store.update(props.editData.exam_key, {
        locations: validLocs.map((r) => ({
          exam_region: Number(r.exam_region),
          test_date: r.test_date || null
        }))
      });
    } else {
      await store.create({
        tpk_type: Number(form.value.tpk_type),
        round: Number(form.value.round),
        locations: validLocs.map((r) => ({
          exam_region: Number(r.exam_region),
          test_date: r.test_date || null
        }))
      });
    }
    toast.success('저장되었습니다.');
    emit('saved');
  } catch (error) {
    toast.error(error?.response?.data?.detail || '오류가 발생했습니다.');
  }
}

/** 삭제 버튼 클릭 */
function handleDelete() {
  showConfirm.value = true;
}

/** 삭제 확인 */
async function confirmDelete() {
  showConfirm.value = false;
  try {
    await store.remove(props.editData.exam_key);
    toast.success('삭제되었습니다.');
    emit('saved');
  } catch (error) {
    toast.error(error?.response?.data?.detail || '오류가 발생했습니다.');
  }
}

function cancelDelete() {
  showConfirm.value = false;
}
</script>

<template>
  <FormModal
    :visible="visible"
    :title="modalTitle"
    :show-delete="isEditMode"
    @close="emit('close')"
    @save="handleSave"
    @delete="handleDelete"
  >
    <div class="space-y-4">
      <!-- 시험종류 -->
      <div class="flex items-center">
        <label class="w-24 shrink-0 text-sm font-medium text-gray-700">시험종류</label>
        <select
          v-if="!isEditMode"
          v-model="form.tpk_type"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="c in tpkTypeCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
        <input
          v-else
          :value="editData?.tpk_type_name"
          type="text"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <!-- 회차 -->
      <div class="flex items-center">
        <label class="w-24 shrink-0 text-sm font-medium text-gray-700">회차</label>
        <input
          v-if="!isEditMode"
          v-model.number="form.round"
          type="number"
          min="1"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <input
          v-else
          :value="editData?.round"
          type="number"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <hr class="border-gray-200" />

      <!-- 지역별 시험일 -->
      <div>
        <div class="mb-2 text-sm font-medium text-gray-700">지역별 시험일</div>
        <div class="space-y-2">
          <div v-for="(row, idx) in locationRows" :key="idx" class="flex items-center gap-2">
            <!-- 지역 셀렉트박스 -->
            <select
              v-model="row.exam_region"
              class="w-40 rounded border border-gray-300 px-3 py-2 text-sm"
            >
              <option value=""></option>
              <option v-for="c in examRegionCodes" :key="c.code" :value="c.code">
                {{ c.code_name }}
              </option>
            </select>
            <!-- 시험일 날짜 입력 -->
            <input
              v-model="row.test_date"
              type="date"
              class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
            />
            <!-- 행 삭제 버튼 -->
            <button
              type="button"
              class="px-1 text-lg leading-none text-gray-400 hover:text-red-500"
              @click="removeLocationRow(idx)"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- 지역 추가 버튼 -->
        <button
          type="button"
          class="mt-3 flex w-full items-center justify-center gap-1 rounded border border-dashed border-blue-400 px-3 py-1.5 text-sm text-blue-500 hover:bg-blue-50"
          @click="addLocationRow"
        >
          + 지역 추가
        </button>
      </div>
    </div>
  </FormModal>

  <!-- 삭제 확인 다이얼로그 -->
  <ConfirmDialog
    :visible="showConfirm"
    message="삭제하시겠습니까?"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
