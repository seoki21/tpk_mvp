<!--
  연습문제 생성 요청 등록/수정 모달 컴포넌트
  - editData가 null이면 등록 모드, 객체이면 수정 모드
  - FormModal 래퍼를 사용하여 모달 UI를 구성
  - 저장 시 스토어의 create 또는 update 액션을 호출
-->
<script setup>
import { ref, watch, computed } from 'vue';
import FormModal from '@/components/common/FormModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import { usePracticeRequestStore } from '@/stores/practiceRequest';
import { useToast } from '@/composables/useToast';

const store = usePracticeRequestStore();
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

/** 수정 모드 여부 */
const isEditMode = computed(() => props.editData !== null);

/** 모달 타이틀 */
const modalTitle = computed(() =>
  isEditMode.value ? '연습문제 생성 요청 수정' : '연습문제 생성 요청'
);

/* ========== 폼 데이터 ========== */
const form = ref({
  exam_type: '',
  tpk_level: '',
  section: '',
  difficulty: '',
  question_count: 10,
  gen_method: ''
});

/** 모달이 열릴 때 폼 데이터를 초기화 */
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      if (props.editData) {
        /* 수정 모드: 기존 데이터를 폼에 채움 */
        form.value = {
          exam_type: String(props.editData.exam_type || ''),
          tpk_level: String(props.editData.tpk_level || ''),
          section: String(props.editData.section || ''),
          difficulty: String(props.editData.difficulty || ''),
          question_count: props.editData.question_count || 10,
          gen_method: String(props.editData.gen_method || '')
        };
      } else {
        /* 등록 모드: 빈 폼 */
        form.value = {
          exam_type: '',
          tpk_level: '',
          section: '',
          difficulty: '',
          question_count: 10,
          gen_method: ''
        };
      }
    }
  }
);

/* ========== 삭제 확인 다이얼로그 ========== */
const showConfirm = ref(false);

/** 저장 핸들러 — 필수 필드 검증 후 API 호출 */
async function handleSave() {
  if (!form.value.exam_type) {
    toast.warning('시험유형을 선택하세요.');
    return;
  }
  if (!form.value.tpk_level) {
    toast.warning('토픽레벨을 선택하세요.');
    return;
  }
  if (!form.value.section) {
    toast.warning('영역을 선택하세요.');
    return;
  }
  if (!form.value.question_count || form.value.question_count < 1) {
    toast.warning('문항수를 1 이상 입력하세요.');
    return;
  }

  try {
    if (isEditMode.value) {
      await store.update(props.editData.request_key, form.value);
    } else {
      await store.create(form.value);
    }
    toast.success('저장되었습니다.');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '저장에 실패했습니다.');
  }
}

/** 삭제 버튼 클릭 → 확인 다이얼로그 */
function handleDelete() {
  showConfirm.value = true;
}

/** 삭제 확인 후 실행 */
async function confirmDelete() {
  showConfirm.value = false;
  try {
    await store.remove(props.editData.request_key);
    toast.success('삭제되었습니다.');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '삭제에 실패했습니다.');
  }
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
      <!-- 시험유형 -->
      <div class="flex items-center">
        <label class="w-24 shrink-0 text-sm font-medium text-gray-700">시험유형</label>
        <select
          v-model="form.exam_type"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">선택하세요</option>
          <option v-for="opt in store.examTypeOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 토픽레벨 -->
      <div class="flex items-center">
        <label class="w-24 shrink-0 text-sm font-medium text-gray-700">토픽레벨</label>
        <select
          v-model="form.tpk_level"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">선택하세요</option>
          <option v-for="opt in store.tpkLevelOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 영역 -->
      <div class="flex items-center">
        <label class="w-24 shrink-0 text-sm font-medium text-gray-700">영역</label>
        <select
          v-model="form.section"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">선택하세요</option>
          <option v-for="opt in store.sectionOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 난이도 -->
      <div class="flex items-center">
        <label class="w-24 shrink-0 text-sm font-medium text-gray-700">난이도</label>
        <select
          v-model="form.difficulty"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">선택하세요</option>
          <option v-for="opt in store.difficultyOptions" :key="opt.code" :value="String(opt.code)">
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 구분선 -->
      <hr class="border-gray-300" />

      <!-- 문항수 -->
      <div class="flex items-center">
        <label class="w-24 shrink-0 text-sm font-medium text-gray-700">문항수</label>
        <input
          v-model.number="form.question_count"
          type="number"
          min="1"
          class="w-24 rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <!-- 생성방법 -->
      <div class="flex items-center">
        <label class="w-24 shrink-0 text-sm font-medium text-gray-700">생성방법</label>
        <div class="flex items-center gap-6">
          <label
            v-for="opt in store.genMethodOptions"
            :key="opt.code"
            class="flex cursor-pointer items-center gap-1.5 text-sm text-gray-700"
          >
            <input
              v-model="form.gen_method"
              type="radio"
              :value="String(opt.code)"
              class="text-blue-500 focus:ring-blue-500"
            />
            {{ opt.code_name }}
          </label>
        </div>
      </div>
    </div>
  </FormModal>

  <!-- 삭제 확인 다이얼로그 -->
  <ConfirmDialog
    :visible="showConfirm"
    message="삭제하시겠습니까?"
    @confirm="confirmDelete"
    @cancel="showConfirm = false"
  />
</template>
