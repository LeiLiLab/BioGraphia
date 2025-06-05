<template>
  <q-page class="welcome-page">
    <div class="header-section bg-primary text-white q-pa-md">
      <div class="text-h5 text-center">User Login & Add New User</div>
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

        <!-- Password Input -->
        <div class="row items-center q-mb-md">
          <q-input
            v-model="password"
            :type="isPwd ? 'password' : 'text'"
            label="Password"
            class="col"
            outlined
            color="primary"
            bg-color="white"
          >
            <template v-slot:prepend>
              <q-icon name="lock" color="primary" />
            </template>
            <template v-slot:append>
              <q-icon
                :name="isPwd ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                color="primary"
                @click="isPwd = !isPwd"
              />
            </template>
          </q-input>
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
            :disable="!selectedUser || !password"
          />
        </div>

        <!-- Reset Password Button -->
        <div class="row q-mb-md">
          <q-btn
            label="Reset Password"
            color="secondary"
            text-color="white"
            size="lg"
            class="col login-btn"
            @click="showResetPasswordDialog = true"
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
            @click="showPinDialog = true"
          />
        </div>
      </div>
    </div>

    <!-- PIN Verification Dialog -->
    <q-dialog v-model="showPinDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">PIN Verification</div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="pinCode"
            label="Enter PIN"
            outlined
            :type="isPinVisible ? 'text' : 'password'"
            @keyup.enter="verifyPin"
          >
            <template v-slot:append>
              <q-icon
                :name="isPinVisible ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="isPinVisible = !isPinVisible"
              />
            </template>
          </q-input>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn
            flat
            label="Verify"
            color="primary"
            @click="verifyPin"
            :disable="!pinCode"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

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
            class="q-mb-md"
            :rules="[(val) => !!val || 'Username is required']"
          >
            <template v-slot:error>
              <div class="error-message">Username is required</div>
            </template>
          </q-input>

          <q-input
            v-model="newPassword"
            :type="isNewPwd ? 'password' : 'text'"
            label="Enter password"
            outlined
            :rules="[(val) => !!val || 'Password is required']"
          >
            <template v-slot:prepend>
              <q-icon name="lock" color="primary" />
            </template>
            <template v-slot:append>
              <q-icon
                :name="isNewPwd ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                color="primary"
                @click="isNewPwd = !isNewPwd"
              />
            </template>
            <template v-slot:error>
              <div class="error-message">Password is required</div>
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
            :disable="!newUsername || !newPassword"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Reset Password Dialog - Step 1: Verify Current Password -->
    <q-dialog v-model="showResetPasswordDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Reset Password</div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="currentPassword"
            label="Current Password"
            outlined
            :type="isCurrentPwdVisible ? 'text' : 'password'"
          >
            <template v-slot:append>
              <q-icon
                :name="isCurrentPwdVisible ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="isCurrentPwdVisible = !isCurrentPwdVisible"
              />
            </template>
          </q-input>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn
            flat
            label="Verify"
            color="primary"
            @click="verifyCurrentPassword"
            :disable="!currentPassword"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Reset Password Dialog - Step 2: Enter New Password -->
    <q-dialog v-model="showNewPasswordDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Enter New Password</div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="newResetPassword"
            label="New Password"
            outlined
            :type="isNewResetPwdVisible ? 'text' : 'password'"
            class="q-mb-md"
          >
            <template v-slot:append>
              <q-icon
                :name="isNewResetPwdVisible ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="isNewResetPwdVisible = !isNewResetPwdVisible"
              />
            </template>
          </q-input>

          <q-input
            v-model="confirmPassword"
            label="Confirm Password"
            outlined
            :type="isConfirmPwdVisible ? 'text' : 'password'"
          >
            <template v-slot:append>
              <q-icon
                :name="isConfirmPwdVisible ? 'visibility' : 'visibility_off'"
                class="cursor-pointer"
                @click="isConfirmPwdVisible = !isConfirmPwdVisible"
              />
            </template>
          </q-input>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn
            flat
            label="Reset Password"
            color="primary"
            @click="handleResetPassword"
            :disable="!newResetPassword || !confirmPassword || newResetPassword !== confirmPassword"
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
  id?: number
  username: string
  password: string
}

