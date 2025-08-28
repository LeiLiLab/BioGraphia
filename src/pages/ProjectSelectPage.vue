<template>
  <q-page class="project-select-page">
    <div class="content-container">
      <div class="project-box q-pa-lg">
        <div class="row items-center q-mb-md">
          <q-select
            v-model="selectedProject"
            :options="userProjects"
            label="Select Project"
            class="col project-select"
            outlined
            color="primary"
            bg-color="white"
            behavior="menu"
            popup-content-class="project-select-popup"
          >
            <template v-slot:prepend>
              <q-icon name="folder" color="primary" />
            </template>
          </q-select>
        </div>

        <!-- Continue Button -->
        <div class="row q-mb-md">
          <q-btn
            label="Continue"
            color="primary"
            text-color="white"
            size="lg"
            class="col continue-btn"
            @click="continueToLogin"
            :disable="!selectedProject"
          />
        </div>

        <!-- 启用添加项目按钮 (仅Admin可见) -->
        <div class="row" v-if="isAdmin">
          <q-btn
            color="secondary" 
            text-color="white"
            label="Create New Project"
            size="lg"
            class="col continue-btn"
            @click="showAddProjectDialog = true" 
          />
        </div>
        
        <!-- 管理项目权限按钮 (仅Admin可见) -->
        <div class="row q-mt-md" v-if="isAdmin">
          <q-btn
            color="accent" 
            text-color="white"
            label="Manage Project Permissions"
            size="lg"
            class="col continue-btn"
            @click="showProjectPermissionDialog = true" 
          />
        </div>
      </div>
    </div>

    <!-- 创建新项目对话框 -->
    <q-dialog v-model="showAddProjectDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Create New Project</div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="newProjectName"
            label="Enter project name"
            outlined
            class="add-project-input"
            :rules="[(val) => !!val || 'Project name is required']"
            @keyup.enter="handleAddProject" 
          >
            <template v-slot:error>
              <div class="error-message">Project name is required</div>
            </template>
          </q-input>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn
            flat
            label="Create & Continue"
            color="primary"
            @click="handleAddProject"
            :disable="!newProjectName"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
    
    <!-- 项目权限管理对话框 (仅Admin可见) -->
    <q-dialog v-model="showProjectPermissionDialog" persistent maximized>
      <q-card style="max-width: 900px; margin: auto; height: 600px; padding: 20px 40px;">
        <!-- Title Section -->
        <q-card-section class="q-pb-md">
          <div class="text-h5 text-center">Manage Project Access</div>
          <div class="text-subtitle1 text-center q-mt-sm" v-if="selectedProjectForPermission">
            Project: {{ selectedProjectForPermission }}
          </div>
        </q-card-section>
        
        <!-- Project Selection -->
        <q-card-section class="q-py-md">
          <q-select
            v-model="selectedProjectForPermission"
            :options="allProjects"
            label="Select Project to Manage"
            outlined
            color="primary"
            @update:model-value="loadProjectPermissions"
          />
        </q-card-section>

        <!-- Content Section (显示仅当选择了项目) -->
        <q-card-section v-if="selectedProjectForPermission" class="q-py-md content-section" style="height: calc(100% - 220px); overflow: hidden;">
          <div class="row q-gutter-xl justify-center" style="height: 100%">
            <!-- Left Panel -->
            <div class="col panel-wrapper">
              <div class="text-h6 text-center q-mb-sm">Users Without Access</div>
              <q-card bordered class="user-selection-panel">
                <q-card-section style="height: 100%; padding: 0;">
                  <div class="selection-container">
                    <div class="select-all-wrapper q-pa-md">
                      <q-checkbox
                        v-model="leftSelectAll"
                        label="SELECT ALL"
                        @update:model-value="selectAllAvailable"
                        class="select-all-checkbox"
                      />
                    </div>
                    <q-list separator class="scroll-list">
                      <q-item v-for="user in availableUsersList" :key="user">
                        <q-item-section class="text-center">
                          <q-checkbox
                            v-model="selectedAvailableUsers"
                            :val="user"
                            :label="user"
                            class="user-checkbox"
                          />
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <!-- Center Arrows -->
            <div class="col-auto self-center">
              <div class="column q-gutter-y-md justify-center">
                <q-btn
                  flat
                  round
                  color="primary"
                  icon="arrow_forward"
                  @click="moveToSelected"
                  :disable="!selectedAvailableUsers.length"
                  size="lg"
                />
                <q-btn
                  flat
                  round
                  color="primary"
                  icon="arrow_back"
                  @click="moveToAvailable"
                  :disable="!selectedAssignedUsers.length"
                  size="lg"
                />
              </div>
            </div>

            <!-- Right Panel -->
            <div class="col panel-wrapper">
              <div class="text-h6 text-center q-mb-sm">Users With Access</div>
              <q-card bordered class="user-selection-panel">
                <q-card-section style="height: 100%; padding: 0;">
                  <div class="selection-container">
                    <div class="select-all-wrapper q-pa-md">
                      <q-checkbox
                        v-model="rightSelectAll"
                        label="SELECT ALL"
                        @update:model-value="selectAllSelected"
                        class="select-all-checkbox"
                      />
                    </div>
                    <q-list separator class="scroll-list">
                      <q-item v-for="user in selectedUsersList" :key="user">
                        <q-item-section class="text-center">
                          <q-checkbox
                            v-model="selectedAssignedUsers"
                            :val="user"
                            :label="user"
                            class="user-checkbox"
                          />
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right" class="q-pa-md">
          <q-btn flat label="CANCEL" color="negative" v-close-popup />
          <q-btn 
            flat 
            label="SAVE" 
            color="positive" 
            @click="saveProjectPermissions" 
            :disable="!selectedProjectForPermission"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { BACKEND_URL } from '../config/api'

