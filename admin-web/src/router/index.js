/**
 * 관리자 웹 라우터 정의
 * AdminLayout을 부모 라우트로 사용하고, 각 페이지를 children으로 배치한다.
 * 아직 미구현된 페이지는 DashboardView를 placeholder로 사용한다.
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('../components/layout/AdminLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue')
        },
        /* 그룹코드관리 */
        {
          path: 'group-codes',
          name: 'groupCodes',
          component: () => import('../views/GroupCodeListView.vue')
        },
        /* 코드관리 */
        {
          path: 'codes',
          name: 'codes',
          component: () => import('../views/CodeListView.vue')
        },
        /* 아래 메뉴는 추후 구현 예정 — placeholder */
        {
          path: 'users',
          name: 'users',
          component: () => import('../views/DashboardView.vue')
        },
        {
          path: 'exam-questions',
          name: 'examQuestions',
          component: () => import('../views/DashboardView.vue')
        },
        {
          path: 'practice-questions',
          name: 'practiceQuestions',
          component: () => import('../views/DashboardView.vue')
        },
        {
          path: 'question-structures',
          name: 'questionStructures',
          component: () => import('../views/DashboardView.vue')
        },
        {
          path: 'question-types',
          name: 'questionTypes',
          component: () => import('../views/DashboardView.vue')
        }
      ]
    }
  ]
})

export default router
