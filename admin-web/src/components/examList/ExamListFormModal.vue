<!--
  시험문항 등록/수정 모달 컴포넌트
  - editData가 null이면 등록 모드, 객체이면 수정 모드
  - 시험유형, 토픽레벨, 영역 셀렉트박스는 examList 스토어의 코드 옵션에서 가져온다.
  - 등록 모드에서는 exam_key가 자동 생성(SERIAL)이므로 표시하지 않는다.
  - 수정 모드에서는 exam_key를 읽기 전용으로 표시한다.
-->
<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import FormModal from '@/components/common/FormModal.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { useExamListStore } from '@/stores/examList'

const { t } = useI18n()
const store = useExamListStore()

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
})

const emit = defineEmits(['close', 'saved'])

/** 수정 모드 여부 판별 */
const isEditMode = computed(() => props.editData !== null)

/** 모달 타이틀 (등록/수정에 따라 변경) */
const modalTitle = computed(() =>
  isEditMode.value ? t('examList.editTitle') : t('examList.createTitle')
)

/* ========== 폼 데이터 ========== */
const form = ref({
  exam_key: '',
  exam_year: '',
  exam_type: '',
  topic_level: '',
  round: '',
  section: '',
  del_yn: 'N'
})

/** 모달이 열릴 때 폼 데이터를 초기화 */
watch(() => props.visible, (newVal) => {
  if (newVal) {
    if (props.editData) {
      /* 수정 모드: 기존 데이터를 폼에 채움 */
      form.value = {
        exam_key: props.editData.exam_key || '',
        exam_year: props.editData.exam_year || '',
        exam_type: props.editData.exam_type || '',
        topic_level: props.editData.topic_level || '',
        round: props.editData.round ?? '',
        section: props.editData.section || '',
        del_yn: props.editData.del_yn || 'N'
      }
    } else {
      /* 등록 모드: 빈 폼으로 초기화 */
      form.value = {
        exam_key: '',
        exam_year: '',
        exam_type: '',
        topic_level: '',
        round: '',
        section: '',
        del_yn: 'N'
      }
    }

    /* 코드 옵션이 비어 있으면 가져옴 */
    if (store.examTypeOptions.length === 0) {
      store.fetchCodeOptions()
    }
  }
})

/* ========== 삭제 확인 다이얼로그 ========== */
const showConfirm = ref(false)

/** 저장 핸들러 */
async function handleSave() {
  try {
    if (isEditMode.value) {
      await store.update(form.value.exam_key, {
        exam_year: form.value.exam_year,
        exam_type: form.value.exam_type,
        topic_level: form.value.topic_level,
        round: form.value.round,
        section: form.value.section,
        del_yn: form.value.del_yn
      })
    } else {
      await store.create({
        exam_year: form.value.exam_year,
        exam_type: form.value.exam_type,
        topic_level: form.value.topic_level,
        round: form.value.round,
        section: form.value.section
      })
    }
    alert(t('common.saveSuccess'))
    emit('saved')
  } catch (error) {
    alert(error.detail || t('common.error'))
  }
}

/** 삭제 버튼 클릭 → 확인 다이얼로그 표시 */
function handleDelete() {
  showConfirm.value = true
}

/** 삭제 확인 후 실행 */
async function confirmDelete() {
  showConfirm.value = false
  try {
    await store.remove(form.value.exam_key)
    alert(t('common.deleteSuccess'))
    emit('saved')
  } catch (error) {
    alert(error.detail || t('common.error'))
  }
}

/** 삭제 취소 */
function cancelDelete() {
  showConfirm.value = false
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
      <!-- 시험키 (수정 모드에서만 읽기 전용 표시) -->
      <div v-if="isEditMode" class="flex items-center">
        <label class="w-28 text-sm font-medium text-gray-700 shrink-0">
          {{ t('examList.examKey') }}
        </label>
        <input
          :value="form.exam_key"
          type="text"
          readonly
          class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm bg-gray-100"
        />
      </div>

      <!-- 년도 -->
      <div class="flex items-center">
        <label class="w-28 text-sm font-medium text-gray-700 shrink-0">
          {{ t('examList.examYear') }}
        </label>
        <input
          v-model="form.exam_year"
          type="text"
          maxlength="4"
          class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
        />
      </div>

      <!-- 시험유형 -->
      <div class="flex items-center">
        <label class="w-28 text-sm font-medium text-gray-700 shrink-0">
          {{ t('examList.examType') }}
        </label>
        <select
          v-model="form.exam_type"
          class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option
            v-for="opt in store.examTypeOptions"
            :key="opt.code"
            :value="opt.code"
          >
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 토픽레벨 -->
      <div class="flex items-center">
        <label class="w-28 text-sm font-medium text-gray-700 shrink-0">
          {{ t('examList.topicLevel') }}
        </label>
        <select
          v-model="form.topic_level"
          class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option
            v-for="opt in store.tpkLevelOptions"
            :key="opt.code"
            :value="opt.code"
          >
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 회차 -->
      <div class="flex items-center">
        <label class="w-28 text-sm font-medium text-gray-700 shrink-0">
          {{ t('examList.round') }}
        </label>
        <input
          v-model.number="form.round"
          type="number"
          class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
        />
      </div>

      <!-- 영역 -->
      <div class="flex items-center">
        <label class="w-28 text-sm font-medium text-gray-700 shrink-0">
          {{ t('examList.section') }}
        </label>
        <select
          v-model="form.section"
          class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
        >
          <option value=""></option>
          <option
            v-for="opt in store.sectionOptions"
            :key="opt.code"
            :value="opt.code"
          >
            {{ opt.code_name }}
          </option>
        </select>
      </div>

      <!-- 삭제여부 (수정 모드에서만 표시) -->
      <div v-if="isEditMode" class="flex items-center">
        <label class="w-28 text-sm font-medium text-gray-700 shrink-0">
          {{ t('examList.delYn') }}
        </label>
        <select
          v-model="form.del_yn"
          class="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
        >
          <option value="N">N</option>
          <option value="Y">Y</option>
        </select>
      </div>
    </div>
  </FormModal>

  <!-- 삭제 확인 다이얼로그 -->
  <ConfirmDialog
    :visible="showConfirm"
    :message="t('common.deleteConfirm')"
    @confirm="confirmDelete"
    @cancel="cancelDelete"
  />
</template>
