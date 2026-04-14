<!--
  관리자 관리 페이지
  - SUPER 권한이 없는 경우 접근 제한 메시지를 표시한다.
  - 관리자 목록을 테이블로 표시하고, 등록/수정/삭제 기능을 제공한다.
-->
<script setup>
import { onMounted, ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useToast } from '@/composables/useToast';
import * as adminApi from '@/api/admin';
import SearchBar from '@/components/common/SearchBar.vue';
import DataTable from '@/components/common/DataTable.vue';
import Pagination from '@/components/common/Pagination.vue';
import FormModal from '@/components/common/FormModal.vue';
import ConfirmDialog from '@/components/common/ConfirmDialog.vue';

const authStore = useAuthStore();
const toast = useToast();

/* ========== 테이블 컬럼 정의 ========== */
const columns = [
  { key: 'admin_id', label: '관리자 ID', width: '150px', align: 'left' },
  { key: 'admin_desc', label: '설명', width: '200px', align: 'left' },
  { key: 'roles', label: '권한', width: '120px' },
  { key: 'del_yn', label: '삭제여부', width: '100px' },
  { key: 'ins_user', label: '생성자', width: '120px' },
  { key: 'ins_date', label: '생성시간', width: '180px' }
];

/* ========== 목록 상태 ========== */
const list = ref([]);
const total = ref(0);
const page = ref(1);
const size = ref(20);
const loading = ref(false);

/* ========== 모달 상태 ========== */
const showModal = ref(false);
const editData = ref(null);
const form = ref({
  admin_id: '',
  password: '',
  passwordConfirm: '',
  admin_desc: '',
  role_code: 'MANAGER'
});
const isEditMode = ref(false);

/* ========== 삭제 확인 ========== */
const showConfirm = ref(false);

/** 목록 조회 */
async function fetchList() {
  loading.value = true;
  try {
    const res = await adminApi.getList({ page: page.value, size: size.value });
    list.value = res.data || res.list || [];
    total.value = res.total || 0;
  } catch (error) {
    console.error('[Admin] fetchList 실패:', error);
  } finally {
    loading.value = false;
  }
}

/** 조회 버튼 클릭 */
function handleSearch() {
  page.value = 1;
  fetchList();
}

/** 등록 버튼 클릭 */
function handleRegister() {
  isEditMode.value = false;
  editData.value = null;
  form.value = {
    admin_id: '',
    password: '',
    passwordConfirm: '',
    admin_desc: '',
    role_code: 'MANAGER'
  };
  showModal.value = true;
}

/** 행 클릭 → 수정 모달 */
function handleRowClick(row) {
  isEditMode.value = true;
  editData.value = row;
  form.value = {
    admin_id: row.admin_id,
    password: '',
    passwordConfirm: '',
    admin_desc: row.admin_desc || '',
    role_code: row.roles || 'MANAGER'
  };
  showModal.value = true;
}

/** 저장 */
async function handleSave() {
  try {
    /* 비밀번호 확인 검증 — 비밀번호 입력 시 확인 필드와 일치 여부 체크 */
    if (form.value.password) {
      if (form.value.password !== form.value.passwordConfirm) {
        toast.warning('비밀번호가 일치하지 않습니다.');
        return;
      }
    }
    if (isEditMode.value) {
      const updateData = { admin_desc: form.value.admin_desc };
      if (form.value.password) updateData.password = form.value.password;
      await adminApi.update(form.value.admin_id, updateData);
    } else {
      if (!form.value.admin_id || !form.value.password) {
        toast.warning('아이디와 비밀번호를 입력하세요.');
        return;
      }
      await adminApi.create({
        admin_id: form.value.admin_id,
        password: form.value.password,
        admin_desc: form.value.admin_desc,
        role_code: form.value.role_code
      });
    }
    toast.success('저장되었습니다');
    showModal.value = false;
    fetchList();
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다');
  }
}

/** 삭제 */
function handleDelete() {
  showConfirm.value = true;
}

async function confirmDelete() {
  showConfirm.value = false;
  try {
    await adminApi.remove(form.value.admin_id);
    toast.success('삭제되었습니다');
    showModal.value = false;
    fetchList();
  } catch (error) {
    toast.error(error.detail || '오류가 발생했습니다');
  }
}

/** 페이지 변경 */
function handlePageChange(newPage) {
  page.value = newPage;
  fetchList();
}

/** 페이지 크기 변경 */
function handlePageSizeChange(newSize) {
  size.value = newSize;
  page.value = 1;
  fetchList();
}

onMounted(() => {
  if (authStore.isSuper) fetchList();
});
</script>

<template>
  <div>
    <h2 class="mb-4 text-xl font-bold text-gray-800">관리자 관리</h2>

    <!-- SUPER 권한 없음 -->
    <div v-if="!authStore.isSuper" class="flex h-40 items-center justify-center text-gray-400">
      관리자 등록 권한이 없습니다. (SUPER 권한 필요)
    </div>

    <!-- SUPER 권한 있음 -->
    <template v-else>
      <SearchBar @search="handleSearch" @register="handleRegister" />

      <DataTable
        :columns="columns"
        :data="list"
        :loading="loading"
        :page-size="size"
        :total="total"
        @row-click="handleRowClick"
        @update:page-size="handlePageSizeChange"
      />

      <Pagination :page="page" :size="size" :total="total" @update:page="handlePageChange" />
    </template>

    <!-- 등록/수정 모달 -->
    <FormModal
      :visible="showModal"
      :title="isEditMode ? '관리자 수정' : '관리자 등록'"
      :show-delete="isEditMode && form.admin_id !== 'admin'"
      @close="showModal = false"
      @save="handleSave"
      @delete="handleDelete"
    >
      <div class="space-y-4">
        <div class="flex items-center">
          <label class="w-28 shrink-0 text-sm font-medium text-gray-700">관리자 ID</label>
          <input
            v-model="form.admin_id"
            type="text"
            :readonly="isEditMode"
            :class="isEditMode ? 'bg-gray-100' : ''"
            class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div class="flex items-center">
          <label class="w-28 shrink-0 text-sm font-medium text-gray-700">비밀번호</label>
          <input
            v-model="form.password"
            type="password"
            :placeholder="isEditMode ? '변경 시에만 입력' : ''"
            class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div class="flex items-center">
          <label class="w-28 shrink-0 text-sm font-medium text-gray-700">비밀번호 확인</label>
          <input
            v-model="form.passwordConfirm"
            type="password"
            :placeholder="isEditMode ? '변경 시에만 입력' : ''"
            class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div class="flex items-center">
          <label class="w-28 shrink-0 text-sm font-medium text-gray-700">설명</label>
          <input
            v-model="form.admin_desc"
            type="text"
            class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <div v-if="!isEditMode" class="flex items-center">
          <label class="w-28 shrink-0 text-sm font-medium text-gray-700">권한</label>
          <select
            v-model="form.role_code"
            class="flex-1 rounded border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="MANAGER">MANAGER</option>
            <option value="SUPER">SUPER</option>
          </select>
        </div>
      </div>
    </FormModal>

    <ConfirmDialog
      :visible="showConfirm"
      message="삭제하시겠습니까?"
      @confirm="confirmDelete"
      @cancel="showConfirm = false"
    />
  </div>
</template>
