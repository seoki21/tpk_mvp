<!--
  시험 템플릿 등록/수정 모달 컴포넌트
  - editData가 null이면 등록 모드, 객체이면 수정 모드
  - 등록 모드: 복합 PK(시험종류/레벨/영역/문항번호) 모두 입력 가능
  - 수정 모드: PK는 읽기전용, 지문유형/문항유형만 수정 가능
  - 지문유형/문항유형 셀렉트박스는 tb_code에서 각 그룹코드로 조회한다.
-->
<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import FormModal from '@/components/common/FormModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import { useExamTemplateStore } from '@/stores/examTemplate';
import { useToast } from '@/composables/useToast';
import * as codeApi from '@/api/code';

const store = useExamTemplateStore();
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
const modalTitle = computed(() => (isEditMode.value ? '시험 템플릿 수정' : '시험 템플릿 등록'));

/* ========== 코드 목록 (셀렉트박스용) ========== */
const tpkTypeCodes = ref([]); // 시험종류 코드 목록
const tpkLevelCodes = ref([]); // 토픽레벨 코드 목록
const sectionCodes = ref([]); // 영역 코드 목록
const passageTypeCodes = ref([]); // 지문유형 코드 목록
const questionTypeCodes = ref([]); // 문항유형 코드 목록

/* ========== 폼 데이터 ========== */
const form = ref({
  tpk_type: '',
  tpk_level: '',
  section: '',
  question_no: '',
  passage_type: '',
  question_type: ''
});

/** 코드 목록 일괄 로드 */
async function loadCodes() {
  try {
    const [tpkTypeRes, tpkLevelRes, sectionRes, passageRes, questionRes] = await Promise.all([
      codeApi.getCodesByGroup('topik_type'),
      codeApi.getCodesByGroup('tpk_level'),
      codeApi.getCodesByGroup('section'),
      codeApi.getCodesByGroup('passage_type'),
      codeApi.getCodesByGroup('question_type')
    ]);
    tpkTypeCodes.value = tpkTypeRes.data || [];
    tpkLevelCodes.value = tpkLevelRes.data || [];
    sectionCodes.value = sectionRes.data || [];
    passageTypeCodes.value = passageRes.data || [];
    questionTypeCodes.value = questionRes.data || [];
  } catch (error) {
    console.error('[ExamTemplateFormModal] 코드 목록 로드 실패:', error);
  }
}

/** 모달이 열릴 때 코드 목록 로드 후 폼 데이터 초기화 */
watch(
  () => props.visible,
  async (newVal) => {
    if (newVal) {
      /* 모달이 열릴 때마다 코드 목록을 새로 로드 */
      await loadCodes();

      if (props.editData) {
        /* 수정 모드: 기존 데이터를 폼에 채움 */
        form.value = {
          tpk_type: props.editData.tpk_type ?? '',
          tpk_level: props.editData.tpk_level ?? '',
          section: props.editData.section ?? '',
          question_no: props.editData.question_no ?? '',
          passage_type: props.editData.passage_type ?? '',
          question_type: props.editData.question_type ?? ''
        };
      } else {
        /* 등록 모드: 빈 폼으로 초기화 */
        form.value = {
          tpk_type: '',
          tpk_level: '',
          section: '',
          question_no: '',
          passage_type: '',
          question_type: ''
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
  if (
    !form.value.tpk_type ||
    !form.value.tpk_level ||
    !form.value.section ||
    form.value.question_no === ''
  ) {
    toast.error('시험종류, 토픽레벨, 영역, 문항번호는 필수 입력입니다.');
    return;
  }
  try {
    if (isEditMode.value) {
      await store.update(
        props.editData.tpk_type,
        props.editData.tpk_level,
        props.editData.section,
        props.editData.question_no,
        {
          passage_type: form.value.passage_type || null,
          question_type: form.value.question_type || null
        }
      );
    } else {
      await store.create({
        tpk_type: Number(form.value.tpk_type),
        tpk_level: Number(form.value.tpk_level),
        section: Number(form.value.section),
        question_no: Number(form.value.question_no),
        passage_type: form.value.passage_type ? Number(form.value.passage_type) : null,
        question_type: form.value.question_type ? Number(form.value.question_type) : null
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
    await store.remove(
      props.editData.tpk_type,
      props.editData.tpk_level,
      props.editData.section,
      props.editData.question_no
    );
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

      <!-- 영역 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">영역</label>
        <select
          v-if="!isEditMode"
          v-model="form.section"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="c in sectionCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
        <input
          v-else
          :value="editData?.section_name"
          type="text"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <!-- 문항번호 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">문항번호</label>
        <input
          v-if="!isEditMode"
          v-model.number="form.question_no"
          type="number"
          min="1"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
        <input
          v-else
          :value="editData?.question_no"
          type="number"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <!-- 지문유형 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">지문유형</label>
        <select
          v-model="form.passage_type"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="c in passageTypeCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
      </div>

      <!-- 문항유형 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700">문항유형</label>
        <select
          v-model="form.question_type"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option v-for="c in questionTypeCodes" :key="c.code" :value="c.code">
            {{ c.code_name }}
          </option>
        </select>
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
