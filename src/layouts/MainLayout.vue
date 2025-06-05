<template>
  <q-layout view="lHh Lpr lFf">
    <q-header v-if="$route.path !== '/'" elevated>
      <q-toolbar class="row justify-between items-center">
        <div class="text-subtitle1 row items-center">
          Current Project/User: {{ currentProject?.name || 'Unknown' }}/{{ currentUser?.username }}
          <q-btn flat round dense icon="logout" class="q-ml-sm" @click="handleLogout">
            <q-tooltip class="tooltip-custom">Log Out</q-tooltip>
          </q-btn>
        </div>
        
        <!-- 中间标题 -->
        <div v-if="$route.path === '/login'" class="page-title">
          Please Select or Add a User to Continue
        </div>
        <div v-if="$route.path === '/project-select'" class="page-title">
          Please Select a Project to Continue
        </div>
        <div v-if="$route.path === '/admin-dashboard'" class="admin-title">
          Admin Control Panel
        </div>
        <div v-if="$route.path === '/project-prompt'" class="page-title">
          Project Prompt Configuration
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

interface Project {
  id: string
  name: string
}

export default defineComponent({
  name: 'MainLayout',

  setup() {
    const router = useRouter()
    const $q = useQuasar()
    const currentUser = ref<User | null>(null)
    const currentProject = ref<Project | null>(null)

    // 监听 localStorage 的变化
    const updateCurrentUser = () => {
      const userStr = localStorage.getItem('currentUser')
      if (userStr) {
        currentUser.value = JSON.parse(userStr)
      } else {
        currentUser.value = null
      }
      
      const projectStr = localStorage.getItem('currentProject')
      if (projectStr) {
        try {
          // 尝试解析为JSON
          currentProject.value = JSON.parse(projectStr)
        } catch {
          // 如果解析失败，说明项目名是简单字符串
          currentProject.value = { id: projectStr, name: projectStr }
        }
      } else {
        currentProject.value = null
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
      currentProject,
      handleLogout,
    }
  },
})
</script>

<style lang="scss" scoped>
.q-toolbar {
  padding: 0 20px;

  .text-subtitle1 {
    min-width: 200px;
  }

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

  .page-title {
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
