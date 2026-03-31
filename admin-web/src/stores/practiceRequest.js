/**
 * 연습문제 생성 요청 Pinia 스토어
 * - 목록 조회, 검색 조건, 코드 selectbox 옵션을 관리한다.
 */
import { defineStore } from 'pinia';
import { ref } from 'vue';
import * as practiceRequestApi from '@/api/practiceRequest';
import * as codeApi from '@/api/code';

export const usePracticeRequestStore = defineStore('practiceRequest', () => {
  /* ========== 상태 ========== */

  /** 목록 데이터 */
  const list = ref([]);

  /** 전체 건수 */
  const total = ref(0);

  /** 현재 페이지 */
  const page = ref(1);

  /** 페이지당 행 수 */
  const size = ref(20);

  /** 로딩 상태 */
  const loading = ref(false);

  /** 검색 조건 */
  const searchParams = ref({
    exam_type: '',
    tpk_level: '',
    section: '',
    gen_method: '',
    status: ''
  });

  /* ========== 코드 selectbox 옵션 ========== */

  /** 시험유형 옵션 */
  const examTypeOptions = ref([]);

  /** 토픽레벨 옵션 */
  const tpkLevelOptions = ref([]);

  /** 영역 옵션 */
  const sectionOptions = ref([]);

  /** 난이도 옵션 */
  const difficultyOptions = ref([]);

  /** 생성방법 옵션 */
  const genMethodOptions = ref([]);

  /** 상태 옵션 */
  const statusOptions = ref([]);

  /* ========== 액션 ========== */

  /**
   * 코드 selectbox 옵션을 일괄 로드한다.
   * 시험유형, 토픽레벨, 영역, 난이도, 생성방법, 상태 그룹코드를 병렬 조회한다.
   */
  async function fetchCodeOptions() {
    try {
      const [etRes, tlRes, scRes, dfRes, gmRes, stRes] = await Promise.all([
        codeApi.getCodesByGroup('exam_type'),
        codeApi.getCodesByGroup('tpk_level'),
        codeApi.getCodesByGroup('section'),
        codeApi.getCodesByGroup('difficulty'),
        codeApi.getCodesByGroup('exam_req_method'),
        codeApi.getCodesByGroup('exam_req_status')
      ]);
      examTypeOptions.value = etRes.data || [];
      tpkLevelOptions.value = tlRes.data || [];
      sectionOptions.value = scRes.data || [];
      difficultyOptions.value = dfRes.data || [];
      genMethodOptions.value = gmRes.data || [];
      statusOptions.value = stRes.data || [];
    } catch (error) {
      console.error('[PracticeRequest Store] fetchCodeOptions 실패:', error);
    }
  }

  /**
   * 목록을 조회한다. 빈 문자열 파라미터는 제외한다.
   */
  async function fetchList() {
    loading.value = true;
    try {
      /* 빈 문자열 파라미터 필터링 (FastAPI Optional 파싱 오류 방지) */
      const params = { page: page.value, size: size.value };
      Object.entries(searchParams.value).forEach(([key, val]) => {
        if (val) params[key] = val;
      });

      const res = await practiceRequestApi.getList(params);
      console.log('[PracticeRequest] res:', res);
      console.log('[PracticeRequest] res.data:', res?.data);
      console.log('[PracticeRequest] res.list:', res?.list);
      console.log('[PracticeRequest] res.total:', res?.total);
      list.value = res.list || res.data || [];
      total.value = res.total || 0;
    } catch (error) {
      console.error('[PracticeRequest Store] fetchList 실패:', error);
      list.value = [];
      total.value = 0;
    } finally {
      loading.value = false;
    }
  }

  /**
   * 연습문제 생성 요청을 등록한다.
   * @param {Object} data - 등록 데이터
   */
  async function create(data) {
    return practiceRequestApi.create(data);
  }

  /**
   * 연습문제 생성 요청을 수정한다.
   * @param {number} requestKey - 요청 PK
   * @param {Object} data - 수정 데이터
   */
  async function update(requestKey, data) {
    return practiceRequestApi.update(requestKey, data);
  }

  /**
   * 연습문제 생성 요청을 삭제한다.
   * @param {number} requestKey - 요청 PK
   */
  async function remove(requestKey) {
    return practiceRequestApi.remove(requestKey);
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
    difficultyOptions,
    genMethodOptions,
    statusOptions,
    fetchCodeOptions,
    fetchList,
    create,
    update,
    remove
  };
});
