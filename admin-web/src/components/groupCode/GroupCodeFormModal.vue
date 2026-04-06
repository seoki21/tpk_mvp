<!--
  그룹코드 등록/수정 모달 컴포넌트
  - editData가 null이면 등록 모드, 객체이면 수정 모드
  - FormModal 래퍼를 사용하여 모달 UI를 구성
  - 저장 시 스토어의 create 또는 update 액션을 호출
  - 삭제 시 ConfirmDialog로 확인 후 스토어의 remove 호출
-->
<script setup>
import { ref, watch, computed } from 'vue';
import FormModal from '@/components/common/FormModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';
import { useGroupCodeStore } from '@/stores/groupCode';
import { useToast } from '@/composables/useToast';

const store = useGroupCodeStore();
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

/** 모달 타이틀 (등록/수정에 따라 변경) */
const modalTitle = computed(() => (isEditMode.value ? '그룹 코드 수정' : '그룹 코드 등록'));

/* ========== 폼 데이터 ========== */
const form = ref({
  group_code: '',
  group_name: '',
  group_desc: '',
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
          group_name: props.editData.group_name || '',
          group_desc: props.editData.group_desc || ''
        };
      } else {
        /* 등록 모드: 빈 폼으로 초기화 */
        form.value = {
          group_code: '',
          group_name: '',
          group_desc: ''
        };
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
      await store.update(form.value.group_code, {
        group_name: form.value.group_name,
        group_desc: form.value.group_desc
      });
    } else {
      await store.create(form.value);
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
    await store.remove(form.value.group_code);
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
        <input
          v-model="form.group_code"
          type="text"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
          :readonly="isEditMode"
          :class="{ 'bg-gray-100': isEditMode }"
        />
      </div>

      <!-- 코드명 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700"> 코드명 </label>
        <input
          v-model="form.group_name"
          type="text"
          class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <!-- 코드설명 -->
      <div class="flex items-center">
        <label class="w-28 shrink-0 text-sm font-medium text-gray-700"> 코드설명 </label>
        <input
          v-model="form.group_desc"
          type="text"
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
