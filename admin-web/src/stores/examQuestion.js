/**
 * 기출문제 관리 Pinia 스토어
 * - 기출문제 selectbox 옵션, 파일 목록, 문제/지시문 데이터를 관리한다.
 * - PDF→JSON 변환 및 일괄 저장 기능을 제공한다.
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import * as examListApi from '@/api/examList';
import { getFiles } from '@/api/examFile';
import * as examQuestionApi from '@/api/examQuestion';

/**
 * JSON 문자열을 안전하게 파싱하여 객체로 반환
 * 파싱 실패 시 null 반환
 */
function safeParseJson(jsonStr) {
  if (!jsonStr) return null;
  try {
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
}

export const useExamQuestionStore = defineStore('examQuestion', () => {
  /* ========== 상태 ========== */

  /** 기출문제(시험) 목록 — 상단 selectbox용 */
  const examOptions = ref([]);

  /** 기출문제 selectbox 로딩 상태 */
  const examOptionsLoading = ref(false);

  /** 기출문제 selectbox 에러 메시지 (null이면 에러 없음) */
  const examOptionsError = ref(null);

  /** 선택된 시험키 */
  const selectedExamKey = ref(null);

  /** 선택된 시험의 파일 목록 — 파일 selectbox용 */
  const fileOptions = ref([]);

  /** 선택된 파일키 */
  const selectedPdfKey = ref(null);

  /** 문제 목록 */
  const questions = ref([]);

  /** 지시문 목록 */
  const instructions = ref([]);

  /** 로딩 상태 */
  const loading = ref(false);

  /** MP3 파일 목록 (file_type='mp3') — 듣기 화면용 */
  const mp3Files = ref([]);

  /* ========== 계산된 속성 ========== */

  /** 선택된 시험 정보 */
  const selectedExam = computed(
    () => examOptions.value.find((e) => e.exam_key === selectedExamKey.value) || null
  );

  /** 선택된 파일 정보 */
  const selectedFile = computed(
    () => fileOptions.value.find((f) => f.pdf_key === selectedPdfKey.value) || null
  );

  /**
   * 문제와 지시문을 합치고 순서대로 정렬한 통합 목록
   * 지시문의 no_list 기준으로 문제 앞에 배치
   */
  const mergedItems = computed(() => {
    const items = [];

    // 지시문 추가 (_parsed로 JSON 1회 파싱, no_list 첫 번호를 _sortKey로 사용)
    instructions.value.forEach((ins) => {
      const parsed = safeParseJson(ins.ins_json);
      const firstNo =
        parsed && parsed.no_list && parsed.no_list.length ? parsed.no_list[0] : ins.ins_no;
      items.push({
        ...ins,
        _type: 'instruction',
        _sortKey: firstNo,
        _parsed: parsed
      });
    });

    // 문제 추가 (_parsed로 JSON 1회 파싱, _feedbackParsed로 feedback_json 파싱)
    questions.value.forEach((q) => {
      items.push({
        ...q,
        _type: 'question',
        _sortKey: q.question_no,
        _parsed: safeParseJson(q.question_json),
        _feedbackParsed: safeParseJson(q.feedback_json)
      });
    });

    // 번호 오름차순 정렬, 같은 번호면 지시문이 문제보다 먼저
    items.sort((a, b) => {
      if (a._sortKey !== b._sortKey) return a._sortKey - b._sortKey;
      if (a._type === 'instruction' && b._type !== 'instruction') return -1;
      if (a._type !== 'instruction' && b._type === 'instruction') return 1;
      return 0;
    });
    return items;
  });

  /**
   * 문제번호 → MP3 파일 매핑
   * 파일명 형식 "[N1]-[N2].mp3"에서 N2를 추출하여 문제번호와 매칭한다.
   */
  const mp3FileMap = computed(() => {
    const map = {};
    mp3Files.value.forEach((file) => {
      const match = file.file_name.match(/\d+-(\d+)\.mp3$/i);
      if (match) {
        const questionNo = parseInt(match[1], 10);
        map[questionNo] = file;
      }
    });
    return map;
  });

  /* ========== 액션 ========== */

  /**
   * 기출문제(시험) 목록 조회 — 상단 selectbox 옵션 로드
   * 모든 시험 목록을 조회하여 selectbox에 표시한다.
   */
  async function fetchExamOptions() {
    examOptionsLoading.value = true;
    examOptionsError.value = null;
    try {
      const res = await examListApi.getList({ page: 1, size: 100 });
      const items = res.list || res.data || [];
      /* 삭제되지 않은 시험만 selectbox에 표시 */
      examOptions.value = items.filter((e) => e.del_yn !== 'Y');
    } catch (error) {
      console.error('[ExamQuestion Store] fetchExamOptions 실패:', error);
      examOptions.value = [];
      examOptionsError.value = '기출문제 목록을 불러오지 못했습니다.';
    } finally {
      examOptionsLoading.value = false;
    }
  }

  /**
   * 선택된 시험의 파일 목록 조회 — 파일 selectbox 옵션 로드
   * @param {number} examKey - 시험키 PK
   */
  async function fetchFileOptions(examKey) {
    try {
      const res = await getFiles(examKey);
      const allFiles = res.data || [];
      /* file_type이 'pdf' 이거나 NULL인 파일만 표시 */
      fileOptions.value = allFiles.filter((f) => !f.file_type || f.file_type === 'pdf');
    } catch (error) {
      console.error('[ExamQuestion Store] fetchFileOptions 실패:', error);
      fileOptions.value = [];
    }
  }

  /**
   * 선택된 시험의 문제 + 지시문 조회
   * @param {number} examKey - 시험키 PK
   */
  async function fetchQuestionsAndInstructions(examKey) {
    loading.value = true;
    try {
      const res = await examQuestionApi.getQuestionsAndInstructions(examKey);
      const data = res.data || {};
      questions.value = data.questions || [];
      instructions.value = data.instructions || [];
    } catch (error) {
      console.error('[ExamQuestion Store] fetchQuestionsAndInstructions 실패:', error);
      questions.value = [];
      instructions.value = [];
    } finally {
      loading.value = false;
    }
  }

  /**
   * MP3 파일 목록 조회 — 듣기 화면에서 문제별 음성 재생에 사용
   * @param {number} examKey - 시험키 PK
   */
  async function fetchMp3Files(examKey) {
    try {
      const res = await getFiles(examKey);
      const allFiles = res.data || [];
      mp3Files.value = allFiles.filter((f) => f.file_type === 'mp3');
    } catch (error) {
      console.error('[ExamQuestion Store] fetchMp3Files 실패:', error);
      mp3Files.value = [];
    }
  }

  /**
   * 시험 선택 변경 처리
   * - 파일 목록(PDF) + MP3 파일 목록을 동시에 로드
   * @param {number} examKey - 시험키 PK
   */
  async function selectExam(examKey) {
    selectedExamKey.value = examKey;
    selectedPdfKey.value = null;
    fileOptions.value = [];
    questions.value = [];
    instructions.value = [];
    mp3Files.value = [];

    if (examKey) {
      await Promise.all([fetchFileOptions(examKey), fetchMp3Files(examKey)]);
    }
  }

  /**
   * 파일 선택 변경 처리
   * @param {number} pdfKey - 파일키 PK
   */
  function selectFile(pdfKey) {
    selectedPdfKey.value = pdfKey;
  }

  return {
    examOptions,
    examOptionsLoading,
    examOptionsError,
    selectedExamKey,
    fileOptions,
    selectedPdfKey,
    questions,
    instructions,
    loading,
    selectedExam,
    selectedFile,
    mergedItems,
    mp3Files,
    mp3FileMap,
    fetchExamOptions,
    fetchFileOptions,
    fetchMp3Files,
    fetchQuestionsAndInstructions,
    selectExam,
    selectFile
  };
});
