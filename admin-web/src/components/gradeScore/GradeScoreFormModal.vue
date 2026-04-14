<!--
  등급 등록/수정 모달 컴포넌트
  - editData가 null이면 등록 모드, 객체이면 수정 모드
  - 등록 모드: 복합 PK(시험종류/레벨/등급)와 점수 모두 입력 가능
  - 수정 모드: PK(시험종류/레벨/등급)는 읽기전용, 점수 범위/총점만 수정 가능
  - 시험종류/레벨 셀렉트박스는 tb_code에서 각 그룹코드로 조회한다.
-->
<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import FormModal from '@/components/common/FormModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import { useGradeScoreStore } from '@/stores/gradeScore';
import { useToast } from '@/composables/useToast';
import * as codeApi from '@/api/code';

const store = useGradeScoreStore();
const toast = useToast();

const props = defineProps({
  /** 모달 표시 여부 */
  visible: {
    type: Boolean,
    required: true
  },
  /** 수정 대상 데이터 (null이면 등록 모드) */
  editData: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['close', 'saved']);

/** 수정 모드 여부 판별 */
const isEditMode = computed(() => props.editData !== null);

/** 모달 타이틀 */
const modalTitle = computed(() => (isEditMode.value ? '등급 수정' : '등급 등록'));

/* ========== 코드 목록 (셀렉트박스용) ========== */
const tpkTypeCodes = ref([]); // 시험종류 코드 목록
const tpkLevelCodes = ref([]); // 토픽레벨 코드 목록
const tpkGradeCodes = ref([]); // 등급 코드 목록

/* ========== 폼 데이터 ========== */
const form = ref({
  tpk_type: '',
  tpk_level: '',
  tpk_grade: '',
  min_score: '',
  max_score: '',
  total_score: ''
});

/** 코드 목록 로드 */
async function loadCodes() {
  try {
    const [tpkTypeRes, tpkLevelRes, tpkGradeRes] = await Promise.all([
      codeApi.getCodesByGroup('topik_type'),
      codeApi.getCodesByGroup('tpk_level'),
      codeApi.getCodesByGroup('tpk_grade')
    ]);
    tpkTypeCodes.value = tpkTypeRes.data || [];
    tpkLevelCodes.value = tpkLevelRes.data || [];
    tpkGradeCodes.value = tpkGradeRes.data || [];
  } catch (error) {
    console.error('[GradeScoreFormModal] 코드 목록 로드 실패:', error);
  }
}

/** 모달이 열릴 때 코드 목록 로드 후 폼 데이터 초기화 */
watch(
  () => props.visible,
  async (newVal) => {
    if (newVal) {
      await loadCodes();

      if (props.editData) {
        /* 수정 모드: 기존 데이터를 폼에 채움 */
        form.value = {
          tpk_type: props.editData.tpk_type ?? '',
          tpk_level: props.editData.tpk_level ?? '',
          tpk_grade: props.editData.tpk_grade ?? '',
          min_score: props.editData.min_score ?? '',
          max_score: props.editData.max_score ?? '',
          total_score: props.editData.total_score ?? ''
        };
      } else {
        /* 등록 모드: 빈 폼으로 초기화 */
        form.value = {
          tpk_type: '',
          tpk_level: '',
          tpk_grade: '',
          min_score: '',
          max_score: '',
          total_score: ''
        };
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
  /* 필수 입력 검증 */
  if (!form.value.tpk_type || !form.value.tpk_level || form.value.tpk_grade === '') {
    toast.error('시험종류, 토픽레벨, 등급은 필수 입력입니다.');
    return;
  }
  if (form.value.min_score === '' || form.value.max_score === '' || form.value.total_score === '') {
    toast.error('최소점수, 최대점수, 총점은 필수 입력입니다.');
    return;
  }

  try {
    if (isEditMode.value) {
      /* 수정: 점수 범위/총점만 전송 */
      await store.update(
        props.editData.tpk_type,
        props.editData.tpk_level,
        props.editData.tpk_grade,
        {
          min_score: Number(form.value.min_score),
          max_score: Number(form.value.max_score),
          total_score: Number(form.value.total_score)
        }
      );
    } else {
      /* 등록: 전체 필드 전송 */
      await store.create({
        tpk_type: Number(form.value.tpk_type),
        tpk_level: Number(form.value.tpk_level),
        tpk_grade: Number(form.value.tpk_grade),
        min_score: Number(form.value.min_score),
        max_score: Number(form.value.max_score),
        total_score: Number(form.value.total_score)
      });
    }
    toast.success('저장되었습니다.');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다.');
  }
}

/** 삭제 버튼 클릭 → 확인 다이얼로그 표시 */
function handleDelete() {
  showConfirm.value = true;
}

/** 삭제 확인 후 실행 */
async function confirmDelete() {
  showConfirm.value = false;
  try {
    await store.remove(props.editData.tpk_type, props.editData.tpk_level, props.editData.tpk_grade);
    toast.success('삭제되었습니다.');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다.');
  }
}

/** 삭제 취소 */
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
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">시험종류</label>
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

      <!-- 토픽레벨 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">토픽레벨</label>
        <select
          v-if="!isEditMode"
          v-model="form.tpk_level"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="c in tpkLevelCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
        <input
          v-else
          :value="editData?.tpk_level_name"
          type="text"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <!-- 등급 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">등급</label>
        <select
          v-if="!isEditMode"
          v-model="form.tpk_grade"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="c in tpkGradeCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
        <input
          v-else
          :value="editData?.tpk_grade_name"
          type="text"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <!-- 구분선 -->
      <hr class="border-gray-200" />

      <!-- 최소 점수 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">최소 점수</label>
        <input
          v-model.number="form.min_score"
          type="number"
          min="0"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <!-- 최대 점수 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">최대 점수</label>
        <input
          v-model.number="form.max_score"
          type="number"
          min="0"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <!-- 총점 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">총점</label>
        <input
          v-model.number="form.total_score"
          type="number"
          min="0"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
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