export default defineComponent({
  name: 'LoginPage',

  setup() {
    const router = useRouter()
    const $q = useQuasar()
    const users = ref<User[]>([])
    const selectedUser = ref<User | null>(null)
    const password = ref('')
    const isPwd = ref(true)  // 控制密码显示/隐藏
    const showPinDialog = ref(false)
    const showAddUserDialog = ref(false)
    const pinCode = ref('')
    const isPinVisible = ref(false)
    const newUsername = ref('')
    const newPassword = ref('')
    const isNewPwd = ref(true)
    const showResetPasswordDialog = ref(false)
    const showNewPasswordDialog = ref(false)
    const currentPassword = ref('')
    const newResetPassword = ref('')
    const confirmPassword = ref('')
    const isCurrentPwdVisible = ref(false)
    const isNewResetPwdVisible = ref(false)
    const isConfirmPwdVisible = ref(false)

    // Load users from backend API
    const loadUsers = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/users`)
        users.value = response.data.users
      } catch (error) {
        console.error('Error loading users:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load users',
          position: 'top',
          timeout: 2000,
        })
      }
    }

    // Verify PIN
    const verifyPin = () => {
      if (pinCode.value === '123456') {
        showPinDialog.value = false
        pinCode.value = '' // Clear PIN
        showAddUserDialog.value = true // Show add user dialog
      } else {
        $q.notify({
          type: 'negative',
          message: 'Invalid PIN',
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      }
    }

    // Handle login
    const handleLogin = () => {
      if (selectedUser.value && password.value) {
        // 验证密码
        const user = users.value.find(u => u.username === selectedUser.value?.username)
        if (user && user.password === password.value) {
          // 密码正确,保存用户信息并跳转
          const userInfo = {
            username: user.username
          }
          localStorage.setItem('currentUser', JSON.stringify(userInfo))
          
          // 登录后直接跳转到项目选择页面
          router.push('/project-select')
          
          $q.notify({
            type: 'positive',
            message: `Successfully logged in as ${user.username}`,
            position: 'top',
            timeout: 2000,
            html: true,
            classes: 'text-h6',
          })
        } else {
          // 密码错误,显示错误提示
          $q.notify({
            type: 'negative',
            message: 'Invalid username or password',
            position: 'top',
            timeout: 2000,
            html: true,
            classes: 'text-h6',
          })
        }
      }
    }

    // Handle add new user
    const handleAddUser = async () => {
      if (newUsername.value && newPassword.value) {
        try {
          const response = await axios.post(`${BACKEND_URL}/api/users`, {
            username: newUsername.value,
            password: newPassword.value
          })

          if (response.data.success) {
            await loadUsers()
            // Select the newly added user
            const newUser = users.value.find((user) => user.username === newUsername.value)
            if (newUser) {
              selectedUser.value = newUser
              showAddUserDialog.value = false
              // Set the password for automatic login
              password.value = newPassword.value
              // Clear the form
              newUsername.value = ''
              newPassword.value = ''
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

    // Verify current password
    const verifyCurrentPassword = async () => {
      if (selectedUser.value && currentPassword.value) {
        const user = users.value.find(u => u.username === selectedUser.value?.username)
        if (user && user.password === currentPassword.value) {
          showResetPasswordDialog.value = false
          showNewPasswordDialog.value = true
          currentPassword.value = '' // Clear current password
        } else {
          $q.notify({
            type: 'negative',
            message: 'Invalid current password',
            position: 'top',
            timeout: 2000,
          })
        }
      }
    }

    // Handle reset password
    const handleResetPassword = async () => {
      if (selectedUser.value && newResetPassword.value === confirmPassword.value) {
        try {
          const response = await axios.put(`${BACKEND_URL}/api/users/password`, {
            username: selectedUser.value.username,
            newPassword: newResetPassword.value
          })

          if (response.data.success) {
            // Update local user data
            await loadUsers()
            
            // Close dialog and clear form
            showNewPasswordDialog.value = false
            newResetPassword.value = ''
            confirmPassword.value = ''
            
            $q.notify({
              type: 'positive',
              message: 'Password reset successfully',
              position: 'top',
              timeout: 2000,
            })
          }
        } catch (error) {
          console.error('Error resetting password:', error)
          $q.notify({
            type: 'negative',
            message: 'Failed to reset password',
            position: 'top',
            timeout: 2000,
          })
        }
      }
    }

    onMounted(async () => {
      await loadUsers()
    })

    return {
      users,
      selectedUser,
      password,
      isPwd,
      showPinDialog,
      showAddUserDialog,
      pinCode,
      isPinVisible,
      newUsername,
      newPassword,
      isNewPwd,
      showResetPasswordDialog,
      showNewPasswordDialog,
      currentPassword,
      newResetPassword,
      confirmPassword,
      isCurrentPwdVisible,
      isNewResetPwdVisible,
      isConfirmPwdVisible,
      verifyPin,
      handleLogin,
      handleAddUser,
      verifyCurrentPassword,
      handleResetPassword,
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
}

.add-user-input {
  margin-bottom: 1rem;
}

.error-message {
  color: #C10015;
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

.user-select-popup {
  max-height: 40vh;
}
</style> 