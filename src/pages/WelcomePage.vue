<template>
  <q-page class="welcome-page">
    <!-- Add header section -->
    <div class="header-section bg-primary text-white q-pa-md">
      <div class="text-h5 text-center">Please Select or Add a User to Continue</div>
    </div>

    <div class="content-container">
      <h1 class="text-h2 text-primary q-mb-xl text-center">Welcome</h1>

      <div class="login-box q-pa-lg">
        <div class="row items-center q-mb-md">
          <q-select
            v-model="selectedUser"
            :options="users"
            option-label="username"
            label="Selected User"
            class="col user-select"
            outlined
            color="primary"
            bg-color="white"
            behavior="menu"
            popup-content-class="user-select-popup"
          >
            <template v-slot:prepend>
              <q-icon name="person" color="primary" />
            </template>
            <template v-slot:option="{ itemProps, opt }">
              <q-item v-bind="itemProps">
                <q-item-section class="text-center">
                  {{ opt.username }}
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>

        <!-- Login Button -->
        <div class="row q-mb-md">
          <q-btn
            label="Log In"
            color="primary"
            text-color="white"
            size="lg"
            class="col login-btn"
            @click="handleLogin"
            :disable="!selectedUser"
          />
        </div>

        <!-- Add New User Dialog Trigger -->
        <div class="row">
          <q-btn
            color="primary"
            text-color="white"
            label="Add New User"
            size="lg"
            class="col login-btn"
            @click="showAddUserDialog = true"
          />
        </div>
      </div>
    </div>

    <!-- Add User Dialog -->
    <q-dialog v-model="showAddUserDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Add New User</div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="newUsername"
            label="Enter new username"
            outlined
            class="add-user-input"
            :rules="[(val) => !!val || 'Username is required']"
          >
            <template v-slot:error>
              <div class="error-message">Username is required</div>
            </template>
          </q-input>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn
            flat
            label="Add & Login"
            color="primary"
            @click="handleAddUser"
            :disable="!newUsername"
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

interface User {
  id: number
  username: string
}

export default defineComponent({
  name: 'WelcomePage',

  setup() {
    const router = useRouter()
    const $q = useQuasar()
    const users = ref<User[]>([])
    const selectedUser = ref<User | null>(null)
    const showAddUserDialog = ref(false)
    const newUsername = ref('')

    // Load users from JSON file
    const loadUsers = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/users`)
        users.value = response.data.users

        // 设置 Admin 为默认用户
        const adminUser = users.value.find((user) => user.username === 'Admin')
        if (adminUser) {
          selectedUser.value = adminUser
        }
      } catch (error) {
        console.error('Error loading users:', error)
      }
    }

    // Handle login
    const handleLogin = () => {
      if (selectedUser.value) {
        localStorage.setItem('currentUser', JSON.stringify(selectedUser.value))
        
        // 根据用户类型决定跳转路径
        if (selectedUser.value.username === 'Admin') {
          // Admin用户导航到管理员面板
          router.push('/admin-dashboard')
        } else {
          // 普通用户导航到常规管理页面
          router.push('/management')
        }
        
        $q.notify({
          type: 'positive',
          message: `Successfully logged in as ${selectedUser.value.username}`,
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      }
    }

    // Handle add new user
    const handleAddUser = async () => {
      if (newUsername.value) {
        try {
          const response = await axios.post(`${BACKEND_URL}/api/users`, {
            username: newUsername.value,
          })

          if (response.data.success) {
            await loadUsers()
            // Select the newly added user
            const newUser = users.value.find((user) => user.username === newUsername.value)
            if (newUser) {
              selectedUser.value = newUser
              showAddUserDialog.value = false
              newUsername.value = ''
              // Proceed with login
              handleLogin()
            }
          }
        } catch (error) {
          console.error('Error adding new user:', error)
          $q.notify({
            type: 'negative',
            message: 'Error adding new user',
            position: 'top',
            timeout: 2000,
            html: true,
            classes: 'text-h6',
          })
        }
      }
    }

    // 在组件挂载时立即加载用户列表
    onMounted(async () => {
      await loadUsers()
    })

    return {
      users,
      selectedUser,
      showAddUserDialog,
      newUsername,
      handleLogin,
      handleAddUser,
    }
  },
})
</script>

<style lang="scss" scoped>
.welcome-page {
  min-height: 100vh;
  background: white;
  position: relative;
}

.header-section {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1;
}

.content-container {
  text-align: center;
  padding: 2rem;
  width: 100%;
  max-width: 400px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.login-box {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.login-btn {
  font-size: 1.2rem;
  padding: 0.8rem 2rem;
  border-radius: 8px;
  transition: transform 0.3s ease;

  &:hover:not(:disabled) {
    transform: scale(1.05);
  }
}

// Add User Dialog Styles
.add-user-input {
  :deep(.q-field__native) {
    color: black !important;
    font-size: 1.2rem;
  }

  :deep(.q-field__label) {
    color: rgba(0, 0, 0, 0.7) !important;
    font-size: 1.2rem;
  }
}

.error-message {
  font-size: 1rem;
  color: red;
}

.user-select {
  :deep(.q-field__native) {
    color: #000000 !important;
    font-size: 1.2rem;
  }

  :deep(.q-field__label) {
    color: rgba(0, 0, 0, 0.7) !important;
    font-size: 1.2rem;
  }

  :deep(.q-field__control) {
    background: white;
    border: 2px solid rgba(0, 0, 0, 0.1) !important;
  }

  :deep(.q-field__control:hover) {
    border: 2px solid var(--q-primary) !important;
  }

  :deep(.q-icon) {
    opacity: 0.8;
  }
}

// Style for the dropdown popup
:deep(.user-select-popup) {
  background: white;
  color: black;
  font-size: 1.2rem;

  .q-item {
    min-height: 40px;
    padding: 8px 16px;
    justify-content: center;

    &:hover {
      background: rgba(25, 118, 210, 0.1);
    }

    &--active {
      background: rgba(25, 118, 210, 0.2);
    }
  }

  .q-item-section {
    text-align: center;
    padding: 0;
  }
}
</style>
