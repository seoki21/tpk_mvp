<!--
  코드 목록 페이지
  - 서브 타이틀, 검색바(그룹코드 셀렉트박스 + 코드명 텍스트), 데이터 테이블, 페이지네이션으로 구성
  - 행 클릭 시 수정 모달, 등록 버튼 클릭 시 등록 모달을 표시
  - 마운트 시 그룹코드 전체 목록과 코드 페이징 목록을 조회한다.
-->
<script setup>
import { onMounted, computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useCodeStore } from '@/stores/code'
import { useGroupCodeStore } from '@/stores/groupCode'
import SearchBar from '@/components/common/SearchBar.vue'
import DataTable from '@/components/common/DataTable.vue'
import Pagination from '@/components/common/Pagination.vue'
import CodeFormModal from '@/components/code/CodeFormModal.vue'

const { t } = useI18n()
const codeStore = useCodeStore()
const groupCodeStore = useGroupCodeStore()

/* ========== 테이블 컬럼 정의 ========== */
const columns = computed(() => [
  { key: 'group_code', label: t('code.groupCode'), width: '140px' },
  { key: 'group_name', label: t('code.groupCodeName'), width: '140px', align: 'left' },
  { key: 'code', label: t('code.code'), width: '100px' },
  { key: 'code_name', label: t('code.codeName'), width: '180px', align: 'left' },
  { key: 'code_desc', label: t('code.codeDesc'), width: '240px', align: 'left' },
  { key: 'sort_order', label: t('code.sortOrder'), width: '100px' },
  { key: 'del_yn', label: t('code.delYn'), width: '100px' },
  { key: 'ins_user', label: t('code.insUser'), width: '120px' },
  { key: 'ins_date', label: t('code.insDate'), width: '180px' }
])

/* ========== 모달 상태 ========== */
const showModal = ref(false)
const editData = ref(null)

/** 조회 버튼 클릭 */
function handleSearch() {
  codeStore.page = 1
  codeStore.fetchList()
}

/** 등록 버튼 클릭 */
function handleRegister() {
  editData.value = null
  showModal.value = true
}

/** 행 클릭 → 수정 모달 열기 */
function handleRowClick(row) {
  editData.value = { ...row }
  showModal.value = true
}

/** 모달 닫기 */
function handleModalClose() {
  showModal.value = false
  editData.value = null
}

/** 저장/삭제 완료 후 모달 닫고 목록 새로고침 */
function handleSaved() {
  showModal.value = false
  editData.value = null
  codeStore.fetchList()
}

/** 페이지 변경 */
function handlePageChange(newPage) {
  codeStore.page = newPage
  codeStore.fetchList()
}

/** 페이지당 행 수 변경 */
function handlePageSizeChange(newSize) {
  codeStore.size = newSize
  codeStore.page = 1
  codeStore.fetchList()
}

/* ========== 초기 데이터 로드 ========== */
onMounted(() => {
  groupCodeStore.fetchAllGroupCodes()
  codeStore.fetchList()
})
</script>

<template>
  <div>
    <!-- 서브 타이틀 -->
    <h2 class="text-xl font-bold text-gray-800 mb-4">
      {{ t('code.title') }}
    </h2>

    <!-- 검색바 -->
    <SearchBar @search="handleSearch" @register="handleRegister">
      <!-- 그룹코드 셀렉트박스 -->
      <div class="flex items-center gap-2">
        <label class="text-sm font-medium text-gray-700 whitespace-nowrap">
          {{ t('code.groupCode') }}
        </label>
        <select
          v-model="codeStore.searchParams.group_code"
          class="border border-gray-300 rounded px-3 py-1.5 text-sm min-w-[160px]"
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
      </div>

      <!-- 코드명 텍스트 입력 -->
      <div class="flex items-center gap-2">
        <label class="text-sm font-medium text-gray-700 whitespace-nowrap">
          {{ t('code.codeName') }}
        </label>
        <input
          v-model="codeStore.searchParams.code_name"
          type="text"
          class="border border-gray-300 rounded px-3 py-1.5 text-sm min-w-[160px]"
          @keyup.enter="handleSearch"
        />
      </div>
    </SearchBar>

    <!-- 데이터 테이블 -->
    <DataTable
      :columns="columns"
      :data="codeStore.list"
      :loading="codeStore.loading"
      :page-size="codeStore.size"
      :total="codeStore.total"
      @row-click="handleRowClick"
      @update:page-size="handlePageSizeChange"
    />

    <!-- 페이지네이션 -->
    <Pagination
      :page="codeStore.page"
      :size="codeStore.size"
      :total="codeStore.total"
      @update:page="handlePageChange"
    />

    <!-- 등록/수정 모달 -->
    <CodeFormModal
      :visible="showModal"
      :edit-data="editData"
      @close="handleModalClose"
      @saved="handleSaved"
    />
  </div>
</template>
