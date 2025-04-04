<template>
  <q-layout view="lHh Lpr lFf">
    <q-header v-if="$route.path !== '/'" elevated>
      <q-toolbar class="row justify-between items-center">
        <div class="text-h6 row items-center">
          Current User: {{ currentUser?.username }}
          <q-btn flat round dense icon="logout" class="q-ml-sm" @click="handleLogout">
            <q-tooltip class="tooltip-custom">Log Out</q-tooltip>
          </q-btn>
        </div>
        <div v-if="$route.path === '/admin-dashboard'" class="admin-title">
          Admin Control Panel
        </div>
        <div v-if="$route.query.mode === 'temp'" class="temp-warning">
          ⚠️ Editing in Temporary Directory
        </div>
        <div class="text-h6" style="visibility: hidden">Placeholder</div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script lang="ts">
import { defineComponent, ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'

interface User {
  id: number
  username: string
}

export default defineComponent({
  name: 'MainLayout',

  setup() {
    const router = useRouter()
    const $q = useQuasar()
    const currentUser = ref<User | null>(null)

    // 监听 localStorage 的变化
    const updateCurrentUser = () => {
      const userStr = localStorage.getItem('currentUser')
      if (userStr) {
        currentUser.value = JSON.parse(userStr)
      } else {
        currentUser.value = null
      }
    }

    // 初始化时获取用户信息
    updateCurrentUser()

    // 创建一个定时器来检查 localStorage 的变化
    const checkInterval = setInterval(updateCurrentUser, 100)

    // 组件卸载时清除定时器
    onBeforeUnmount(() => {
      clearInterval(checkInterval)
    })

    const handleLogout = () => {
      const username = currentUser.value?.username
      localStorage.removeItem('currentUser')
      router.push('/')
      $q.notify({
        type: 'positive',
        message: `Successfully logged out${username ? ` from ${username}` : ''}`,
        position: 'top',
        timeout: 2000,
        html: true,
        classes: 'text-h6',
      })
    }

    return {
      currentUser,
      handleLogout,
    }
  },
})
</script>

<style lang="scss" scoped>
.q-toolbar {
  padding: 0 20px;

  .text-h6 {
    min-width: 200px;
  }

  .app-logo {
    width: 32px;
    height: 32px;
    object-fit: cover;
    border-radius: 4px;
  }

  .app-title {
    font-size: 18px;
    font-weight: 600;
    color: white;
  }

  .app-brand {
    margin-right: 16px;
  }

  .q-toolbar-title {
    flex: 1;
  }

  .q-btn {
    color: white;
    opacity: 0.8;
    transition: opacity 0.3s ease;

    &:hover {
      opacity: 1;
    }
  }

  .temp-warning {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    font-size: 24px;
    font-weight: 500;
    color: #ffeb3b;
    text-align: center;
  }

  .admin-title {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    font-size: 24px;
    font-weight: 500;
    color: white;
    text-align: center;
  }
}

:deep(.q-tooltip.q-tooltip--style) {
  font-size: 8px !important;
  padding: 4px 8px !important;
  min-height: 24px !important;
  background: rgba(97, 97, 97, 0.9) !important;
}
</style>
