/**
 * 시험일정 Pinia 스토어
 * - tb_exam_schedule 목록 조회, 생성, 수정, 삭제 기능
 * - 검색 조건(시험종류)과 페이징 상태를 관리한다.
 */
import { defineStore } from 'pinia';
import { ref, reactive } from 'vue';
import * as examScheduleApi from '@/api/examSchedule';

export const useExamScheduleStore = defineStore('examSchedule', () => {
  /* ========== 상태 ========== */

  /** 시험일정 목록 */
  const list = ref([]);

  /** 전체 건수 */
  const total = ref(0);

  /** 현재 페이지 */
  const page = ref(1);

  /** 페이지당 항목 수 */
  const size = ref(20);

  /** 로딩 상태 */
  const loading = ref(false);

  /** 검색 조건 — 시험종류 코드 필터 */
  const searchParams = reactive({
    tpk_type: ''
  });

  /* ========== 액션 ========== */

  /**
   * 시험일정 목록 조회 (검색 조건 + 페이징 적용)
   */
  async function fetchList() {
    loading.value = true;
    try {
      /* 빈 문자열 파라미터 제거 */
      const filtered = {};
      for (const [k, v] of Object.entries(searchParams)) {
        if (v !== '' && v !== null && v !== undefined) filtered[k] = v;
      }
      const params = { page: page.value, size: size.value, ...filtered };
      const res = await examScheduleApi.getList(params);
      list.value = res.list || res.data || [];
      total.value = res.total || 0;
    } catch (error) {
      console.error('[ExamSchedule Store] fetchList 실패:', error);
    } finally {
      loading.value = false;
    }
  }

  /**
   * 시험일정 단건 조회 (locations 포함)
   * @param {number} examKey - 시험일정 키
   */
  async function fetchDetail(examKey) {
    try {
      return await examScheduleApi.getDetail(examKey);
    } catch (error) {
      console.error('[ExamSchedule Store] fetchDetail 실패:', error);
      throw error;
    }
  }

  /**
   * 시험일정 등록
   * @param {Object} data - 등록할 데이터
   */
  async function create(data) {
    try {
      return await examScheduleApi.create(data);
    } catch (error) {
      console.error('[ExamSchedule Store] create 실패:', error);
      throw error;
    }
  }

  /**
   * 시험일정 수정
   * @param {number} examKey - 시험일정 키
   * @param {Object} data - 수정할 데이터
   */
  async function update(examKey, data) {
    try {
      return await examScheduleApi.update(examKey, data);
    } catch (error) {
      console.error('[ExamSchedule Store] update 실패:', error);
      throw error;
    }
  }

  /**
   * 시험일정 삭제
   * @param {number} examKey - 시험일정 키
   */
  async function remove(examKey) {
    try {
      return await examScheduleApi.remove(examKey);
    } catch (error) {
      console.error('[ExamSchedule Store] remove 실패:', error);
      throw error;
    }
  }

  return {
    list,
    total,
    page,
    size,
    loading,
    searchParams,
    fetchList,
    fetchDetail,
    create,
    update,
    remove
  };
});
