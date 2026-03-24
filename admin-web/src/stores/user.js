/**
 * 사용자 Pinia 스토어
 * - 사용자 목록 조회 기능 (조회 전용, CUD 없음)
 * - 검색 조건과 페이징 상태를 관리한다.
 */
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import * as userApi from '@/api/user'

export const useUserStore = defineStore('user', () => {
  /* ========== 상태 ========== */

  /** 사용자 목록 (페이징된 결과) */
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
    email: ''
  })

  /* ========== 액션 ========== */

  /**
   * 사용자 목록 조회 (검색 조건 + 페이징 적용)
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
      const res = await userApi.getList(params)
      list.value = res.list || res.data || []
      total.value = res.total || 0
    } catch (error) {
      console.error('[User Store] fetchList 실패:', error)
    } finally {
      loading.value = false
    }
  }

  return {
    list,
    total,
    page,
    size,
    loading,
    searchParams,
    fetchList
  }
})
