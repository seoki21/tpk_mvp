/**
 * 기출문제 관리 공통 composable
 * - 읽기(PastExamQuestionView)와 듣기(PastExamListeningView) 화면에서 공유하는 로직을 제공한다.
 * - JSON 편집 상태 관리, 영역 필터, 저장, 피드백 생성 등 공통 기능을 포함한다.
 */
import { ref, reactive, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useExamQuestionStore } from '@/stores/examQuestion';
import {
  bulkSave,
  generateFeedbackSingle,
  updateQuestionSingle,
  cropImages,
  renameCropImages,
  cropManualImages
} from '@/api/examQuestion';
import { getCodesByGroup } from '@/api/code';
import { useToast } from '@/composables/useToast';

export function useExamQuestionCommon() {
  const router = useRouter();
  const store = useExamQuestionStore();
  const toast = useToast();

  /* ========== 코드 목록 (section / passage_type / question_type 셀렉트박스용) ========== */
  /** 영역(section) 코드 목록 — [{ code, code_name, ... }] */
  const sectionCodes = ref([]);
  /** 지문유형(passage_type) 코드 목록 */
  const passageTypeCodes = ref([]);
  /** 문제유형(question_type) 코드 목록 */
  const questionTypeCodes = ref([]);

  /**
   * tb_code 테이블에서 셀렉트박스용 코드 목록을 일괄 로드한다.
   * View 컴포넌트의 onMounted에서 호출한다.
   */
  async function loadCodeOptions() {
    try {
      const [sectionRes, passageRes, questionRes] = await Promise.all([
        getCodesByGroup('section'),
        getCodesByGroup('passage_type'),
        getCodesByGroup('question_type')
      ]);
      sectionCodes.value = sectionRes.data || [];
      passageTypeCodes.value = passageRes.data || [];
      questionTypeCodes.value = questionRes.data || [];
    } catch (err) {
      console.error('[loadCodeOptions] 코드 목록 로드 실패:', err);
    }
  }

  /**
   * 코드 값(숫자)으로 코드명(텍스트)을 조회한다.
   * @param {Array} codeList - 코드 목록 배열
   * @param {number|string} codeValue - 코드 값
   * @returns {string} 코드명 (못 찾으면 코드값 그대로 반환)
   */
  function getCodeName(codeList, codeValue) {
    if (codeValue == null) return '';
    const found = codeList.find((c) => String(c.code) === String(codeValue));
    return found ? found.code_name : String(codeValue);
  }

  /**
   * 셀렉트박스 값 변경 시 parsed 객체 + 좌측 JSON 텍스트를 동기화한다.
   * @param {Object} item - mergedItems의 항목
   * @param {string} field - 변경할 필드명 (section, passage_type, question_type)
   * @param {*} value - 새 값 (코드 값, 숫자)
   */
  function handleCodeFieldChange(item, field, value) {
    const state = getEditState(item);
    if (!state.parsed) return;

    /* parsed 객체에 값 반영 (숫자로 저장) */
    const numValue = value !== '' && value != null ? Number(value) : null;
    state.parsed[field] = numValue;

    /* 좌측 JSON 텍스트도 동기화 */
    state.text = JSON.stringify(state.parsed, null, 2);
    state.error = false;
  }

  /* ========== 확인 다이얼로그 ========== */
  const showConfirm = ref(false);
  const confirmMessage = ref('');
  const confirmCallback = ref(null);

  /** 확인 다이얼로그 — 확인 */
  function handleConfirm() {
    showConfirm.value = false;
    if (confirmCallback.value) confirmCallback.value();
  }

  /** 확인 다이얼로그 — 취소 */
  function handleCancel() {
    showConfirm.value = false;
    confirmCallback.value = null;
  }

  /* ========== 좌측 JSON 편집 상태 관리 ========== */

  /**
   * 각 항목의 편집 중인 JSON 텍스트를 관리하는 Map
   * key: "q_{question_no}" 또는 "i_{ins_no}"
   * value: { text, parsed, error, feedbackText, feedbackParsed, feedbackError, activeTab }
   */
  const editStates = reactive(new Map());

  /** 항목의 고유 키를 생성한다. */
  function itemKey(item) {
    return item._type === 'question' ? `q_${item.question_no}` : `i_${item.ins_no}`;
  }

  /** JSON 문자열을 pretty-print 형태로 변환한다. */
  function prettyPrint(jsonStr) {
    if (!jsonStr) return '{}';
    try {
      return JSON.stringify(JSON.parse(jsonStr), null, 2);
    } catch {
      return jsonStr;
    }
  }

  /** 항목의 편집 상태를 반환한다 (없으면 기본값 생성). */
  function getEditState(item) {
    const key = itemKey(item);
    if (!editStates.has(key)) {
      const raw = item._type === 'question' ? item.question_json : item.ins_json;
      const state = { text: prettyPrint(raw), parsed: item._parsed, error: false };
      if (item._type === 'question') {
        state.feedbackText = prettyPrint(item.feedback_json);
        state.feedbackParsed = item._feedbackParsed;
        state.feedbackError = false;
        state.activeTab = 'question';
      }
      editStates.set(key, state);
    }
    return editStates.get(key);
  }

  /** mergedItems가 변경될 때 편집 상태를 초기화한다. */
  watch(
    () => store.mergedItems,
    (items) => {
      editStates.clear();
      items.forEach((item) => {
        const key = itemKey(item);
        const raw = item._type === 'question' ? item.question_json : item.ins_json;
        const state = { text: prettyPrint(raw), parsed: item._parsed, error: false };
        if (item._type === 'question') {
          state.feedbackText = prettyPrint(item.feedback_json);
          state.feedbackParsed = item._feedbackParsed;
          state.feedbackError = false;
          state.activeTab = 'question';
        }
        editStates.set(key, state);
      });
    }
  );

  /** 좌측 JSON 편집 시 실시간 파싱하여 우측 UI에 반영한다. */
  function handleJsonEditFromPanel(item, newText) {
    const state = getEditState(item);
    const isFeedbackTab = item._type === 'question' && state.activeTab === 'feedback';

    if (isFeedbackTab) {
      state.feedbackText = newText;
      try {
        state.feedbackParsed = JSON.parse(state.feedbackText);
        state.feedbackError = false;
      } catch {
        state.feedbackError = true;
      }
    } else {
      state.text = newText;
      try {
        state.parsed = JSON.parse(state.text);
        state.error = false;
      } catch {
        state.error = true;
      }
    }
  }

  /** 좌측 JSON 탭 전환 (문제 항목 전용) */
  function setJsonTab(item, tab) {
    getEditState(item).activeTab = tab;
  }

  /** 현재 활성 탭에 해당하는 JSON 텍스트 반환 */
  function getActiveJsonText(item) {
    const state = getEditState(item);
    if (item._type === 'question' && state.activeTab === 'feedback') return state.feedbackText;
    return state.text;
  }

  /** 현재 활성 탭의 에러 상태 반환 */
  function getActiveJsonError(item) {
    const state = getEditState(item);
    if (item._type === 'question' && state.activeTab === 'feedback') return state.feedbackError;
    return state.error;
  }

  /* ========== 통합 selectbox + API 호출 팝업 ========== */

  /** API 호출 팝업 표시 여부 */
  const showConvertPopup = ref(false);

  /**
   * 통합 selectbox 변경 — examKey + pdfKey를 동시에 설정하고 데이터 조회
   * 영역에 따라 읽기/듣기 화면으로 라우트 분기한다.
   */
  async function handleCombinedChange(examKey, pdfKey) {
    if (!examKey || !pdfKey) {
      store.selectedExamKey = null;
      store.selectedPdfKey = null;
      store.fileOptions = [];
      store.questions = [];
      store.instructions = [];
      return;
    }

    /* 시험이 변경된 경우 파일/MP3 목록도 다시 로드 */
    if (store.selectedExamKey !== examKey) {
      await store.selectExam(examKey);
    }
    store.selectFile(pdfKey);

    /* 문제/지시문 조회 */
    await store.fetchQuestionsAndInstructions(examKey);

    /* 영역에 따라 읽기/듣기 화면으로 라우트 분기 */
    if (store.selectedExam) {
      const targetRoute =
        store.selectedExam.section_name === '듣기' ? 'pastExamListening' : 'pastExamQuestions';
      const currentRoute = router.currentRoute.value.name;
      if (currentRoute !== targetRoute) {
        router.push({ name: targetRoute });
      }
    }
  }

  /** API 호출 버튼 클릭 → 팝업 표시 */
  function handleConvertClick() {
    if (!store.selectedExamKey || !store.selectedPdfKey) {
      toast.warning('기출문제를 먼저 선택하세요.');
      return;
    }
    showConvertPopup.value = true;
  }

  /** API 호출 팝업 닫기 */
  function handleConvertPopupClose() {
    showConvertPopup.value = false;
  }

  /** API 호출 팝업에서 저장 완료 → 문제 목록 새로고침 */
  async function handleConvertPopupSaved() {
    showConvertPopup.value = false;
    if (store.selectedExamKey) {
      await store.fetchQuestionsAndInstructions(store.selectedExamKey);
    }
  }

  /* ========== 저장 ========== */

  /** 전체 문제/지시문 일괄 저장 */
  async function handleSaveAll() {
    if (!store.selectedExamKey || store.mergedItems.length === 0) return;

    const payload = { questions: [], instructions: [] };

    for (const item of store.mergedItems) {
      const state = getEditState(item);

      if (state.error || (item._type === 'question' && state.feedbackError)) {
        const label =
          item._type === 'question' ? `${item.question_no}번 문제` : `지시문 ${item.ins_no}`;
        toast.error(`${label}의 JSON 형식이 올바르지 않습니다. 수정 후 다시 시도하세요.`);
        return;
      }

      let jsonForSave;
      try {
        jsonForSave = JSON.stringify(JSON.parse(state.text));
      } catch {
        const label =
          item._type === 'question' ? `${item.question_no}번 문제` : `지시문 ${item.ins_no}`;
        toast.error(`${label}의 JSON 형식이 올바르지 않습니다.`);
        return;
      }

      if (item._type === 'question') {
        const parsed = state.parsed || {};
        const questionData = {
          question_no: item.question_no,
          section: parsed.section != null ? String(parsed.section) : (item.section || null),
          question_type: parsed.question_type != null ? String(parsed.question_type) : (item.question_type || null),
          struct_type: item.struct_type,
          question_json: jsonForSave,
          score: parsed.score || item.score,
          difficulty: item.difficulty
        };
        if (state.feedbackText && state.feedbackText.trim() !== '{}') {
          try {
            questionData.feedback_json = JSON.stringify(JSON.parse(state.feedbackText));
          } catch {
            toast.error(`${item.question_no}번 문제의 피드백 JSON 형식이 올바르지 않습니다.`);
            return;
          }
        }
        payload.questions.push(questionData);
      } else {
        payload.instructions.push({
          ins_no: item.ins_no,
          ins_json: jsonForSave
        });
      }
    }

    confirmMessage.value = '전체 저장하시겠습니까?';
    confirmCallback.value = async () => {
      try {
        await bulkSave(store.selectedExamKey, payload);
        toast.success('저장되었습니다.');
        await store.fetchQuestionsAndInstructions(store.selectedExamKey);
      } catch (error) {
        toast.error(error.detail || '저장에 실패했습니다.');
      }
    };
    showConfirm.value = true;
  }

  /* ========== 데이터 추출 ========== */

  /** 문항의 정답 번호를 반환한다. */
  function getCorrectAnswer(item) {
    const fbParsed = item._feedbackParsed;
    if (fbParsed && fbParsed.correct_answer) return fbParsed.correct_answer;
    const parsed = getEditState(item).parsed;
    if (parsed && parsed.correct_answer) return parsed.correct_answer;
    return null;
  }

  /** locale 코드 → 표시 라벨 매핑 (한국어, 3글자 이내) */
  const localeLabels = {
    ko: '한국어',
    en: '영어',
    vi: '베트남',
    zh: '중국어',
    'zh-TW': '대만어',
    th: '태국어',
    id: '인니어',
    uz: '우즈벡',
    ru: '러시아',
    ja: '일본어',
    mn: '몽골어',
    ne: '네팔어',
    my: '미얀마'
  };

  /**
   * 문항의 피드백 데이터를 반환한다 (다국어 탭 구조).
   * feedback_json의 키를 기반으로 동적으로 탭을 생성한다.
   * ko가 있으면 항상 첫 번째 탭으로 표시한다.
   */
  function getFeedbackData(item) {
    const state = getEditState(item);
    const fbParsed = state.feedbackParsed || item._feedbackParsed;

    if (fbParsed) {
      const feedbackMap = fbParsed.feedback || fbParsed;
      /* feedback_json의 키 중 배열 값이 있는 것만 탭으로 생성 */
      const keys = Object.keys(feedbackMap).filter(
        (k) => Array.isArray(feedbackMap[k]) && feedbackMap[k].length
      );
      if (keys.length > 0) {
        /* ko를 맨 앞으로 정렬 */
        keys.sort((a, b) => (a === 'ko' ? -1 : b === 'ko' ? 1 : 0));
        const tabs = keys.map((k) => ({
          key: k,
          label: localeLabels[k] || k,
          list: feedbackMap[k]
        }));
        return { tabs, source: 'feedback_json' };
      }
    }

    const parsed = getEditState(item).parsed;
    if (parsed && parsed.feedback && parsed.feedback.length) {
      const tabs = [{ key: 'ko', label: '한국어', list: parsed.feedback }];
      return { tabs, source: 'question_json' };
    }

    return { tabs: [], source: 'none' };
  }

  /** 기출문제 selectbox 표시 텍스트 생성 */
  function getExamLabel(exam) {
    const parts = [];
    if (exam.exam_year) parts.push(exam.exam_year + '년');
    if (exam.round) parts.push('제' + exam.round + '회');
    if (exam.tpk_level_name) parts.push(exam.tpk_level_name);
    return parts.join(' ') || `시험 ${exam.exam_key}`;
  }

  /* ========== 피드백 생성 (locale 선택 팝업 연동) ========== */
  const feedbackGenerating = ref(false);

  /** locale 선택 다이얼로그 표시 여부 */
  const showLocaleDialog = ref(false);

  /** locale 선택 후 실행할 콜백 */
  const localeCallback = ref(null);

  /** 현재 문항에 이미 존재하는 피드백의 locale 코드 목록 (팝업 기본 체크 판단용) */
  const existingFeedbackLocales = ref([]);

  /** locale 선택 다이얼로그 — 확인 (선택된 locale 목록으로 콜백 실행) */
  function handleLocaleConfirm(locales) {
    showLocaleDialog.value = false;
    if (localeCallback.value) localeCallback.value(locales);
  }

  /** locale 선택 다이얼로그 — 취소 */
  function handleLocaleCancel() {
    showLocaleDialog.value = false;
    localeCallback.value = null;
  }

  /**
   * 문항의 기존 피드백에서 데이터가 있는 locale 코드 목록을 추출한다.
   * @param {Object} item - mergedItems의 항목
   * @returns {string[]} 피드백이 존재하는 locale 코드 배열 (예: ['ko', 'en', 'ja'])
   */
  function _getExistingFeedbackLocales(item) {
    const state = getEditState(item);
    const fbParsed = state.feedbackParsed || item._feedbackParsed;
    if (!fbParsed) return [];
    const feedbackMap = fbParsed.feedback || fbParsed;
    return Object.keys(feedbackMap).filter(
      (k) => Array.isArray(feedbackMap[k]) && feedbackMap[k].length > 0
    );
  }

  /** 개별 문항 피드백 생성 — locale 선택 팝업 후 실행 */
  function handleGenerateFeedbackForItem(item) {
    if (!store.selectedExamKey) return;

    /* 기존 피드백 locale 목록을 팝업에 전달 */
    existingFeedbackLocales.value = _getExistingFeedbackLocales(item);

    localeCallback.value = async (locales) => {
      feedbackGenerating.value = true;
      try {
        const state = getEditState(item);
        const questionJson = JSON.stringify(JSON.parse(state.text));
        /* 시험의 영역명을 전달 (듣기/읽기 프롬프트 분기용) */
        const section = store.selectedExam?.section_name || null;
        const res = await generateFeedbackSingle(questionJson, 'claude', locales, section);
        const feedbackJson = res.data?.feedback_json;

        if (feedbackJson) {
          const parsed = JSON.parse(feedbackJson);
          state.feedbackText = JSON.stringify(parsed, null, 2);
          state.feedbackParsed = parsed;
          state.feedbackError = false;
          state.activeTab = 'feedback';
        }
      } catch (error) {
        toast.error(error.detail || '피드백 생성에 실패했습니다.');
      } finally {
        feedbackGenerating.value = false;
      }
    };
    showLocaleDialog.value = true;
  }

  /** 단건 저장 상태 */
  const itemSaving = ref(false);

  /** 개별 문항 저장 */
  async function handleSaveItemSingle(item) {
    if (!store.selectedExamKey) return;

    const state = getEditState(item);
    const questionNo = item.question_no;

    let questionMinified = null;
    if (state.text && state.text.trim()) {
      try {
        questionMinified = JSON.stringify(JSON.parse(state.text));
      } catch {
        toast.error('문제 JSON 형식이 올바르지 않습니다.');
        return;
      }
    }

    let feedbackMinified = null;
    if (state.feedbackText && state.feedbackText.trim()) {
      try {
        feedbackMinified = JSON.stringify(JSON.parse(state.feedbackText));
      } catch {
        toast.error('피드백 JSON 형식이 올바르지 않습니다.');
        return;
      }
    }

    confirmMessage.value = `${questionNo}번 문제를 저장하시겠습니까?`;
    confirmCallback.value = async () => {
      itemSaving.value = true;
      try {
        await updateQuestionSingle(
          store.selectedExamKey,
          questionNo,
          questionMinified,
          feedbackMinified
        );
        toast.success('저장되었습니다.');
      } catch (error) {
        toast.error(error.detail || '저장에 실패했습니다.');
      } finally {
        itemSaving.value = false;
      }
    };
    showConfirm.value = true;
  }

  /* ========== JSON 파일 임포트 ========== */

  /**
   * 문항 JSON 파일 임포트 핸들러
   * ExamConvertPopup.confirmSave()와 동일한 로직으로 bulkSave API를 호출한다.
   * @param {Array} items - 파싱된 JSON 배열 ([{ item_type: 'I'|'Q', ... }])
   */
  function handleImportQuestionJson(items) {
    if (!store.selectedExamKey) {
      toast.warning('기출문제를 먼저 선택하세요.');
      return;
    }

    confirmMessage.value = '문항 JSON 파일을 저장하시겠습니까?';
    confirmCallback.value = async () => {
      try {
        const questions = [];
        const instructions = [];
        let insCounter = 1;

        for (const item of items) {
          if (item.item_type === 'I') {
            instructions.push({ ins_no: insCounter++, ins_json: JSON.stringify(item) });
          } else if (item.item_type === 'Q') {
            questions.push({
              question_no: item.no,
              section: item.section != null ? String(item.section) : null,
              question_type: item.question_type != null ? String(item.question_type) : null,
              struct_type: null,
              question_json: JSON.stringify(item),
              score: item.score || null,
              difficulty: null
            });
          }
        }

        await bulkSave(store.selectedExamKey, { questions, instructions });
        toast.success('문항 JSON 파일이 저장되었습니다.');
        await store.fetchQuestionsAndInstructions(store.selectedExamKey);
      } catch (error) {
        toast.error(error.detail || '문항 JSON 저장에 실패했습니다.');
      }
    };
    showConfirm.value = true;
  }

  /**
   * 피드백 JSON 파일 임포트 핸들러
   * 파일 형식: { "question_no": { "locale": [...], ... }, ... } 또는 배열
   * 각 문항의 feedback_json을 업데이트한다.
   * @param {Object|Array} data - 파싱된 피드백 JSON 데이터
   */
  function handleImportFeedbackJson(data) {
    if (!store.selectedExamKey) {
      toast.warning('기출문제를 먼저 선택하세요.');
      return;
    }
    if (store.mergedItems.length === 0) {
      toast.warning('문항 데이터가 없습니다. 문항 JSON을 먼저 저장하세요.');
      return;
    }

    confirmMessage.value = '피드백 JSON 파일을 저장하시겠습니까?';
    confirmCallback.value = async () => {
      try {
        /* 피드백 데이터를 문항별로 매핑하여 bulkSave 호출 */
        const questions = [];

        for (const item of store.mergedItems) {
          if (item._type !== 'question') continue;

          const qNo = item.question_no;
          const feedbackData = data[String(qNo)] || data[qNo];
          if (!feedbackData) continue;

          const state = getEditState(item);
          questions.push({
            question_no: qNo,
            section: item.section,
            question_type: item.question_type,
            struct_type: item.struct_type,
            question_json: state.text ? JSON.stringify(JSON.parse(state.text)) : item.question_json,
            feedback_json: JSON.stringify(feedbackData),
            score: item.score,
            difficulty: item.difficulty
          });
        }

        if (questions.length === 0) {
          toast.warning('매칭되는 피드백 데이터가 없습니다.');
          return;
        }

        await bulkSave(store.selectedExamKey, { questions, instructions: [] });
        toast.success(`피드백 ${questions.length}건이 저장되었습니다.`);
        await store.fetchQuestionsAndInstructions(store.selectedExamKey);
      } catch (error) {
        toast.error(error.detail || '피드백 JSON 저장에 실패했습니다.');
      }
    };
    showConfirm.value = true;
  }

  /** JSON 미변환 필터 체크박스 토글 */
  function handleToggleJsonFilter(checked) {
    store.jsonFilterOnly = checked;
  }

  /* ========== 이미지 생성 (PDF crop) ========== */

  /** 이미지 생성 처리 중 상태 */
  const imageGenerating = ref(false);

  /**
   * "이미지 생성" 버튼 클릭 핸들러
   * 1. PDF에서 이미지 영역을 OpenCV로 자동 검출/crop (백엔드 API)
   * 2. 현재 mergedItems에서 이미지 포함 문항을 식별 (is_question_image/is_choices_image)
   * 3. crop 결과와 문항을 자동 매칭
   * 4. JSON에 question_img, choices 이미지 경로 업데이트
   */
  function handleGenerateImages() {
    if (!store.selectedExamKey || !store.selectedPdfKey) {
      toast.warning('기출문제를 먼저 선택하세요.');
      return;
    }
    if (store.mergedItems.length === 0) {
      toast.warning('문항 데이터가 없습니다. JSON 변환을 먼저 진행하세요.');
      return;
    }

    confirmMessage.value = '문항과 문제 이미지를 자동 생성하시겠습니까?';
    confirmCallback.value = () => _executeGenerateImages();
    showConfirm.value = true;
  }

  /** 이미지 생성 실행 (컨펌 후 호출) */
  async function _executeGenerateImages() {
    /* 이미지 포함 문항 식별 */
    const imageItems = [];
    for (const item of store.mergedItems) {
      const state = getEditState(item);
      const parsed = state.parsed;
      if (!parsed) continue;

      const hasQuestionImg = parsed.is_question_image === 'Y';
      const hasChoicesImg = parsed.is_choices_image === 'Y';
      if (hasQuestionImg || hasChoicesImg) {
        imageItems.push({
          item,
          state,
          parsed,
          hasQuestionImg,
          hasChoicesImg,
          no:
            item._type === 'question'
              ? item.question_no
              : parsed.no_list
                ? parsed.no_list[0]
                : item.ins_no
        });
      }
    }

    if (imageItems.length === 0) {
      toast.info('이미지가 포함된 문항이 없습니다.');
      return;
    }

    imageGenerating.value = true;
    try {
      /* 1. 백엔드 crop API 호출 */
      const res = await cropImages(store.selectedExamKey, store.selectedPdfKey);
      const cropResults = res.data || [];

      if (cropResults.length === 0) {
        toast.warning('PDF에서 이미지를 검출하지 못했습니다.');
        return;
      }

      /* 2. 자동 매칭: 이미지 문항 순서와 crop 결과 순서를 매핑 */
      const examKey = store.selectedExamKey;
      const renameMap = [];
      let cropIdx = 0;

      /* 변경 데이터를 임시 보관 — rename 완료 전에 reactive 객체를 수정하면
         Vue가 re-render하여 아직 존재하지 않는 이미지를 요청하는 문제 방지 */
      const pendingUpdates = [];

      for (const imgItem of imageItems) {
        const no = imgItem.no;
        const updates = {};

        if (imgItem.hasChoicesImg) {
          /* 답안 이미지: 4개 박스를 순서대로 매핑 (2x2 그리드) */
          const choiceCount = imgItem.parsed.choices ? imgItem.parsed.choices.length : 4;
          const newChoices = [];

          for (let i = 0; i < choiceCount; i++) {
            if (cropIdx >= cropResults.length) break;
            const crop = cropResults[cropIdx];
            const newFilename = `ans_${examKey}_${no}_${i + 1}.png`;
            renameMap.push({ old_filename: crop.filename, new_filename: newFilename });
            const circleNum = String.fromCodePoint(0x2460 + i);
            newChoices.push(`${circleNum} ${newFilename}`);
            cropIdx++;
          }

          updates.choices = newChoices;
        }

        if (imgItem.hasQuestionImg) {
          if (cropIdx < cropResults.length) {
            const crop = cropResults[cropIdx];
            const newFilename = `qst_${examKey}_${no}.png`;
            renameMap.push({ old_filename: crop.filename, new_filename: newFilename });
            updates.question_img = newFilename;
            cropIdx++;
          }
        }

        pendingUpdates.push({ imgItem, updates });
      }

      /* 3. 파일명 일괄 변경 (백엔드) — rename 완료까지 reactive 객체를 수정하지 않음 */
      if (renameMap.length > 0) {
        await renameCropImages(examKey, renameMap);
      }

      /* rename 완료 후 parsed 객체 + 편집 상태를 일괄 반영
         (이 시점부터 이미지 파일이 최종 이름으로 존재) */
      for (const { imgItem, updates } of pendingUpdates) {
        if (updates.choices) imgItem.parsed.choices = updates.choices;
        if (updates.question_img) imgItem.parsed.question_img = updates.question_img;
        imgItem.state.text = JSON.stringify(imgItem.parsed, null, 2);
        imgItem.state.parsed = imgItem.parsed;
        imgItem.state.error = false;
      }

      toast.success(`이미지 ${renameMap.length}개 생성 완료. 전체 저장을 눌러주세요.`);
    } catch (error) {
      toast.error(error.detail || '이미지 생성에 실패했습니다.');
    } finally {
      imageGenerating.value = false;
    }
  }

  /* ========== 수동 이미지 생성 (ImageCropPopup) ========== */

  /** 수동 이미지 생성 팝업 표시 상태 */
  const showImageCropPopup = ref(false);
  /** 수동 이미지 생성 대상 문항 목록 */
  const cropPopupImageItems = ref([]);

  /**
   * "수동 생성" 버튼 클릭 핸들러
   * 이미지가 필요한 문항을 식별하고 수동 생성 팝업을 연다.
   */
  function handleManualGenerateImages() {
    if (!store.selectedExamKey || !store.selectedPdfKey) {
      toast.warning('기출문제를 먼저 선택하세요.');
      return;
    }
    if (store.mergedItems.length === 0) {
      toast.warning('문항 데이터가 없습니다. JSON 변환을 먼저 진행하세요.');
      return;
    }

    // 이미지 포함 문항 식별
    const imageItems = [];
    for (const item of store.mergedItems) {
      const state = getEditState(item);
      const parsed = state.parsed;
      if (!parsed) continue;
      if (parsed.is_question_image === 'Y' || parsed.is_choices_image === 'Y') {
        imageItems.push({
          item,
          state,
          parsed,
          hasQuestionImg: parsed.is_question_image === 'Y',
          hasChoicesImg: parsed.is_choices_image === 'Y',
          no: item._type === 'question'
            ? item.question_no
            : parsed.no_list ? parsed.no_list[0] : item.ins_no
        });
      }
    }

    if (imageItems.length === 0) {
      toast.info('이미지가 포함된 문항이 없습니다.');
      return;
    }

    cropPopupImageItems.value = imageItems;
    showImageCropPopup.value = true;
  }

  /**
   * 수동 생성 팝업에서 "적용" 시 호출 (다중 문항 지원)
   * 각 crop 데이터에 문항번호(no)가 포함되어 있으므로 해당 문항의 parsed를 각각 업데이트한다.
   * @param {{ crops: Array<{ no, imageType, page, x, y, w, h }> }} cropData
   */
  async function handleCropApply(cropData) {
    if (!cropData.crops || cropData.crops.length === 0) return;

    const examKey = store.selectedExamKey;
    const pdfKey = store.selectedPdfKey;

    // 문항번호 → imgItem 빠른 조회용 맵 생성
    const itemMap = {};
    for (const imgItem of cropPopupImageItems.value) {
      itemMap[imgItem.no] = imgItem;
    }

    // 백엔드로 전송할 crop 목록 구성 (문항번호별 filename 생성)
    const backendCrops = cropData.crops.map((c) => {
      let filename;
      if (c.imageType === 'question') {
        filename = `qst_${examKey}_${c.no}.png`;
      } else {
        const choiceIdx = parseInt(c.imageType.replace('choice', ''), 10);
        filename = `ans_${examKey}_${c.no}_${choiceIdx}.png`;
      }
      return {
        page: c.page,
        x: c.x,
        y: c.y,
        w: c.w,
        h: c.h,
        filename
      };
    });

    imageGenerating.value = true;
    try {
      await cropManualImages(examKey, pdfKey, backendCrops);

      // 문항별로 parsed 객체 업데이트
      const updatedItems = new Set();
      for (const crop of cropData.crops) {
        const imgItem = itemMap[crop.no];
        if (!imgItem) continue;

        if (crop.imageType === 'question' && imgItem.hasQuestionImg) {
          imgItem.parsed.question_img = `qst_${examKey}_${crop.no}.png`;
        } else if (crop.imageType.startsWith('choice') && imgItem.hasChoicesImg) {
          const choiceIdx = parseInt(crop.imageType.replace('choice', ''), 10);
          const circleNum = String.fromCodePoint(0x2460 + choiceIdx - 1);
          const filename = `ans_${examKey}_${crop.no}_${choiceIdx}.png`;
          if (!imgItem.parsed.choices) imgItem.parsed.choices = [];
          imgItem.parsed.choices[choiceIdx - 1] = `${circleNum} ${filename}`;
        }

        updatedItems.add(crop.no);
      }

      // 변경된 문항들의 편집 상태 일괄 반영
      for (const no of updatedItems) {
        const imgItem = itemMap[no];
        if (!imgItem) continue;
        imgItem.state.text = JSON.stringify(imgItem.parsed, null, 2);
        imgItem.state.parsed = imgItem.parsed;
        imgItem.state.error = false;
      }

      showImageCropPopup.value = false;
      toast.success(`이미지 ${backendCrops.length}개 수동 생성 완료. 전체 저장을 눌러주세요.`);
    } catch (error) {
      toast.error(error.detail || '수동 이미지 생성에 실패했습니다.');
    } finally {
      imageGenerating.value = false;
    }
  }

  /** 수동 생성 팝업 닫기 */
  function handleCropPopupClose() {
    showImageCropPopup.value = false;
  }

  /** 기출문제 목록 재조회 */
  function handleRetryExamOptions() {
    store.fetchExamOptions();
  }

  return {
    store,
    toast,
    /* 확인 다이얼로그 */
    showConfirm,
    confirmMessage,
    handleConfirm,
    handleCancel,
    /* JSON 편집 */
    editStates,
    getEditState,
    handleJsonEditFromPanel,
    setJsonTab,
    getActiveJsonText,
    getActiveJsonError,
    /* 통합 selectbox + API 호출 팝업 */
    showConvertPopup,
    handleCombinedChange,
    handleConvertClick,
    handleConvertPopupClose,
    handleConvertPopupSaved,
    /* 저장 */
    handleSaveAll,
    /* 데이터 추출 */
    getCorrectAnswer,
    getFeedbackData,
    getExamLabel,
    /* 피드백 생성 (locale 선택 팝업) */
    feedbackGenerating,
    showLocaleDialog,
    existingFeedbackLocales,
    handleLocaleConfirm,
    handleLocaleCancel,
    handleGenerateFeedbackForItem,
    /* 단건 저장 */
    itemSaving,
    handleSaveItemSingle,
    /* 이미지 생성 */
    imageGenerating,
    handleGenerateImages,
    /* 수동 이미지 생성 */
    showImageCropPopup,
    cropPopupImageItems,
    handleManualGenerateImages,
    handleCropApply,
    handleCropPopupClose,
    /* JSON 파일 임포트 */
    handleImportQuestionJson,
    handleImportFeedbackJson,
    /* 코드 목록 (셀렉트박스) */
    sectionCodes,
    passageTypeCodes,
    questionTypeCodes,
    loadCodeOptions,
    getCodeName,
    handleCodeFieldChange,
    /* 기타 */
    handleToggleJsonFilter,
    handleRetryExamOptions
  };
}
