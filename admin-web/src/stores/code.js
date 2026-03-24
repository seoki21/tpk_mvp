/**
 * 코드 Pinia 스토어
 * - 코드 목록 조회, 상세 조회, 생성, 수정, 삭제 기능
 * - 검색 조건과 페이징 상태를 관리한다.
 */
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import * as codeApi from '@/api/code'

export const useCodeStore = defineStore('code', () => {
  /* ========== 상태 ========== */

  /** 코드 목록 (페이징된 결과) */
  const list = ref([])

  /** 전체 건수 */
  const total = ref(0)

  /** 현재 페이지 (1부터 시작) */
  const page = ref(1)

  /** 페이지당 항목 수 */
  const size = ref(20)

  /** 로딩 상태 */
  const loading = ref(false)

  /** 검색 조건 */
  const searchParams = reactive({
    group_code: '',
    code_name: ''
  })

  /* ========== 액션 ========== */

  /**
   * 코드 목록 조회 (검색 조건 + 페이징 적용)
   */
  async function fetchList() {
    loading.value = true
    try {
      /* 빈 문자열 파라미터 제거 */
      const filtered = {}
      for (const [k, v] of Object.entries(searchParams)) {
        if (v !== '' && v !== null && v !== undefined) filtered[k] = v
      }
      const params = {
        page: page.value,
        size: size.value,
        ...filtered
      }
      const res = await codeApi.getList(params)
      list.value = res.list || res.data || []
      total.value = res.total || 0
    } catch (error) {
      console.error('[Code Store] fetchList 실패:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 코드 상세 조회
   * @param {string} codeGroup - 그룹코드
   * @param {string} code - 코드
   * @returns {Object} 상세 데이터
   */
  async function fetchDetail(codeGroup, code) {
    try {
      return await codeApi.getDetail(codeGroup, code)
    } catch (error) {
      console.error('[Code Store] fetchDetail 실패:', error)
      throw error
    }
  }

  /**
   * 코드 생성
   * @param {Object} data - 생성할 데이터
   */
  async function create(data) {
    try {
      const res = await codeApi.create(data)
      return res
    } catch (error) {
      console.error('[Code Store] create 실패:', error)
      throw error
    }
  }

  /**
   * 코드 수정
   * @param {string} codeGroup - 그룹코드
   * @param {string} code - 코드
   * @param {Object} data - 수정할 데이터
   */
  async function update(codeGroup, code, data) {
    try {
      const res = await codeApi.update(codeGroup, code, data)
      return res
    } catch (error) {
      console.error('[Code Store] update 실패:', error)
      throw error
    }
  }

  /**
   * 코드 삭제
   * @param {string} codeGroup - 그룹코드
   * @param {string} code - 코드
   */
  async function remove(codeGroup, code) {
    try {
      const res = await codeApi.remove(codeGroup, code)
      return res
    } catch (error) {
      console.error('[Code Store] remove 실패:', error)
      throw error
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
  }
})
