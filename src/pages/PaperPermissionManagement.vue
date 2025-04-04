<!-- Paper Permission Management Page -->
<template>
  <q-page class="q-pa-md">
    <!-- Back button -->
    <div class="q-mb-md">
      <q-btn 
        color="primary" 
        label="Back to dashboard" 
        @click="goToDashboard"
        flat
        class="back-btn"
        icon="arrow_back"
        icon-left
      />
    </div>
    
    <div class="text-h4 q-mb-lg text-center">Paper Permission Management</div>

    <!-- Papers table -->
    <div class="table-wrapper">
      <q-table
        :rows="papers"
        :columns="columns"
        row-key="pmid"
        :loading="loading"
        class="management-table q-mb-xl"
        :rows-per-page-options="[0]"
        :pagination="{rowsPerPage: 0}"
        hide-pagination
        bordered
        flat
      >
        <!-- Custom template for title column -->
        <template v-slot:body-cell-title="props">
          <q-td :props="props" style="font-size: 18px" class="text-center">
            <div class="ellipsis" style="max-width: 950px">
              {{ formatTitle(props.value) }}
              <q-tooltip>{{ props.value }}</q-tooltip>
            </div>
          </q-td>
        </template>

        <!-- Custom template for assigned users column -->
        <template v-slot:body-cell-assigned_user="props">
          <q-td :props="props" style="font-size: 18px" class="text-center">
            <div class="user-avatars-wrapper" v-if="props.row.assigned_user.length > 0">
              <div class="user-avatars" style="position: relative;">
                <div 
                  v-for="(user, index) in props.row.assigned_user.slice(0, 3)" 
                  :key="user"
                  class="user-avatar"
                  :style="{ 
                    zIndex: 3 - index, 
                    marginLeft: index > 0 ? '-13px' : '0',
                    backgroundColor: getAvatarColor(user)
                  }"
                >
                  {{ user.charAt(0).toUpperCase() }}
                </div>
                <div 
                  v-if="props.row.assigned_user.length > 3" 
                  class="more-users"
                  :style="{ marginLeft: '4px' }"
                >
                  +{{ props.row.assigned_user.length - 3 }}
                </div>
                <q-tooltip>{{ props.row.assigned_user.join(', ') }}</q-tooltip>
              </div>
              <q-btn
                round
                dense
                flat
                icon="edit"
                color="primary"
                @click="openAddUserDialog(props.row)"
                class="edit-btn"
              >
                <q-tooltip>Edit user access</q-tooltip>
              </q-btn>
            </div>
            <div v-else class="no-users">
              No assigned users
              <q-btn
                round
                dense
                flat
                icon="edit"
                color="primary"
                @click="openAddUserDialog(props.row)"
                class="edit-btn"
              >
                <q-tooltip>Edit user access</q-tooltip>
              </q-btn>
            </div>
          </q-td>
        </template>

        <!-- Custom header -->
        <template v-slot:header="props">
          <q-tr :props="props">
            <q-th
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              style="font-size: 18px"
              class="text-center"
            >
              {{ col.label }}
            </q-th>
          </q-tr>
        </template>
        
        <!-- Empty state message -->
        <template v-slot:no-data>
          <div class="full-width row flex-center q-py-xl">
            <div class="text-center">
              <q-icon name="info" size="2rem" color="grey" />
              <p class="text-h6 text-grey q-mt-md">No papers found</p>
              <p class="text-subtitle1 text-grey-7">Papers will appear here after they have been added to the system</p>
            </div>
          </div>
        </template>
      </q-table>
    </div>

    <!-- Add User Dialog -->
    <q-dialog v-model="showAddUserDialog" persistent maximized>
      <q-card style="max-width: 900px; margin: auto; height: 600px; padding: 20px 40px;">
        <!-- Title Section -->
        <q-card-section class="q-pb-md">
          <div class="text-h5 text-center">Manage Access</div>
        </q-card-section>

        <!-- Content Section -->
        <q-card-section class="q-py-md content-section" style="height: calc(100% - 140px); overflow: hidden;">
          <div class="row q-gutter-xl justify-center" style="height: 100%">
            <!-- Left Panel -->
            <div class="col panel-wrapper">
              <div class="text-h6 text-center q-mb-sm">Unaccess Users</div>
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
              <div class="text-h6 text-center q-mb-sm">Access Users</div>
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
          <q-btn flat label="SAVE" color="positive" @click="saveUserAccess" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import axios from 'axios'
import type { QTableColumn } from 'quasar'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { BACKEND_URL } from '../config/api'

interface Paper {
  pmid: string
  title: string
  assigned_user: string[]
  extraction_time?: string
}

interface User {
  id: number
  username: string
}

