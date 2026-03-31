/**
 * 관리자 웹 라우터 정의
 * - AdminLayout을 부모 라우트로 사용하고, 각 페이지를 children으로 배치한다.
 * - 로그인 페이지는 AdminLayout 밖에 배치한다.
 * - beforeEach 가드로 미인증 시 로그인 페이지로 리다이렉트한다.
 */
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    /* 로그인 페이지 — AdminLayout 밖 (인증 불필요) */
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresAuth: false }
    },
    /* 관리자 페이지 — AdminLayout 내 (인증 필요) */
    {
      path: '/',
      component: () => import('../components/layout/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue')
        },
        /* 사용자관리 */
        {
          path: 'users',
          name: 'users',
          component: () => import('../views/UserListView.vue')
        },
        /* 기출시험관리 */
        {
          path: 'exam-questions',
          name: 'examQuestions',
          component: () => import('../views/ExamListView.vue')
        },
        /* 기출문제관리 */
        {
          path: 'past-exam-questions',
          name: 'pastExamQuestions',
          component: () => import('../views/PastExamQuestionView.vue')
        },
        /* 기출문제관리 (듣기) — 영역 전환 시 자동 이동 */
        {
          path: 'past-exam-listening',
          name: 'pastExamListening',
          component: () => import('../views/PastExamListeningView.vue')
        },
        /* 연습문항관리 */
        {
          path: 'practice-questions',
          name: 'practiceQuestions',
          component: () => import('../views/PracticeQuestionListView.vue')
        },
        {
          path: 'question-structures',
          name: 'questionStructures',
          component: () => import('../views/PlaceholderView.vue')
        },
        {
          path: 'question-types',
          name: 'questionTypes',
          component: () => import('../views/PlaceholderView.vue')
        },
        /* 관리자 관리 */
        {
          path: 'admins',
          name: 'admins',
          component: () => import('../views/AdminManageView.vue')
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
        }
      ]
    }
  ]
});

/* 네비게이션 가드 — 인증 필요 페이지에 토큰 없이 접근 시 로그인 페이지로 이동 */
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('admin_token');
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth !== false);

  if (requiresAuth && !token) {
    next({ name: 'login' });
  } else if (to.name === 'login' && token) {
    /* 이미 로그인된 상태에서 로그인 페이지 접근 시 대시보드로 이동 */
    next({ name: 'dashboard' });
  } else {
    next();
  }
});

export default router;
