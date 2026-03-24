/**
 * 그룹코드 Pinia 스토어
 * - 그룹코드 목록 조회, 전체 목록 조회, 상세 조회, 생성, 수정, 삭제 기능
 * - 검색 조건과 페이징 상태를 관리한다.
 */
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import * as groupCodeApi from '@/api/groupCode'

export const useGroupCodeStore = defineStore('groupCode', () => {
  /* ========== 상태 ========== */

  /** 그룹코드 목록 (페이징된 결과) */
  const list = ref([])

  /** 전체 건수 */
  const total = ref(0)

  /** 현재 페이지 (1부터 시작) */
  const page = ref(1)

  /** 페이지당 항목 수 */
  const size = ref(20)

  /** 로딩 상태 */
  const loading = ref(false)

  /** 전체 그룹코드 목록 (셀렉트박스용) */
  const allGroupCodes = ref([])

  /** 검색 조건 */
  const searchParams = reactive({
    group_code: '',
    group_name: ''
  })

  /* ========== 액션 ========== */

  /**
   * 그룹코드 목록 조회 (검색 조건 + 페이징 적용)
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
      const res = await groupCodeApi.getList(params)
      list.value = res.list || res.data || []
      total.value = res.total || 0
    } catch (error) {
      console.error('[GroupCode Store] fetchList 실패:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 전체 그룹코드 목록 조회 (셀렉트박스 등에서 사용)
   */
  async function fetchAllGroupCodes() {
    try {
      const res = await groupCodeApi.getAll()
      allGroupCodes.value = Array.isArray(res) ? res : (res.data || [])
    } catch (error) {
      console.error('[GroupCode Store] fetchAllGroupCodes 실패:', error)
    }
  }

  /**
   * 그룹코드 상세 조회
   * @param {string} groupCode - 그룹코드 PK
   * @returns {Object} 상세 데이터
   */
  async function fetchDetail(groupCode) {
    try {
      return await groupCodeApi.getDetail(groupCode)
    } catch (error) {
      console.error('[GroupCode Store] fetchDetail 실패:', error)
      throw error
    }
  }

  /**
   * 그룹코드 생성
   * @param {Object} data - 생성할 데이터
   */
  async function create(data) {
    try {
      const res = await groupCodeApi.create(data)
      return res
    } catch (error) {
      console.error('[GroupCode Store] create 실패:', error)
      throw error
    }
  }

  /**
   * 그룹코드 수정
   * @param {string} groupCode - 수정 대상 PK
   * @param {Object} data - 수정할 데이터
   */
  async function update(groupCode, data) {
    try {
      const res = await groupCodeApi.update(groupCode, data)
      return res
    } catch (error) {
      console.error('[GroupCode Store] update 실패:', error)
      throw error
    }
  }

  /**
   * 그룹코드 삭제
   * @param {string} groupCode - 삭제 대상 PK
   */
  async function remove(groupCode) {
    try {
      const res = await groupCodeApi.remove(groupCode)
      return res
    } catch (error) {
      console.error('[GroupCode Store] remove 실패:', error)
      throw error
    }
  }

  return {
    list,
    total,
    page,
    size,
    loading,
    allGroupCodes,
    searchParams,
    fetchList,
    fetchAllGroupCodes,
    fetchDetail,
    create,
    update,
    remove
  }
})