export default defineComponent({
  name: 'PaperPermissionManagement',

  setup() {
    const router = useRouter()
    const $q = useQuasar()
    const papers = ref<Paper[]>([])
    const loading = ref(true)
    const showAddUserDialog = ref(false)
    const selectedUser = ref('')
    const selectedPaper = ref<Paper | null>(null)
    const availableUsers = ref<string[]>([])
    const selectedAvailableUsers = ref<string[]>([])
    const selectedAssignedUsers = ref<string[]>([])
    const leftSelectAll = ref(false)
    const rightSelectAll = ref(false)
    const availableUsersList = ref<string[]>([])
    const selectedUsersList = ref<string[]>([])

    const formatTitle = (val: string) => {
      return val.length > 94 ? val.substring(0, 94) + '...' : val
    }

    const goToDashboard = () => {
      router.push('/admin-dashboard')
    }

    const columns: QTableColumn[] = [
      {
        name: 'pmid',
        label: 'PMID',
        field: 'pmid',
        align: 'center' as const,
        style: 'width: 150px; font-size: 18px',
      },
      {
        name: 'title',
        label: 'Title',
        field: 'title',
        align: 'center' as const,
        style: 'width: 562px', // 750px * 0.75 = 562px
      },
      {
        name: 'assigned_user',
        label: 'Assigned Users',
        field: 'assigned_user',
        align: 'center' as const,
        style: 'width: 488px', // 增加宽度以填充剩余空间 (1200 - 150 - 562 = 488)
      }
    ]

    const loadPapers = async () => {
      try {
        const [papersResponse, accessResponse] = await Promise.all([
          axios.get(`${BACKEND_URL}/api/papers`),
          axios.get(`${BACKEND_URL}/api/user-access`)
        ])
        
        // Get papers data
        const papersData = papersResponse.data.papers.map((paper: Paper) => ({
          ...paper,
          assigned_user: [] // Initialize empty array
        }))
        
        // Add user access data
        const accessData = accessResponse.data
        papersData.forEach((paper: Paper) => {
          if (accessData[paper.pmid]) {
            paper.assigned_user = accessData[paper.pmid].access_users.filter(
              (user: string) => user !== 'Main'
            )
          }
        })
        
        papers.value = papersData
      } catch (error) {
        console.error('Error loading papers:', error)
        papers.value = []
      } finally {
        loading.value = false
      }
    }

    const loadUsers = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/users`)
        // Filter out 'Admin' from available users
        availableUsers.value = response.data.users
          .map((user: User) => user.username)
          .filter((username: string) => username !== 'Admin')
      } catch (error) {
        console.error('Error loading users:', error)
        availableUsers.value = []
      }
    }

    const openAddUserDialog = (paper: Paper) => {
      selectedPaper.value = paper
      // Reset all selection states
      selectedAvailableUsers.value = []
      selectedAssignedUsers.value = []
      leftSelectAll.value = false
      rightSelectAll.value = false
      
      // Initialize the two lists
      availableUsersList.value = availableUsers.value.filter(
        user => !paper.assigned_user.includes(user)
      )
      selectedUsersList.value = [...paper.assigned_user]
      
      // Show the dialog
      showAddUserDialog.value = true
    }

    const selectAllAvailable = (val: boolean) => {
      if (val) {
        selectedAvailableUsers.value = [...availableUsersList.value]
      } else {
        selectedAvailableUsers.value = []
      }
    }

    const selectAllSelected = (val: boolean) => {
      if (val) {
        selectedAssignedUsers.value = [...selectedUsersList.value]
      } else {
        selectedAssignedUsers.value = []
      }
    }

    const moveToSelected = () => {
      // Move selected users from available to selected
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

    const moveToAvailable = () => {
      // Move selected users from selected to available
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

    const saveUserAccess = async () => {
      if (!selectedPaper.value) return

      try {
        // Save to backend
        await axios.post(`${BACKEND_URL}/api/user-access`, {
          pmid: selectedPaper.value.pmid,
          access_users: selectedUsersList.value
        })

        // Update local state
        const paper = papers.value.find(p => p.pmid === selectedPaper.value?.pmid)
        if (paper) {
          paper.assigned_user = [...selectedUsersList.value]
        }

        showAddUserDialog.value = false
        selectedPaper.value = null

        $q.notify({
          type: 'positive',
          message: 'User access updated successfully',
          position: 'top',
          timeout: 2000
        })
      } catch (error) {
        console.error('Error updating user access:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to update user access',
          position: 'top',
          timeout: 2000
        })
      }
    }

    const removeUserAccess = async (pmid: string, username: string) => {
      try {
        // Here you would typically call your API to remove user access
        // For now, we'll just update the local state
        const paper = papers.value.find(p => p.pmid === pmid)
        if (paper) {
          paper.assigned_user = paper.assigned_user.filter(user => user !== username)
        }

        $q.notify({
          type: 'positive',
          message: 'User access removed successfully',
          position: 'top',
          timeout: 2000
        })
      } catch (error) {
        console.error('Error removing user access:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to remove user access',
          position: 'top',
          timeout: 2000
        })
      }
    }

    // 预定义的颜色数组
    const avatarColors = [
      '#1976D2', // 蓝色
      '#388E3C', // 绿色
      '#D32F2F', // 红色
      '#7B1FA2', // 紫色
      '#C2185B', // 粉色
      '#F57C00', // 橙色
      '#0097A7', // 青色
      '#00796B', // 青绿色
      '#FBC02D', // 黄色
      '#6D4C41', // 棕色
    ]

    // 根据用户名生成固定的颜色
    const getAvatarColor = (username: string) => {
      // 使用用户名生成一个固定的索引
      const index = username.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
      return avatarColors[index % avatarColors.length]
    }

    onMounted(() => {
      loadPapers()
      loadUsers()
    })

    return {
      papers,
      columns,
      loading,
      formatTitle,
      goToDashboard,
      showAddUserDialog,
      selectedUser,
      availableUsers,
      selectedAvailableUsers,
      selectedAssignedUsers,
      leftSelectAll,
      rightSelectAll,
      availableUsersList,
      selectedUsersList,
      selectAllAvailable,
      selectAllSelected,
      moveToSelected,
      moveToAvailable,
      saveUserAccess,
      removeUserAccess,
      openAddUserDialog,
      getAvatarColor,
    }
  },
})
</script>

<style lang="scss" scoped>
.back-btn {
  font-size: 16px;
  padding: 8px 16px;
}

.table-wrapper {
  position: relative;
}

.management-table {
  :deep(.q-table__bottom) {
    font-size: 18px !important;

    .q-table__control {
      font-size: 18px !important;
    }

    .q-field__native {
      font-size: 18px !important;
    }

    .q-field__input {
      font-size: 18px !important;
    }

    .q-select__dropdown-icon {
      font-size: 18px !important;
    }
  }

  :deep(.q-table) {
    border: 1px solid rgba(0, 0, 0, 0.12);

    th,
    td {
      border: 1px solid rgba(0, 0, 0, 0.12) !important;
    }
  }

  .ellipsis {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.user-avatars-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 4px;
  gap: 12px;
}

.user-avatars {
  display: flex;
  align-items: center;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 500;
  border: 2px solid white;
  flex-shrink: 0;
  transition: background-color 0.3s ease;  // 添加颜色过渡效果
}

.more-users {
  font-size: 16px;
  font-weight: 500;
  color: var(--q-primary);
  display: flex;
  align-items: center;
  padding-left: 4px;
  min-width: 24px;  // 确保数字有足够空间
}

.edit-btn {
  margin-left: 4px;
  font-size: 20px;
}

.no-users {
  color: #666;
  font-style: italic;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

:deep(.q-tooltip) {
  font-size: 14px;
  background: rgba(0, 0, 0, 0.8);
  padding: 8px 12px;
  border-radius: 4px;
  max-width: none;
}

.user-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  align-items: center;
  
  .user-chip {
    font-size: 14px;
  }
}

:deep(.q-tooltip) {
  font-size: 18px;
  background: rgba(0, 0, 0, 0.8);
  max-width: 950px;
  white-space: normal;
  word-wrap: break-word;
  padding: 8px 12px;
}

:deep(.q-menu) {
  .q-item {
    font-size: 18px !important;
  }
}

.q-mb-xl {
  margin-bottom: 48px;
}

/* Global notification styles */
:global(.q-notification) {
  min-height: 50px !important;
  padding: 12px 24px !important;
}

:global(.q-notification__message) {
  font-size: 18px !important;
}

:global(.q-notification--warning) {
  background-color: #ffd700 !important;
  color: #000000 !important;
}

:deep(.notification-message) {
  font-size: 18px !important;
}

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
    font-size: 20px;
    font-weight: bold;
  }
}

.scroll-list {
  flex: 1;
  overflow-y: auto;
  
  &::-webkit-scrollbar {
    width: 10px;
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
    font-size: 2em;
  }
  :deep(.q-checkbox__label) {
    font-size: 20px;
    line-height: 1.8;
  }
}

:deep(.q-item) {
  padding: 16px;
  min-height: 60px;
  
  .q-checkbox {
    width: 100%;
    justify-content: center;
  }
}

:deep(.text-h5) {
  font-size: 24px;
  font-weight: 500;
}

:deep(.text-h6) {
  font-size: 20px;
  font-weight: 500;
}
</style> 