// 用户接口定义
interface User {
  username: string;
  password: string;
  projects: string[];
}

// 当前用户接口定义
interface CurrentUser {
  id: number;
  username: string;
}

export default defineComponent({
  name: 'ProjectSelectPage',

  setup() {
    const router = useRouter()
    const $q = useQuasar()
    const allProjects = ref<string[]>([])
    const userProjects = ref<string[]>([])
    const selectedProject = ref<string | null>(null)
    const showAddProjectDialog = ref(false)
    const newProjectName = ref('')
    const currentUser = ref<CurrentUser | null>(null)
    const isAdmin = ref(false)
    
    // 项目权限管理
    const showProjectPermissionDialog = ref(false)
    const selectedProjectForPermission = ref<string | null>(null)
    const allUsers = ref<string[]>([])
    const availableUsersList = ref<string[]>([])
    const selectedUsersList = ref<string[]>([])
    const selectedAvailableUsers = ref<string[]>([])
    const selectedAssignedUsers = ref<string[]>([])
    const leftSelectAll = ref(false)
    const rightSelectAll = ref(false)

    // Load projects from backend
    const loadProjects = async () => {
      try {
        // 获取所有项目列表
        const response = await axios.get(`${BACKEND_URL}/api/projects`)
        allProjects.value = response.data.projects
        
        // 获取用户信息
        const userStr = localStorage.getItem('currentUser')
        if (userStr) {
          currentUser.value = JSON.parse(userStr) as CurrentUser
          isAdmin.value = currentUser.value.username === 'Admin'
          
          // 如果是Admin用户，显示所有项目
          if (isAdmin.value) {
            userProjects.value = [...allProjects.value]
          } else {
            // 非Admin用户，加载用户有权限的项目
            try {
              const userResponse = await axios.get(`${BACKEND_URL}/api/users`)
              const users = userResponse.data.users as User[]
              const currentUserData = users.find((u: User) => u.username === currentUser.value?.username)
              
              if (currentUserData && currentUserData.projects) {
                userProjects.value = currentUserData.projects
              } else {
                // 默认只有default项目
                userProjects.value = ['default']
              }
            } catch (error) {
              console.error('Error loading user projects:', error)
              userProjects.value = ['default'] // 默认至少有default项目
            }
          }
        }
        
        // 设置默认选中项目
        if (userProjects.value.length > 0 && !selectedProject.value) {
          selectedProject.value = userProjects.value[0] || null
        }
      } catch (error) {
        console.error('加载项目列表时出错:', error)
        $q.notify({
          type: 'negative',
          message: '加载项目列表失败，请检查网络连接',
          position: 'top',
          timeout: 3000,
        })
      }
    }
    
    // 加载所有用户列表
    const loadUsers = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/users`)
        const users = response.data.users as User[]
        allUsers.value = users.map((user: User) => user.username)
      } catch (error) {
        console.error('Error loading users:', error)
        allUsers.value = []
      }
    }
    
    // 加载项目权限数据
    const loadProjectPermissions = async () => {
      if (!selectedProjectForPermission.value) return
      
      try {
        const response = await axios.get(`${BACKEND_URL}/api/users`)
        const users = response.data.users as User[]
        
        // 获取有权限的用户
        selectedUsersList.value = users
          .filter((user: User) => 
            user.projects && 
            user.projects.includes(selectedProjectForPermission.value as string) &&
            user.username !== 'Admin' // Admin默认有所有权限，不在列表中显示
          )
          .map((user: User) => user.username)
        
        // 获取无权限的用户
        availableUsersList.value = users
          .filter((user: User) => 
            user.username !== 'Admin' && 
            (!user.projects || !user.projects.includes(selectedProjectForPermission.value as string))
          )
          .map((user: User) => user.username)
        
        // 重置选择状态
        selectedAvailableUsers.value = []
        selectedAssignedUsers.value = []
        leftSelectAll.value = false
        rightSelectAll.value = false
      } catch (error) {
        console.error('Error loading project permissions:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load project permissions data',
          position: 'top',
          timeout: 3000,
        })
      }
    }

    // 处理继续登录操作
    const continueToLogin = async () => {
      if (selectedProject.value) {
        try {
          const response = await axios.post(`${BACKEND_URL}/api/projects/set-current`, {
            project_name: selectedProject.value,
          })
          if (response.data.success) {
            const projectData = {
              id: selectedProject.value,
              name: selectedProject.value,
            }
            localStorage.setItem('currentProject', JSON.stringify(projectData))
            console.log('已存储项目到localStorage:', projectData)
            
            // 获取当前用户信息
            const currentUserStr = localStorage.getItem('currentUser')
            if (!currentUserStr) {
              router.push('/')
              return
            }
            
            const currentUser = JSON.parse(currentUserStr) as CurrentUser
            if (currentUser.username === 'Admin') {
              router.push('/admin-dashboard')
            } else {
              router.push('/management')
            }
          } else {
            $q.notify({
              type: 'negative',
              message: response.data.error || 'Failed to set current project',
              position: 'top',
              timeout: 2000,
              html: true,
              classes: 'text-h6',
            })
          }
        } catch (error) {
          console.error('Error setting current project:', error)
          $q.notify({
            type: 'negative',
            message: 'Error setting project. Please try again.',
            position: 'top',
            timeout: 2000,
            html: true,
            classes: 'text-h6',
          })
        }
      }
    }

    // 处理添加新项目
    const handleAddProject = async () => {
      if (!newProjectName.value) {
        $q.notify({
          type: 'negative',
          message: 'Project name cannot be empty',
          position: 'top',
          timeout: 2000,
        })
        return
      }

      try {
        const response = await axios.post(`${BACKEND_URL}/api/projects`, {
          name: newProjectName.value,
        })

        if (response.data.success) {
          $q.notify({
            type: 'positive',
            message: `Project '${newProjectName.value}' created successfully!`,
            position: 'top',
            timeout: 2000,
          })
          await loadProjects() // 重新加载项目列表
          selectedProject.value = newProjectName.value // 设置新创建的项目为当前选中
          
          // 设置当前项目
          const projectSetResponse = await axios.post(`${BACKEND_URL}/api/projects/set-current`, {
            project_name: newProjectName.value,
          })
          
          if (projectSetResponse.data.success) {
            // 存储项目信息到本地存储
            const projectData = {
              id: newProjectName.value,
              name: newProjectName.value,
            }
            localStorage.setItem('currentProject', JSON.stringify(projectData))
            
            // 自动设置Admin用户为当前用户
            const adminUser = {
              id: 1,
              username: 'Admin'
            }
            localStorage.setItem('currentUser', JSON.stringify(adminUser))
            
            // 清空输入框
            newProjectName.value = ''
            
            // 关闭对话框
            showAddProjectDialog.value = false
            
            // 导航到项目提示词配置页面，而不是登录页面
            router.push('/project-prompt')
          } else {
            $q.notify({
              type: 'negative',
              message: projectSetResponse.data.error || 'Failed to set current project',
              position: 'top',
              timeout: 3000,
            })
          }
        } else {
          $q.notify({
            type: 'negative',
            message: response.data.error || 'Failed to create project',
            position: 'top',
            timeout: 3000,
          })
        }
      } catch (error) {
        console.error('Error creating project:', error)
        let errorMessage = 'Failed to create project. Please try again.'
        if (axios.isAxiosError(error) && error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        } else if (error instanceof Error) {
            // 可以选择性地使用 error.message，或者保持通用错误信息
            // errorMessage = error.message; 
        }
        $q.notify({
          type: 'negative',
          message: errorMessage,
          position: 'top',
          timeout: 3000,
        })
      }
    }
    
    // 项目权限管理功能
    
    // 全选/取消全选左侧列表
    const selectAllAvailable = (val: boolean) => {
      if (val) {
        selectedAvailableUsers.value = [...availableUsersList.value]
      } else {
        selectedAvailableUsers.value = []
      }
    }

    // 全选/取消全选右侧列表
    const selectAllSelected = (val: boolean) => {
      if (val) {
        selectedAssignedUsers.value = [...selectedUsersList.value]
      } else {
        selectedAssignedUsers.value = []
      }
    }

    // 将用户从左侧移动到右侧
    const moveToSelected = () => {
      // 将选中的用户从左侧移动到右侧
      selectedUsersList.value = [
        ...selectedUsersList.value,
        ...selectedAvailableUsers.value
      ]
      availableUsersList.value = availableUsersList.value.filter(
        user => !selectedAvailableUsers.value.includes(user)
      )
      selectedAvailableUsers.value = []
      leftSelectAll.value = false
    }

    // 将用户从右侧移动到左侧
    const moveToAvailable = () => {
      // 将选中的用户从右侧移动到左侧
      availableUsersList.value = [
        ...availableUsersList.value,
        ...selectedAssignedUsers.value
      ]
      selectedUsersList.value = selectedUsersList.value.filter(
        user => !selectedAssignedUsers.value.includes(user)
      )
      selectedAssignedUsers.value = []
      rightSelectAll.value = false
    }

    // 保存项目权限设置
    const saveProjectPermissions = async () => {
      if (!selectedProjectForPermission.value) return
      
      try {
        // 获取所有用户信息
        const response = await axios.get(`${BACKEND_URL}/api/users`)
        const users = response.data.users as User[]
        
        // 更新每个用户的项目权限
        const updatedUsers = users.map((user: User) => {
          // Admin用户始终保留所有项目的权限
          if (user.username === 'Admin') return user
          
          // 初始化projects数组，如果不存在
          if (!user.projects) {
            user.projects = []
          }
          
          // 如果用户在有权限列表中，确保项目在其projects数组中
          if (selectedUsersList.value.includes(user.username)) {
            if (!user.projects.includes(selectedProjectForPermission.value as string)) {
              user.projects.push(selectedProjectForPermission.value as string)
            }
          } else {
            // 否则从projects数组中移除该项目
            user.projects = user.projects.filter((p: string) => p !== selectedProjectForPermission.value)
          }
          
          return user
        })
        
        // 将更新的用户数据保存回后端
        await axios.post(`${BACKEND_URL}/api/users/update-projects`, {
          users: updatedUsers
        })
        
        showProjectPermissionDialog.value = false
        
        $q.notify({
          type: 'positive',
          message: 'Project permissions updated successfully',
          position: 'top',
          timeout: 2000
        })
        
        // 重新加载项目列表，以防当前用户的权限发生变化
        await loadProjects()
      } catch (error) {
        console.error('Error saving project permissions:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to save project permissions',
          position: 'top',
          timeout: 3000,
        })
      }
    }

    onMounted(async () => {
      // 检查是否已登录
      const currentUserStr = localStorage.getItem('currentUser')
      if (!currentUserStr) {
        router.push('/')
        return
      }
      
      // 加载用户数据
      currentUser.value = JSON.parse(currentUserStr) as CurrentUser
      isAdmin.value = currentUser.value.username === 'Admin'
      
      // 加载项目和用户列表
      await loadProjects()
      
      // 如果是Admin，加载所有用户以便管理权限
      if (isAdmin.value) {
        await loadUsers()
      }
    })

    return {
      allProjects,
      userProjects,
      selectedProject,
      showAddProjectDialog,
      newProjectName,
      continueToLogin,
      handleAddProject,
      isAdmin,
      
      // 项目权限管理相关
      showProjectPermissionDialog,
      selectedProjectForPermission,
      availableUsersList,
      selectedUsersList,
      selectedAvailableUsers,
      selectedAssignedUsers,
      leftSelectAll,
      rightSelectAll,
      selectAllAvailable,
      selectAllSelected,
      moveToSelected,
      moveToAvailable,
      loadProjectPermissions,
      saveProjectPermissions
    }
  },
})
</script>

<style lang="scss" scoped>
.project-select-page {
  min-height: 100vh;
  background: white;
  position: relative;
}

.content-container {
  text-align: center;
  padding: 2rem;
  width: 100%;
  max-width: 500px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.project-box {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.continue-btn {
  font-size: 1.2rem;
}

.add-project-input {
  margin-bottom: 1rem;
}

.error-message {
  color: #C10015;
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

.project-select-popup {
  max-height: 40vh;
}

/* 增大项目选择的字体大小 */
:deep(.q-field__label) {
  font-size: 1.2rem;
  font-weight: 500;
}

:deep(.q-field__native) {
  font-size: 1.5rem !important;
}

:deep(.q-select__dropdown-icon) {
  font-size: 1.5rem;
}

/* 项目下拉菜单样式 */
:deep(.q-menu) {
  font-size: 1.3rem;
  
  .q-item {
    min-height: 48px;
  }
  
  .q-item__label {
    font-size: 1.3rem;
  }
}

/* 权限管理对话框样式 */
.content-section {
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.user-selection-panel {
  flex: 1;
  width: 300px;
  background: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.selection-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.select-all-wrapper {
  background: white;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.select-all-checkbox {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  
  :deep(.q-checkbox__inner) {
    font-size: 2em;
  }
  :deep(.q-checkbox__label) {
    font-size: 16px;
    font-weight: bold;
  }
}

.scroll-list {
  flex: 1;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f1f1;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: #555;
  }
}

.user-checkbox {
  :deep(.q-checkbox__inner) {
    font-size: 1.5em;
  }
  :deep(.q-checkbox__label) {
    font-size: 16px;
    line-height: 1.5;
  }
}

:deep(.q-item) {
  padding: 12px;
  min-height: 48px;
  
  .q-checkbox {
    width: 100%;
    justify-content: center;
  }
}
</style> 