<!--
  코드 등록/수정 모달 컴포넌트
  - editData가 null이면 등록 모드, 객체이면 수정 모드
  - 그룹코드 셀렉트박스는 groupCode 스토어의 allGroupCodes에서 가져온다.
  - 등록 모드에서는 group_code과 code가 편집 가능, 수정 모드에서는 읽기 전용 (PK이므로)
-->
<script setup>
import { ref, watch, computed } from 'vue';
import FormModal from '@/components/common/FormModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import { useCodeStore } from '@/stores/code';
import { useGroupCodeStore } from '@/stores/groupCode';
import { useToast } from '@/composables/useToast';

const codeStore = useCodeStore();
const groupCodeStore = useGroupCodeStore();
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
const modalTitle = computed(() => (isEditMode.value ? '코드 수정' : '코드 등록'));

/* ========== 폼 데이터 ========== */
const form = ref({
  group_code: '',
  code: '',
  code_name: '',
  code_desc: '',
  sort_order: 0
});

/** 모달이 열릴 때 폼 데이터를 초기화 */
watch(
  () => props.visible,
  (newVal) => {
    if (newVal) {
      if (props.editData) {
        /* 수정 모드: 기존 데이터를 폼에 채움 */
        form.value = {
          group_code: props.editData.group_code || '',
          code: props.editData.code || '',
          code_name: props.editData.code_name || '',
          code_desc: props.editData.code_desc || '',
          sort_order: props.editData.sort_order ?? 0
        };
      } else {
        /* 등록 모드: 빈 폼으로 초기화 */
        form.value = {
          group_code: '',
          code: '',
          code_name: '',
          code_desc: '',
          sort_order: 0
        };
      }

      /* 그룹코드 목록이 비어 있으면 가져옴 */
      if (groupCodeStore.allGroupCodes.length === 0) {
        groupCodeStore.fetchAllGroupCodes();
      }
    }
  }
);

/* ========== 삭제 확인 다이얼로그 ========== */
const showConfirm = ref(false);

/** 저장 핸들러 */
async function handleSave() {
  try {
    if (isEditMode.value) {
      await codeStore.update(form.value.group_code, form.value.code, {
        code_name: form.value.code_name,
        code_desc: form.value.code_desc,
        sort_order: form.value.sort_order
      });
    } else {
      /* 등록 모드: code는 서버에서 자동채번하므로 전송하지 않음 */
      const { code, ...createData } = form.value;
      await codeStore.create(createData);
    }
    toast.success('저장되었습니다');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다');
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
    await codeStore.remove(form.value.group_code, form.value.code);
    toast.success('삭제되었습니다');
    emit('saved');
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다');
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
      <!-- 그룹코드 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700"> 그룹코드 </label>
        <select
          v-if="!isEditMode"
          v-model="form.group_code"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option
            v-for="gc in groupCodeStore.allGroupCodes"
            :key="gc.group_code"
            :value="gc.group_code"
          >
            {{ gc.group_code }} - {{ gc.group_name }}
          </option>
        </select>
        <input
          v-else
          :value="form.group_code"
          type="text"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <!-- 코드 (수정 모드에서만 읽기전용 표시, 등록 모드에서는 서버 자동채번이므로 숨김) -->
      <div v-if="isEditMode" class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700"> 코드 </label>
        <input
          :value="form.code"
          type="number"
          readonly
          class="flex-1 rounded border border-gray-300 bg-gray-100 px-3 py-2 text-sm"
        />
      </div>

      <!-- 코드명 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700"> 코드명 </label>
        <input
          v-model="form.code_name"
          type="text"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <!-- 코드설명 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700"> 코드설명 </label>
        <input
          v-model="form.code_desc"
          type="text"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <!-- 소팅순서 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700"> 소팅순서 </label>
        <input
          v-model.number="form.sort_order"
          type="number"
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
