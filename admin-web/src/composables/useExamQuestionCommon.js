/**
 * 기출문제 관리 공통 composable
 * - 읽기(PastExamQuestionView)와 듣기(PastExamListeningView) 화면에서 공유하는 로직을 제공한다.
 * - JSON 편집 상태 관리, 영역 필터, 저장, 피드백 생성 등 공통 기능을 포함한다.
 */
import { ref, reactive, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useExamQuestionStore } from '@/stores/examQuestion';
import { bulkSave, generateFeedbackSingle, updateQuestionSingle } from '@/api/examQuestion';
import { useToast } from '@/composables/useToast';

export function useExamQuestionCommon() {
  const router = useRouter();
  const store = useExamQuestionStore();
  const toast = useToast();

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

  /* ========== 영역 필터 ========== */

  /** 선택된 시험과 같은 (year, round, tpk_level)을 가진 시험들의 영역 목록 */
  const sectionOptionsForExam = computed(() => {
    const exam = store.selectedExam;
    if (!exam) return [];
    const siblings = store.examOptions.filter(
      (e) => e.exam_year === exam.exam_year && e.round === exam.round && e.tpk_level === exam.tpk_level
    );
    const seen = new Set();
    return siblings
      .filter((e) => {
        if (seen.has(e.section)) return false;
        seen.add(e.section);
        return true;
      })
      .map((e) => ({ code: e.section, name: e.section_name }));
  });

  /** 시험 선택 변경 — 선택된 시험의 영역에 따라 읽기/듣기 화면으로 라우트 분기 */
  async function handleExamChange(event) {
    const examKey = event.target.value ? Number(event.target.value) : null;
    await store.selectExam(examKey);
    /* 선택된 시험의 영역에 따라 라우트 분기 */
    if (store.selectedExam) {
      const targetRoute = store.selectedExam.section_name === '듣기' ? 'pastExamListening' : 'pastExamQuestions';
      const currentRoute = router.currentRoute.value.name;
      if (currentRoute !== targetRoute) {
        router.push({ name: targetRoute });
      }
    }
  }

  /**
   * 영역 선택 변경 — 같은 그룹 내 해당 영역의 exam_key로 전환
   * section_name에 따라 읽기/듣기 화면으로 라우트 분기한다.
   */
  async function handleSectionChange(event) {
    const sectionCode = event.target.value || null;
    if (!sectionCode || !store.selectedExam) return;

    const currentExam = store.selectedExam;
    const targetExam = store.examOptions.find(
      (e) =>
        e.exam_year === currentExam.exam_year &&
        e.round === currentExam.round &&
        e.tpk_level === currentExam.tpk_level &&
        e.section === sectionCode
    );
    if (targetExam) {
      /* 시험 전환 */
      if (targetExam.exam_key !== store.selectedExamKey) {
        await store.selectExam(targetExam.exam_key);
      }
      /* 영역에 따라 라우트 분기 (듣기 ↔ 읽기) */
      const targetRoute = targetExam.section_name === '듣기' ? 'pastExamListening' : 'pastExamQuestions';
      const currentRoute = router.currentRoute.value.name;
      if (currentRoute !== targetRoute) {
        router.push({ name: targetRoute });
      }
    }
  }

  /** 파일 선택 변경 */
  async function handleFileChange(event) {
    const pdfKey = event.target.value ? Number(event.target.value) : null;
    store.selectFile(pdfKey);
    if (store.selectedExamKey) {
      await store.fetchQuestionsAndInstructions(store.selectedExamKey);
    }
  }

  /** JSON 변환(일괄) 버튼 클릭 → 변환 페이지로 이동 */
  function handleConvertClick() {
    if (!store.selectedExamKey || !store.selectedPdfKey) {
      toast.warning('기출문제와 파일을 먼저 선택하세요.');
      return;
    }
    router.push({
      name: 'examConvert',
      params: { examKey: store.selectedExamKey, pdfKey: store.selectedPdfKey }
    });
  }

  /** JSON 변환(업로드) 파일 선택 핸들러 */
  function handleJsonUploadSelect(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    toast.info(`선택된 파일: ${file.name}\n(업로드 처리는 추후 구현 예정)`);
    event.target.value = '';
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
          section: parsed.section || item.section,
          question_type: parsed.type || item.question_type,
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

  /** 문항의 피드백 데이터를 반환한다 (다국어 탭 구조). */
  function getFeedbackData(item) {
    const langOrder = [
      { key: 'ko', label: '한국어' },
      { key: 'en', label: 'English' },
      { key: 'ja', label: '日本語' },
      { key: 'zh', label: '中文' },
      { key: 'vi', label: 'Tiếng Việt' }
    ];
    const state = getEditState(item);
    const fbParsed = state.feedbackParsed || item._feedbackParsed;

    if (fbParsed) {
      const feedbackMap = fbParsed.feedback || fbParsed;
      const hasData = langOrder.some((l) => Array.isArray(feedbackMap[l.key]) && feedbackMap[l.key].length);
      if (hasData) {
        const tabs = langOrder.map((l) => ({
          key: l.key,
          label: l.label,
          list: Array.isArray(feedbackMap[l.key]) ? feedbackMap[l.key] : []
        }));
        return { tabs, source: 'feedback_json' };
      }
    }

    const parsed = getEditState(item).parsed;
    if (parsed && parsed.feedback && parsed.feedback.length) {
      const tabs = langOrder.map((l) => ({
        key: l.key,
        label: l.label,
        list: l.key === 'ko' ? parsed.feedback : []
      }));
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

  /* ========== 피드백 생성 ========== */
  const feedbackGenerating = ref(false);

  /** 개별 문항 피드백 생성 */
  async function handleGenerateFeedbackForItem(item) {
    if (!store.selectedExamKey) return;

    confirmMessage.value = '피드백을 생성하시겠습니까? Claude API를 사용합니다';
    confirmCallback.value = async () => {
      feedbackGenerating.value = true;
      try {
        const state = getEditState(item);
        const questionJson = JSON.stringify(JSON.parse(state.text));
        const res = await generateFeedbackSingle(questionJson);
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
    showConfirm.value = true;
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
          store.selectedExamKey, questionNo, questionMinified, feedbackMinified
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
    /* 영역 필터 */
    sectionOptionsForExam,
    handleExamChange,
    handleSectionChange,
    handleFileChange,
    handleConvertClick,
    handleJsonUploadSelect,
    /* 저장 */
    handleSaveAll,
    /* 데이터 추출 */
    getCorrectAnswer,
    getFeedbackData,
    getExamLabel,
    /* 피드백 생성 */
    feedbackGenerating,
    handleGenerateFeedbackForItem,
    /* 단건 저장 */
    itemSaving,
    handleSaveItemSingle,
    /* 기타 */
    handleRetryExamOptions,
  };
}
