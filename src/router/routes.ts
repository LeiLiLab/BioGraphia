import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        component: () => import('pages/LoginPage.vue'),
      },
      {
        path: 'project-select',
        component: () => import('pages/ProjectSelectPage.vue'),
      },
      {
        path: 'management',
        name: 'management',
        component: () => import('pages/ManagementPage.vue'),
      },
      {
        path: 'analysis',
        name: 'analysis',
        component: () => import('pages/PaperAnalysis.vue'),
      },
      {
        path: 'admin-dashboard',
        name: 'admin-dashboard',
        component: () => import('pages/AdminDashboard.vue'),
        meta: { requiresAdmin: true }
      },
      {
        path: 'relations-curation',
        name: 'relations-curation',
        component: () => import('pages/CurationManagementPage.vue'),
        meta: { requiresAdmin: true }
      },
      {
        path: 'curation-work',
        name: 'curation-work',
        component: () => import('pages/CurationWorkPage.vue'),
      },
      {
        path: 'curated-papers',
        name: 'curated-papers',
        component: () => import('pages/CuratedPaperManagement.vue'),
        meta: { requiresAdmin: true }
      },
      {
        path: 'paper-permissions',
        name: 'paper-permissions',
        component: () => import('pages/PaperPermissionManagement.vue'),
        meta: { requiresAdmin: true }
      },
      {
        path: 'project-prompt',
        name: 'project-prompt',
        component: () => import('pages/ProjectPromptPage.vue'),
      },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
