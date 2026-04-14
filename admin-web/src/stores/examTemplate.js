/**
 * 시험 템플릿 Pinia 스토어
 * - tb_exam_template 목록 조회, 생성, 수정, 삭제 기능
 * - 검색 조건(시험종류/레벨/영역)과 페이징 상태를 관리한다.
 */
import { defineStore } from 'pinia';
import { ref, reactive } from 'vue';
import * as examTemplateApi from '@/api/examTemplate';

export const useExamTemplateStore = defineStore('examTemplate', () => {
  /* ========== 상태 ========== */

  /** 템플릿 목록 (페이징된 결과) */
  const list = ref([]);

  /** 전체 건수 */
  const total = ref(0);

  /** 현재 페이지 */
  const page = ref(1);

  /** 페이지당 항목 수 */
  const size = ref(20);

  /** 로딩 상태 */
  const loading = ref(false);

  /** 검색 조건 — 시험종류/레벨/영역 코드 필터 */
  const searchParams = reactive({
    tpk_type: '',
    tpk_level: '',
    section: ''
  });

  /* ========== 액션 ========== */

  /**
   * 시험 템플릿 목록 조회 (검색 조건 + 페이징 적용)
   */
  async function fetchList() {
    loading.value = true;
    try {
      /* 빈 문자열 파라미터 제거 — FastAPI Optional 타입 파싱 오류 방지 */
      const filtered = {};
      for (const [k, v] of Object.entries(searchParams)) {
        if (v !== '' && v !== null && v !== undefined) filtered[k] = v;
      }
      const params = { page: page.value, size: size.value, ...filtered };
      const res = await examTemplateApi.getList(params);
      list.value = res.list || res.data || [];
      total.value = res.total || 0;
    } catch (error) {
      console.error('[ExamTemplate Store] fetchList 실패:', error);
    } finally {
      loading.value = false;
    }
  }

  /**
   * 시험 템플릿 등록
   * @param {Object} data - 등록할 데이터
   */
  async function create(data) {
    try {
      return await examTemplateApi.create(data);
    } catch (error) {
      console.error('[ExamTemplate Store] create 실패:', error);
      throw error;
    }
  }

  /**
   * 시험 템플릿 수정
   * @param {number} tpkType - 시험종류 코드
   * @param {number} tpkLevel - 토픽레벨 코드
   * @param {number} section - 영역 코드
   * @param {number} questionNo - 문항번호
   * @param {Object} data - 수정할 데이터
   */
  async function update(tpkType, tpkLevel, section, questionNo, data) {
    try {
      return await examTemplateApi.update(tpkType, tpkLevel, section, questionNo, data);
    } catch (error) {
      console.error('[ExamTemplate Store] update 실패:', error);
      throw error;
    }
  }

  /**
   * 시험 템플릿 삭제
   * @param {number} tpkType - 시험종류 코드
   * @param {number} tpkLevel - 토픽레벨 코드
   * @param {number} section - 영역 코드
   * @param {number} questionNo - 문항번호
   */
  async function remove(tpkType, tpkLevel, section, questionNo) {
    try {
      return await examTemplateApi.remove(tpkType, tpkLevel, section, questionNo);
    } catch (error) {
      console.error('[ExamTemplate Store] remove 실패:', error);
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
    create,
    update,
    remove
  };
});
