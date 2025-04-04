import { defineRouter } from '#q-app/wrappers'
import {
  createMemoryHistory,
  createRouter,
  createWebHashHistory,
  createWebHistory,
} from 'vue-router'
import routes from './routes'
// 移除不适合在路由守卫中使用的导入
// import { useQuasar } from 'quasar'

/*
 * If not building with SSR mode, you can
 * directly export the Router instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Router instance.
 */

export default defineRouter(function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : process.env.VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
  })

  // 添加导航守卫
  Router.beforeEach((to, from, next) => {
    // 检查路由是否需要管理员权限
    if (to.matched.some(record => record.meta.requiresAdmin)) {
      // 从本地存储获取当前用户
      const userJson = localStorage.getItem('currentUser')
      if (userJson) {
        const user = JSON.parse(userJson)
        // 检查当前用户是否为Admin
        if (user.username === 'Admin') {
          next() // 允许访问
        } else {
          // 非Admin用户，重定向到管理页面
          next('/management')
          // 不在这里使用useQuasar，因为它只能在组件setup函数中使用
          // 改为使用简单的控制台日志
          console.warn('只有Admin用户才能访问管理员面板')
        }
      } else {
        // 未登录，重定向到登录页
        next('/')
      }
    } else {
      // 不需要管理员权限的路由正常放行
      next()
    }
  })

  return Router
})
