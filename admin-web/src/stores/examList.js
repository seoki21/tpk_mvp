/**
 * 시험문항 Pinia 스토어
 * - 시험문항 목록 조회, 생성, 수정, 삭제 기능
 * - 검색 조건과 페이징 상태를 관리한다.
 * - 코드 셀렉트박스 옵션(시험유형, 토픽레벨, 영역)도 함께 관리한다.
 */
import { defineStore } from 'pinia';
import { ref, reactive } from 'vue';
import * as examListApi from '@/api/examList';
import * as codeApi from '@/api/code';

export const useExamListStore = defineStore('examList', () => {
  /* ========== 상태 ========== */

  /** 시험문항 목록 (페이징된 결과) */
  const list = ref([]);

  /** 전체 건수 */
  const total = ref(0);

  /** 현재 페이지 (1부터 시작) */
  const page = ref(1);

  /** 페이지당 항목 수 */
  const size = ref(20);

  /** 로딩 상태 */
  const loading = ref(false);

  /** 검색 조건 */
  const searchParams = reactive({
    exam_type: '',
    tpk_level: '',
    round: ''
  });

  /** 시험유형 코드 옵션 (셀렉트박스용) */
  const examTypeOptions = ref([]);

  /** 토픽레벨 코드 옵션 (셀렉트박스용) */
  const tpkLevelOptions = ref([]);

  /** 영역 코드 옵션 (셀렉트박스용) */
  const sectionOptions = ref([]);

  /* ========== 액션 ========== */

  /**
   * 시험문항 목록 조회 (검색 조건 + 페이징 적용)
   * - 조회 결과에 년도 표시용 필드(exam_year_display)를 추가한다.
   */
  async function fetchList() {
    loading.value = true;
    try {
      /* 빈 문자열 파라미터 제거 — FastAPI의 Optional[int] 등 타입 파싱 오류 방지 */
      const filtered = {};
      for (const [k, v] of Object.entries(searchParams)) {
        if (v !== '' && v !== null && v !== undefined) filtered[k] = v;
      }
      const params = {
        page: page.value,
        size: size.value,
        ...filtered
      };
      const res = await examListApi.getList(params);
      const items = res.list || res.data || [];
      /* 년도 표시용 필드 추가: exam_year + '년' */
      list.value = items.map((row) => ({
        ...row,
        exam_year_display: row.exam_year ? row.exam_year + '년' : ''
      }));
      total.value = res.total || 0;
    } catch (error) {
      console.error('[ExamList Store] fetchList 실패:', error);
    } finally {
      loading.value = false;
    }
  }

  /**
   * 코드 셀렉트박스 옵션 조회
   * - 시험유형(exam_type), 토픽레벨(tpk_level), 영역(section) 3개 그룹을 각각 조회한다.
   */
  async function fetchCodeOptions() {
    try {
      const [examTypeRes, tpkCategoryRes, sectionRes] = await Promise.all([
        codeApi.getList({ group_code: 'exam_type', size: 100 }),
        codeApi.getList({ group_code: 'tpk_level', size: 100 }),
        codeApi.getList({ group_code: 'section', size: 100 })
      ]);
      examTypeOptions.value = examTypeRes.list || examTypeRes.data || [];
      tpkLevelOptions.value = tpkCategoryRes.list || tpkCategoryRes.data || [];
      sectionOptions.value = sectionRes.list || sectionRes.data || [];
    } catch (error) {
      console.error('[ExamList Store] fetchCodeOptions 실패:', error);
    }
  }

  /**
   * 시험문항 생성
   * @param {Object} data - 생성할 데이터
   */
  async function create(data) {
    try {
      const res = await examListApi.create(data);
      return res;
    } catch (error) {
      console.error('[ExamList Store] create 실패:', error);
      throw error;
    }
  }

  /**
   * 시험문항 수정
   * @param {number} examKey - 수정 대상 PK
   * @param {Object} data - 수정할 데이터
   */
  async function update(examKey, data) {
    try {
      const res = await examListApi.update(examKey, data);
      return res;
    } catch (error) {
      console.error('[ExamList Store] update 실패:', error);
      throw error;
    }
  }

  /**
   * 시험문항 삭제
   * @param {number} examKey - 삭제 대상 PK
   */
  async function remove(examKey) {
    try {
      const res = await examListApi.remove(examKey);
      return res;
    } catch (error) {
      console.error('[ExamList Store] remove 실패:', error);
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
    examTypeOptions,
    tpkLevelOptions,
    sectionOptions,
    fetchList,
    fetchCodeOptions,
    create,
    update,
    remove
  };
});
