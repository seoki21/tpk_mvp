/**
 * 관리자 웹 라우터 정의
 * AdminLayout을 부모 라우트로 사용하고, 각 페이지를 children으로 배치한다.
 * 아직 미구현된 페이지는 DashboardView를 placeholder로 사용한다.
 */
import { createRouter, createWebHistory } from 'vue-router';

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
        /* 기출문항 변환(JSON) — 기출문제관리에서 진입 */
        {
          path: 'past-exam-questions/:examKey/:pdfKey/convert',
          name: 'examConvert',
          component: () => import('../views/ExamConvertView.vue')
        },
        /* 연습문제관리 */
        {
          path: 'practice-questions',
          name: 'practiceQuestions',
          component: () => import('../views/PracticeQuestionListView.vue')
        },
        /* 연습문제 생성(API) — 연습문제관리에서 등록 버튼 클릭 시 진입 */
        {
          path: 'practice-questions/create',
          name: 'practiceQuestionCreate',
          component: () => import('../views/PracticeQuestionCreateView.vue')
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
});

export default router;
