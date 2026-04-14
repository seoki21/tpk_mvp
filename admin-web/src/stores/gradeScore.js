/**
 * 등급 관리 Pinia 스토어
 * - tb_grade_score 목록 조회, 생성, 수정, 삭제 기능
 * - 검색 조건(시험종류)과 로딩 상태를 관리한다.
 */
import { defineStore } from 'pinia';
import { ref, reactive } from 'vue';
import * as gradeScoreApi from '@/api/gradeScore';

export const useGradeScoreStore = defineStore('gradeScore', () => {
  /* ========== 상태 ========== */

  /** 등급 목록 (전체) */
  const list = ref([]);

  /** 로딩 상태 */
  const loading = ref(false);

  /** 검색 조건 — 시험종류 코드 필터 */
  const searchParams = reactive({
    tpk_type: ''
  });

  /* ========== 액션 ========== */

  /**
   * 등급 목록 조회 (검색 조건 적용)
   */
  async function fetchList() {
    loading.value = true;
    try {
      /* 빈 문자열 파라미터 제거 — FastAPI Optional 타입 파싱 오류 방지 */
      const filtered = {};
      for (const [k, v] of Object.entries(searchParams)) {
        if (v !== '' && v !== null && v !== undefined) filtered[k] = v;
      }
      const res = await gradeScoreApi.getList(filtered);
      list.value = res.data || [];
    } catch (error) {
      console.error('[GradeScore Store] fetchList 실패:', error);
    } finally {
      loading.value = false;
    }
  }

  /**
   * 등급 등록
   * @param {Object} data - 등록할 데이터
   */
  async function create(data) {
    try {
      return await gradeScoreApi.create(data);
    } catch (error) {
      console.error('[GradeScore Store] create 실패:', error);
      throw error;
    }
  }

  /**
   * 등급 수정
   * @param {number} tpkType - 시험종류 코드
   * @param {number} tpkLevel - 토픽레벨 코드
   * @param {number} tpkGrade - 등급
   * @param {Object} data - 수정할 데이터
   */
  async function update(tpkType, tpkLevel, tpkGrade, data) {
    try {
      return await gradeScoreApi.update(tpkType, tpkLevel, tpkGrade, data);
    } catch (error) {
      console.error('[GradeScore Store] update 실패:', error);
      throw error;
    }
  }

  /**
   * 등급 삭제
   * @param {number} tpkType - 시험종류 코드
   * @param {number} tpkLevel - 토픽레벨 코드
   * @param {number} tpkGrade - 등급
   */
  async function remove(tpkType, tpkLevel, tpkGrade) {
    try {
      return await gradeScoreApi.remove(tpkType, tpkLevel, tpkGrade);
    } catch (error) {
      console.error('[GradeScore Store] remove 실패:', error);
      throw error;
    }
  }

  return {
    list,
    loading,
    searchParams,
    fetchList,
    create,
    update,
    remove
  };
});
