<template>
  <q-page class="project-prompt-page">
    <div class="page-content q-pa-md">
      <!-- Main Content -->
      <div class="row q-col-gutter-md">
        <div class="col-12">
          <!-- Prompt Temp Papers Table -->
          <div class="q-mb-xl">
            <div class="text-h5 q-mb-md text-center font-weight-bold" style="font-weight: 700;">Papers with Prompt Analysis</div>
            <div class="table-wrapper">
              <q-table
                :rows="promptTempPapers"
                :columns="columns"
                row-key="pmid"
                :loading="loadingPapers"
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

                <!-- Custom template for prompt versions column -->
                <template v-slot:body-cell-prompt_versions="props">
                  <q-td :props="props" style="font-size: 18px" class="text-center">
                    <div class="prompt-versions-wrapper" v-if="props.row.prompt_versions.length > 0">
                      <div class="prompt-versions">
                        <div 
                          v-for="version in props.row.prompt_versions.slice(0, 5)" 
                          :key="version"
                          class="prompt-version-circle"
                          :style="{ backgroundColor: getVersionColor(version) }"
                          @click="navigateToPaperAnalysis(props.row.pmid, version)"
                        >
                          {{ version.slice(-1) }}
                          <q-tooltip>{{ version }}</q-tooltip>
                        </div>
                        <!-- 如果版本数量超过5个，显示"+X"圆圈 -->
                        <div 
                          v-if="props.row.prompt_versions.length > 5"
                          class="prompt-version-circle more-versions"
                          @click="showAllVersions(props.row.pmid, props.row.prompt_versions)"
                        >
                          +{{ props.row.prompt_versions.length - 5 }}
                          <q-tooltip>Click to see all {{ props.row.prompt_versions.length }} versions</q-tooltip>
                        </div>
                      </div>
                    </div>
                    <div v-else class="no-versions">
                      No prompt versions available
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
                      <p class="text-h6 text-grey q-mt-md">No papers found with prompt analysis</p>
                      <p class="text-subtitle1 text-grey-7">Papers will appear here after they have been processed with prompts</p>
                    </div>
                  </div>
                </template>
              </q-table>
            </div>
          </div>

          <!-- Scraping progress section -->
          <div v-if="showProgress" class="text-h6 q-mb-md text-center">
            <div class="row items-center justify-center">
              <div class="q-mr-sm">Processing Papers: {{ currentPosition + 1 }}/{{ totalPapers }}</div>
              <q-spinner color="primary" size="1.5em" />
            </div>
          </div>
          
          <!-- 直接放置输入框和按钮，移除卡片外壳 -->
          <div class="row q-mt-xl q-mb-md items-center justify-center">
            <div class="col-grow" style="max-width: 1200px; display: flex; gap: 16px; align-items: center">
              <q-input
                v-model="newPaperUrl"
                outlined
                class="col-grow url-input"
                label="Enter PubMed URL"
                @keyup.enter="handleSubmit"
                :loading="submitting"
                style="height: 66px; min-width: 450px;"
              >
                <template v-slot:append>
                  <q-btn color="primary" label="ADD" :loading="submitting" @click="handleSubmit" style="height: 56px; font-size: 18px; padding: 0 15px; align-self: center; display: flex; align-items: center;">
                    <template v-slot:loading>
                      <q-spinner-dots />
                    </template>
                  </q-btn>
                </template>
              </q-input>
              <q-btn
                color="primary"
                :loading="batchSubmitting"
                @click="triggerFileInput"
                class="batch-scrape-btn"
                style="height: 56px; font-size: 18px; padding: 0 15px;"
              >
                <q-icon name="upload_file" class="q-mr-xs" size="22px" />
                BATCH UPLOAD
                <template v-slot:loading>
                  <q-spinner-dots />
                </template>
              </q-btn>
              <!-- 添加Prompt Configuration按钮 -->
              <q-btn
                color="secondary"
                @click="openPromptEditor"
                class="prompt-config-btn"
                style="height: 56px; font-size: 18px; padding: 0 15px;"
              >
                <q-icon name="psychology" size="22px" class="q-mr-xs" />
                EDIT PROMPT
              </q-btn>
              <!-- 添加Complete按钮 -->
              <q-btn
                color="deep-purple"
                @click="completePromptAnalysis"
                class="complete-btn"
                style="height: 56px; font-size: 18px; padding: 0 15px;"
              >
                <q-icon name="check_circle" size="22px" class="q-mr-xs" />
                COMPLETE
              </q-btn>
            </div>
            <!-- Hidden file input -->
            <input
              type="file"
              ref="fileInput"
              accept=".txt"
              style="display: none"
              @change="handleFileSelected"
            />
          </div>
        </div>
      </div>
    </div>
  </q-page>

  <!-- Prompt Editor Dialog -->
  <q-dialog v-model="showPromptEditor" persistent>
    <q-card style="width: 900px; max-width: 95vw; max-height: 90vh;">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-center full-width">
          <div class="text-primary" style="font-size: 24px;">Prompt Configuration</div>
        </div>
      </q-card-section>
      
      <q-card-section class="q-py-md">
        <div class="row justify-between items-center q-mb-md">
          <q-btn 
            icon="arrow_back" 
            color="primary" 
            round 
            :disable="!hasMultiplePrompts"
            @click="switchPromptTemplate((safeCurrentIndex - 1 + promptTemplates.length) % promptTemplates.length)" 
          />
          <div class="text-h6 text-center system-prompt-label">
            {{ promptTemplates[safeCurrentIndex]?.name || '' }}
            <span v-if="promptTemplates[safeCurrentIndex]?.isSystemPrompt" class="system-prompt-badge">
              (Current System Prompt) <q-icon name="check" color="green" size="sm" />
            </span>
          </div>
          <q-btn 
            icon="arrow_forward" 
            color="primary" 
            round 
            :disable="!hasMultiplePrompts"
            @click="switchPromptTemplate((safeCurrentIndex + 1) % promptTemplates.length)" 
          />
        </div>
        
        <div class="text-subtitle1 q-my-sm">
          <q-icon name="info" color="info" size="sm" class="q-mr-sm" />
          {{ promptTemplates[safeCurrentIndex]?.description || 'This prompt template is used for the initial analysis of scientific articles.' }}
        </div>
        
        <div class="q-mb-md prompt-editor-container" style="position: relative;">
          <!-- Loading overlay -->
          <div v-if="isLoadingPrompt" class="prompt-loading-overlay">
            <q-spinner-dots color="primary" size="40px" />
            <div class="text-subtitle1 q-mt-sm">Loading prompt configuration...</div>
          </div>
        
          <div class="prompt-wrapper">
            <q-input
              v-model="currentTemplateContent"
              type="textarea"
              filled
              autogrow
              placeholder="Enter prompt template here"
              style="font-family: monospace;"
              class="prompt-textarea"
              :hint="currentTemplateStats || ''"
            />
          </div>
        </div>
        
        <!-- Button area -->
        <div class="row justify-between q-mt-md">
          <!-- Left buttons -->
          <div>
            <q-btn 
              label="Add Prompt" 
              color="teal" 
              icon="add" 
              @click="openAddPromptDialog" 
              :disable="isLoadingPrompt"
              class="add-prompt-btn q-mr-sm"
            />
            <q-btn 
              label="Set as System Prompt" 
              color="green" 
              icon="check_circle" 
              @click="setAsSystemPrompt" 
              :disable="isLoadingPrompt || promptTemplates[safeCurrentIndex]?.isSystemPrompt"
            />
          </div>
          
          <!-- Right buttons -->
          <div>
            <q-btn label="Cancel" color="negative" @click="onPromptCancel" class="q-mr-sm" :disable="isLoadingPrompt || isSavingPrompt" />
            <q-btn 
              label="Save Changes" 
              color="positive" 
              @click="savePromptChanges" 
              :loading="isSavingPrompt"
              :disable="isLoadingPrompt" 
            />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
  
  <!-- Add Prompt Dialog -->
  <q-dialog v-model="showAddPromptDialog" persistent>
    <q-card style="width: 700px; max-width: 95vw">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Add New Prompt</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>
      
      <q-card-section>
        <q-input 
          v-model="newPromptName" 
          label="Prompt Name/Version" 
          filled 
          class="q-mb-md"
          hint="Example: Version_2, Custom Prompt, etc."
          :rules="[val => !!val || 'Name cannot be empty']"
        />
        
        <q-input
          v-model="newPromptContent"
          type="textarea"
          filled
          autogrow
          label="Prompt Content"
          style="font-family: monospace;"
          class="prompt-textarea q-mb-md"
          :rules="[val => !!val || 'Content cannot be empty']"
          :hint="newPromptStats || 'Enter prompt template content'"
        />
        
        <div class="row justify-end q-mt-lg">
          <q-btn label="Cancel" color="negative" v-close-popup class="q-mr-sm" />
          <q-btn label="Add" color="positive" @click="addNewPrompt" :disable="!canAddPrompt" />
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
  
  <!-- All Versions Dialog -->
  <q-dialog v-model="showAllVersionsDialog">
    <q-card style="width: 500px; max-width: 95vw">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">All Prompt Versions</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>
      
      <q-card-section>
        <div class="text-subtitle1 q-mb-md">PMID: {{ selectedPmid }}</div>
        
        <div class="all-versions-grid">
          <div 
            v-for="version in allVersionsList" 
            :key="version"
            class="prompt-version-circle"
            :style="{ backgroundColor: getVersionColor(version) }"
            @click="navigateAndClose(selectedPmid, version)"
          >
            {{ version.slice(-1) }}
            <q-tooltip>{{ version }}</q-tooltip>
          </div>
        </div>
      </q-card-section>
      
      <q-card-actions align="right">
        <q-btn label="Close" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'
import { BACKEND_URL } from '../config/api'
import { useRouter } from 'vue-router'
import type { QTableColumn } from 'quasar'

interface PromptTemplate {
  name: string;
  description: string;
  content: string;
  isSystemPrompt: boolean;
  isDefault?: boolean;
}

interface PromptTempPaper {
  pmid: string;
  title: string;
  prompt_versions: string[];
}

export default defineComponent({
  name: 'ProjectPromptPage',
  
  setup() {
    const $q = useQuasar()
    const router = useRouter()
    
    // Prompt dialog related states
    const showPromptEditor = ref(false)
    const showAddPromptDialog = ref(false)
    const isLoadingPrompt = ref(false)
    const isSavingPrompt = ref(false)
    const currentPromptIndex = ref(0)
    
    // Prompt template data
    const promptTemplates = ref<PromptTemplate[]>([])
    const currentSystemPromptName = ref('Version_1')
    
    // New prompt form data
    const newPromptName = ref('')
    const newPromptDescription = ref('')
    const newPromptContent = ref('')
    
    // Check if can add new prompt
    const canAddPrompt = computed(() => {
      return newPromptName.value.trim() !== '' && 
             newPromptContent.value.trim() !== '';
    })
    
    // Ensure current index is valid
    const safeCurrentIndex = computed(() => {
      if (currentPromptIndex.value >= 0 && currentPromptIndex.value < promptTemplates.value.length) {
        return currentPromptIndex.value;
      }
      return 0;
    })
    
    // Get current template content
    const currentTemplateContent = computed({
      get: () => {
        const template = promptTemplates.value[safeCurrentIndex.value];
        return template ? template.content : '';
      },
      set: (newValue: string) => {
        if (safeCurrentIndex.value < promptTemplates.value.length) {
          const template = promptTemplates.value[safeCurrentIndex.value];
          if (template) {
            template.content = newValue;
          }
        }
      }
    })
    
    // Calculate current template stats (lines and characters)
    const currentTemplateStats = computed(() => {
      const content = currentTemplateContent.value;
      if (!content) return '';
      
      const lines = content.split('\n').length;
      const chars = content.length;
      return `${lines} lines, ${chars} characters`;
    })
    
    // Calculate new prompt stats (lines and characters)
    const newPromptStats = computed(() => {
      const content = newPromptContent.value;
      if (!content) return '';
      
      const lines = content.split('\n').length;
      const chars = content.length;
      return `${lines} lines, ${chars} characters`;
    })
    
    // Check if there are multiple prompt templates
    const hasMultiplePrompts = computed(() => {
      return promptTemplates.value.length > 1;
    })

    // Paper Crawling Dialog
    const showPaperCrawlingDialog = ref(false)
    const newPaperUrl = ref('')
    const submitting = ref(false)
    const batchSubmitting = ref(false)
    const showProgress = ref(false)
    const currentPosition = ref(0)
    const totalPapers = ref(0)
    const fileInput = ref<HTMLInputElement | null>(null)
    
    // Status check interval for paper processing
    let statusCheckInterval: number | null = null
    
    // PromptTemp Papers Table related
    const promptTempPapers = ref<PromptTempPaper[]>([])
    const loadingPapers = ref(true)
    
    // 显示所有版本对话框相关
    const showAllVersionsDialog = ref(false)
    const selectedPmid = ref('')
    const allVersionsList = ref<string[]>([])
    
    const columns: QTableColumn[] = [
      {
        name: 'pmid',
        label: 'PMID',
        field: 'pmid',
        align: 'center',
        style: 'width: 150px; font-size: 18px',
      },
      {
        name: 'title',
        label: 'Title',
        field: 'title',
        align: 'center',
        style: 'width: 337px',
      },
      {
        name: 'prompt_versions',
        label: 'Prompt Versions',
        field: 'prompt_versions',
        align: 'center',
        style: 'width: 488px',
      }
    ]

    // Format title to limit length
    const formatTitle = (val: string) => {
      return val.length > 94 ? val.substring(0, 94) + '...' : val
    }

    // 预定义的颜色数组
    const versionColors = [
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

    // 根据版本名生成固定的颜色
    const getVersionColor = (version: string) => {
      // 使用版本名生成一个固定的索引
      const index = version.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
      return versionColors[index % versionColors.length]
    }

    // 加载Prompt_Temp下的论文和对应的prompt版本
    const loadPromptTempPapers = async () => {
      loadingPapers.value = true
      try {
        // 这里需要添加新的API端点来获取Prompt_Temp下的论文和对应的prompt版本
        const response = await axios.get(`${BACKEND_URL}/api/prompt-temp-papers`)
        promptTempPapers.value = response.data.papers
      } catch (error) {
        console.error('Failed to load prompt temp papers:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load papers with prompt analysis',
          position: 'top',
          timeout: 3000
        })
        promptTempPapers.value = []
      } finally {
        loadingPapers.value = false
      }
    }

    // 导航到论文分析页面
    const navigateToPaperAnalysis = async (pmid: string, promptVersion: string) => {
      try {
        // 首先设置当前选中的promptVersion到session
        await axios.post(`${BACKEND_URL}/api/set-current-prompt-version`, {
          prompt_version: promptVersion
        })
        
        // 记录当前路径到sessionStorage，以便从论文详情页返回时能回到这个页面
        sessionStorage.setItem('previousPath', router.currentRoute.value.fullPath)
        
        // 然后导航到论文分析页面，使用正确的路由名称'analysis'和url查询参数
      router.push({
          name: 'analysis',
          query: { 
            url: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/` 
          }
        })
      } catch (error) {
        console.error('Failed to set current prompt version:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to navigate to paper analysis',
          position: 'top',
          timeout: 3000
      })
      }
    }

    // 显示所有版本对话框
    const showAllVersions = (pmid: string, versions: string[]) => {
      selectedPmid.value = pmid
      allVersionsList.value = versions
      showAllVersionsDialog.value = true
    }
    
    // 导航并关闭对话框
    const navigateAndClose = (pmid: string, version: string) => {
      showAllVersionsDialog.value = false
      navigateToPaperAnalysis(pmid, version)
    }

    // 添加完成按钮处理函数
    const completePromptAnalysis = async () => {
      try {
        // 显示加载提示
        const notifyRef = $q.notify({
          type: 'ongoing',
          message: 'Completing prompt analysis...',
          position: 'top',
          timeout: 0,
          spinner: true
        })

        // 清除session中的promptVersion
        await axios.post(`${BACKEND_URL}/api/clear-current-prompt-version`)
        
        // 清除提示
        notifyRef()
        
        // 显示成功消息
        $q.notify({
          type: 'positive',
          message: 'Prompt analysis completed. Ready for batch paper crawling.',
          position: 'top',
          timeout: 2000
        })
        
        // 延迟一下，让用户看到成功消息
        setTimeout(() => {
          // 导航到AdminDashboard页面
          router.push({ 
            path: '/admin-dashboard',
            query: { 
              // 添加一个查询参数，用于在AdminDashboard页面自动打开Paper Crawling对话框
              openPaperCrawling: 'true',
              // 添加时间戳防止缓存
              t: Date.now().toString()
            }
          })
        }, 500)
      } catch (error) {
        console.error('Failed to complete prompt analysis:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to complete prompt analysis',
          position: 'top',
          timeout: 3000
        })
      }
    }

    // Handle paper URL submission
    const handleSubmit = async () => {
      if (!newPaperUrl.value) {
        $q.notify({
          type: 'negative',
          message: 'Please enter a URL',
          position: 'top',
          timeout: 3000
        })
        return
      }

      // Validate URL format
      const urlPattern = /^https:\/\/pubmed\.ncbi\.nlm\.nih\.gov\/\d+\/?$/
      if (!urlPattern.test(newPaperUrl.value)) {
        $q.notify({
          type: 'negative',
          message: 'Invalid URL format, please check and try again.',
          position: 'top',
          timeout: 3000
        })
        return
      }

      submitting.value = true

      try {
        // Get current username
        const currentUser = localStorage.getItem('currentUser')
        let username = 'Guest'
        try {
          const userObj = JSON.parse(currentUser || '{}')
          if (userObj && userObj.username) {
            username = userObj.username
          }
        } catch (error) {
          console.log('Failed to parse user object, using original value:', error)
        }
        
        console.log('Single paper upload using username:', username)

        // Create a notification reference
        const notifyRef = $q.notify({
          type: 'ongoing',
          message: 'Processing paper, please wait...',
          position: 'top',
          timeout: 0,
          spinner: true
        })

        try {
          // Call initialize API with username
          const initResponse = await axios.post(`${BACKEND_URL}/api/initialize-paper`, {
            url: newPaperUrl.value,
            username: username,
            promptVersion: promptTemplates.value[safeCurrentIndex.value]?.name || 'Version_1'
          })

          // Ensure processing notification is cleared
          notifyRef()

          if (initResponse.data.success) {
            // Clear input field
            newPaperUrl.value = ''
            
            // 成功后刷新论文列表
            loadPromptTempPapers()

            // Show success message
            $q.notify({
              type: 'positive',
              message: 'Paper initialization started',
              position: 'top',
              timeout: 3000
            })
            
            // 开始检查进度
            showProgress.value = true
            totalPapers.value = 1
            currentPosition.value = 0
            
            // 清除可能存在的旧计时器
            if (statusCheckInterval !== null) {
              clearInterval(statusCheckInterval)
              statusCheckInterval = null
            }
            
            // 启动新的状态检查
            statusCheckInterval = window.setInterval(checkScrapingStatus, 2500)
          }
        } catch (error) {
          // Ensure processing notification is cleared
          notifyRef()
          throw error
        }
      } catch (error: unknown) {
        console.error('Error initializing paper:', error)

        // Type assertion and check if it's an already scraped paper error
        if (error && typeof error === 'object' && 'response' in error && 
            error.response && typeof error.response === 'object' && 'status' in error.response) {
          if (error.response.status === 409) {
            $q.notify({
              type: 'warning',
              message: 'Paper already scraped',
              position: 'top',
              color: 'warning',
              timeout: 3000
            })
            newPaperUrl.value = '' // Clear input field
          } else {
            const errorResponse = error.response as { data?: { message?: string } };
            const errorMessage = errorResponse.data?.message || 'Error initializing paper. Please try again.'

            $q.notify({
              type: 'negative',
              message: errorMessage,
              position: 'top',
              timeout: 3000
            })
          }
        } else {
          $q.notify({
            type: 'negative',
            message: 'Error initializing paper. Please try again.',
            position: 'top',
            timeout: 3000
          })
        }
      } finally {
        submitting.value = false
      }
    }

    // API URL utility function
    const getApiUrl = (endpoint: string) => {
      return `${BACKEND_URL}${endpoint}`;
    }

    // Open prompt editor
    const openPromptEditor = () => {
      showPromptEditor.value = true
      loadTempPrompts()
    }
    
    // Load temporary prompt configurations
    const loadTempPrompts = async () => {
      isLoadingPrompt.value = true
      try {
        // Load prompt templates from temp_prompt.json
        const response = await axios.get(getApiUrl('/api/project-temp-prompts'))
        
        // Extract data using the new structure
        const data = response.data
        
        // Update current system prompt name
        if (data.current_system_prompt_name) {
          currentSystemPromptName.value = data.current_system_prompt_name
        }
        
        // Convert prompt data to template array
        if (data.prompts && typeof data.prompts === 'object') {
          promptTemplates.value = Object.entries(data.prompts).map(([key, value]) => ({
            name: key,
            description: `Version ${key} prompt template`,
            content: value as string,
            isSystemPrompt: key === data.current_system_prompt_name
          }))
        } else {
          console.warn('Unexpected data format from /api/project-temp-prompts')
          promptTemplates.value = []
        }
        
        // If no prompt templates found, load system defaults
        if (promptTemplates.value.length === 0) {
          // Load PROMPT_TEMPLATE from existing prompt.json
          const defaultResponse = await axios.get(getApiUrl('/api/prompt-config'))
          
          promptTemplates.value = [{
            name: 'Version_1',
            description: 'This is the default prompt template for the initial analysis of scientific articles',
            content: defaultResponse.data.PROMPT_TEMPLATE || '',
            isDefault: true,
            isSystemPrompt: true
          }]
          
          currentSystemPromptName.value = 'Version_1'
          
          // Initialize temp_prompt.json file with new structure
          await axios.post(getApiUrl('/api/project-temp-prompts'), {
            current_system_prompt_name: 'Version_1',
            prompts: {
              Version_1: defaultResponse.data.PROMPT_TEMPLATE
            }
          })
        }
        
        // Find and display system prompt template index
        const systemPromptIndex = promptTemplates.value.findIndex(t => t.isSystemPrompt)
        if (systemPromptIndex !== -1) {
          currentPromptIndex.value = systemPromptIndex
        }
        
        console.log('Loaded prompt templates:', promptTemplates.value)
      } catch (error) {
        console.error('Failed to load prompt configuration:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load prompt configuration',
          position: 'top',
          timeout: 3000
        })
        
        // Load an empty template when error occurs
        promptTemplates.value = [{
          name: 'Version_1',
          description: 'Default Prompt Template',
          content: '',
          isDefault: true,
          isSystemPrompt: true
        }]
      } finally {
        isLoadingPrompt.value = false
      }
    }
    
    // Switch prompt template
    const switchPromptTemplate = (index: number) => {
      if (index >= 0 && index < promptTemplates.value.length) {
        currentPromptIndex.value = index
      }
    }
    
    // Open add prompt dialog
    const openAddPromptDialog = () => {
      newPromptName.value = ''
      newPromptDescription.value = ''
      newPromptContent.value = ''
      showAddPromptDialog.value = true
    }
    
    // Add new prompt
    const addNewPrompt = async () => {
      if (!canAddPrompt.value) return
      
      // Check if prompt with same name already exists
      const existingIndex = promptTemplates.value.findIndex(t => t.name === newPromptName.value)
      if (existingIndex !== -1) {
        $q.notify({
          type: 'warning',
          message: `Prompt "${newPromptName.value}" already exists, please use a different name`,
          position: 'top',
          timeout: 3000
        })
        return
      }
      
      // Add to prompt templates list
      promptTemplates.value.push({
        name: newPromptName.value,
        description: `Version ${newPromptName.value} prompt template`,
        content: newPromptContent.value,
        isSystemPrompt: false
      })
      
      try {
        // Create prompts object for temp_prompt.json
        const promptsObj: Record<string, string> = {}
        promptTemplates.value.forEach(template => {
          promptsObj[template.name] = template.content
        })
        
        // Update temp_prompt.json with new structure
        await axios.post(getApiUrl('/api/project-temp-prompts'), {
          current_system_prompt_name: currentSystemPromptName.value,
          prompts: promptsObj
        })
        
        // Switch to newly added prompt
        currentPromptIndex.value = promptTemplates.value.length - 1
        
        // Close dialog
        showAddPromptDialog.value = false
        
        $q.notify({
          type: 'positive',
          message: 'Successfully added new prompt',
          position: 'top',
          timeout: 2000
        })
      } catch (error) {
        console.error('Failed to save new prompt:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to save new prompt',
          position: 'top',
          timeout: 3000
        })
        
        // Remove template that was just added if save fails
        promptTemplates.value.pop()
      }
    }
    
    // Set current prompt as system prompt
    const setAsSystemPrompt = async () => {
      if (safeCurrentIndex.value >= promptTemplates.value.length) return
      
      const template = promptTemplates.value[safeCurrentIndex.value]
      if (!template) return
      
      isSavingPrompt.value = true
      
      try {
        // Update PROMPT_TEMPLATE in prompt.json file
        await axios.put(getApiUrl('/api/prompt-config'), {
          PROMPT_TEMPLATE: template.content
        })
        
        // Update system status of prompt templates
        promptTemplates.value.forEach(t => {
          t.isSystemPrompt = false
        })
        template.isSystemPrompt = true
        
        // Update current system prompt name
        currentSystemPromptName.value = template.name
        
        // Create prompts object for temp_prompt.json
        const promptsObj: Record<string, string> = {}
        promptTemplates.value.forEach(t => {
          promptsObj[t.name] = t.content
        })
        
        // Update temp_prompt.json with new structure including current_system_prompt_name
        await axios.post(getApiUrl('/api/project-temp-prompts'), {
          current_system_prompt_name: template.name,
          prompts: promptsObj
        })
        
        $q.notify({
          type: 'positive',
          message: `Set "${template.name}" as the current system prompt`,
          position: 'top',
          timeout: 2000
        })
      } catch (error) {
        console.error('Failed to set system prompt:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to set system prompt',
          position: 'top',
          timeout: 3000
        })
      } finally {
        isSavingPrompt.value = false
      }
    }
    
    // Save prompt changes
    const savePromptChanges = async () => {
      isSavingPrompt.value = true
      
      try {
        // Create prompts object for temp_prompt.json
        const promptsObj: Record<string, string> = {}
        promptTemplates.value.forEach(template => {
          promptsObj[template.name] = template.content
        })
        
        // Save all prompt templates to temp_prompt.json with new structure
        await axios.post(getApiUrl('/api/project-temp-prompts'), {
          current_system_prompt_name: currentSystemPromptName.value,
          prompts: promptsObj
        })
        
        // If current edit is system prompt, also update prompt.json
        const currentTemplate = promptTemplates.value[safeCurrentIndex.value]
        if (currentTemplate && currentTemplate.isSystemPrompt) {
          await axios.put(getApiUrl('/api/prompt-config'), {
            PROMPT_TEMPLATE: currentTemplate.content
          })
        }
        
        $q.notify({
          type: 'positive',
          message: 'Prompt configuration saved',
          position: 'top',
          timeout: 2000
        })
        
        // Close dialog
        showPromptEditor.value = false
      } catch (error) {
        console.error('Failed to save prompt configuration:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to save prompt configuration',
          position: 'top',
          timeout: 3000
        })
      } finally {
        isSavingPrompt.value = false
      }
    }
    
    // Cancel prompt editing
    const onPromptCancel = () => {
      showPromptEditor.value = false
      
      // Reload prompt data
      loadTempPrompts()
      
      $q.notify({
        type: 'info',
        message: 'Edit cancelled',
        position: 'top',
        timeout: 1000
      })
    }
    
    // Trigger file input click
    const triggerFileInput = () => {
      fileInput.value?.click()
    }
    
    // Handle file selection for batch upload
    const handleFileSelected = async (event: Event) => {
      const input = event.target as HTMLInputElement
      if (!input.files?.length) return

      const file = input.files[0]
      if (file instanceof File) {
        batchSubmitting.value = true
        const formData = new FormData()
        formData.append('file', file)
        
        // Get and add current username
        const currentUser = localStorage.getItem('currentUser')
        let username = 'Guest'
        try {
          const userObj = JSON.parse(currentUser || '{}')
          if (userObj && userObj.username) {
            username = userObj.username
          }
        } catch (error) {
          console.log('Failed to parse user object, using original value:', error)
        }
        
        console.log('Batch upload using username:', username)
        
        // Add username to form data
        formData.append('username', username)
        // 添加 promptVersion 到 FormData
        formData.append('promptVersion', promptTemplates.value[safeCurrentIndex.value]?.name || 'Version_1')

        try {
          const response = await axios.post(`${BACKEND_URL}/api/batch-initialize`, formData)

          if (response.data.success) {
            $q.notify({
              type: 'positive',
              message: response.data.message,
              position: 'top',
              timeout: 3000
            })

            // Start checking progress
            showProgress.value = true
            totalPapers.value = response.data.total
            currentPosition.value = 0

            // Clear any existing timer
            if (statusCheckInterval !== null) {
              clearInterval(statusCheckInterval)
              statusCheckInterval = null
            }

            // Start new status check, check every 2.5 seconds
            statusCheckInterval = window.setInterval(checkScrapingStatus, 2500)
          }
        } catch (error: unknown) {
          console.error('Error uploading file:', error)
          
          let errorMessage = 'Error uploading file. Please try again.';
          
          if (error && typeof error === 'object' && 'response' in error &&
              error.response && typeof error.response === 'object') {
            const errorResponse = error.response as { 
              data?: { message?: string; error?: string }
            };
            
            errorMessage = errorResponse.data?.message || 
                          errorResponse.data?.error || 
                          'Unknown error';
          }

          $q.notify({
            type: 'negative',
            message: errorMessage,
            position: 'top',
            timeout: 3000
          })
        } finally {
          batchSubmitting.value = false
          // Reset file input
          input.value = ''
        }
      }
    }
    
    // Check scraping status
    const checkScrapingStatus = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/scraping-status`)
        const { total_papers, completed_papers, remaining_papers } = response.data

        // If total > 0, scraping task is in progress
        if (total_papers > 0) {
          showProgress.value = true
          totalPapers.value = total_papers

          // Update current progress
          const completedCount = completed_papers.length
          if (completedCount > currentPosition.value) {
            // New completed papers
            const newCompletedPapers = completed_papers.slice(currentPosition.value)

            // Update progress (0-based counting, but display as 1-based)
            currentPosition.value = completedCount

            // Process each newly completed paper
            for (const paper of newCompletedPapers) {
              if (paper.status === 'success') {
                // Success case - 刷新Prompt_Temp下的论文列表
                loadPromptTempPapers()
              } else if (paper.status === 'error' || paper.status === 'failed') {
                // Show error notification
                $q.notify({
                  type: 'negative',
                  message: `Failed to process paper ${paper.pmid}: ${paper.error || 'Unknown error'}`,
                  position: 'top',
                  timeout: 3000
                })
              }
            }
          }

          // If all papers are processed
          if (remaining_papers === 0) {
            showProgress.value = false
            if (statusCheckInterval !== null) {
              clearInterval(statusCheckInterval)
              statusCheckInterval = null
            }

            // Show completion notification
            $q.notify({
              type: 'positive',
              message: `Completed processing all papers`,
              position: 'top',
              timeout: 3000
            })
          }
        } else {
          // No papers being processed, reset state
          showProgress.value = false
          currentPosition.value = 0
          totalPapers.value = 0
          if (statusCheckInterval !== null) {
            clearInterval(statusCheckInterval)
            statusCheckInterval = null
          }
        }
      } catch (error) {
        console.error('Error checking scraping status:', error)
      }
    }
    
    // Automatically show prompt editor dialog on component mount
    onMounted(() => {
      // Check current system prompt name
      axios.get(getApiUrl('/api/current-prompt-version'))
        .then(response => {
          if (response.data && response.data.version) {
            currentSystemPromptName.value = response.data.version
          }
        })
        .catch(error => {
          console.error('Failed to get current prompt version:', error)
        })
      
      // 检查是否是第一次访问此页面
      const hasVisitedPromptPage = sessionStorage.getItem('hasVisitedPromptPage')
      
      if (!hasVisitedPromptPage) {
        // 第一次访问，自动打开prompt编辑器
        setTimeout(() => {
          openPromptEditor()
          // 设置标记，表示已访问过
          sessionStorage.setItem('hasVisitedPromptPage', 'true')
        }, 500)
      }
      
      // 加载Prompt_Temp下的论文
      loadPromptTempPapers()
      
      // 页面加载时启动状态检查并立即执行一次检查
      if (statusCheckInterval !== null) {
        clearInterval(statusCheckInterval)
      }
      statusCheckInterval = window.setInterval(checkScrapingStatus, 2500)
      checkScrapingStatus()
    })
    
    // Clean up interval on component unmount
    onUnmounted(() => {
      if (statusCheckInterval !== null) {
        clearInterval(statusCheckInterval)
        statusCheckInterval = null
      }
    })
    
    return {
      // Prompt dialog related
      showPromptEditor,
      openPromptEditor,
      isLoadingPrompt,
      isSavingPrompt,
      promptTemplates,
      currentPromptIndex,
      safeCurrentIndex,
      currentTemplateContent,
      currentTemplateStats,
      hasMultiplePrompts,
      switchPromptTemplate,
      savePromptChanges,
      onPromptCancel,
      setAsSystemPrompt,
      
      // New prompt related
      showAddPromptDialog,
      newPromptName,
      newPromptContent,
      newPromptStats,
      openAddPromptDialog,
      addNewPrompt,
      canAddPrompt,
      
      // Current system prompt name
      currentSystemPromptName,
      
      // Paper crawling related
      showPaperCrawlingDialog,
      newPaperUrl,
      submitting,
      batchSubmitting,
      showProgress,
      currentPosition,
      totalPapers,
      fileInput,
      handleSubmit,
      triggerFileInput,
      handleFileSelected,
      
      // PromptTemp Papers Table related
      promptTempPapers,
      loadingPapers,
      columns,
      formatTitle,
      getVersionColor,
      navigateToPaperAnalysis,
      showAllVersions,
      navigateAndClose,
      
      // 显示所有版本对话框相关
      showAllVersionsDialog,
      selectedPmid,
      allVersionsList,
      
      // 添加完成按钮处理函数
      completePromptAnalysis,
    }
  }
})
</script>

<style lang="scss" scoped>
.project-prompt-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-content {
  padding-top: 20px;
  padding-bottom: 40px;
}

.action-card {
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;

  .card-content {
    flex-grow: 1;
    padding: 16px;
    font-size: 18px;
  }

  .q-card-actions {
    margin-top: auto;
    padding: 12px;
    display: flex;
    justify-content: flex-end;
  }

  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }
}

.paper-crawling-card {
  border-radius: 12px;
  overflow: hidden;
}

.prompt-editor-container {
  position: relative;
  min-height: 400px;
}

.prompt-wrapper {
  width: 100%;
}

.prompt-textarea {
  font-size: 14px;
  width: 100%;
  
  :deep(.q-field__native) {
    min-height: 400px;
    line-height: 1.5;
    padding: 12px;
    white-space: pre-wrap;
  }
  
  :deep(.q-field__messages) {
    font-size: 16px !important;
    min-height: 24px;
    opacity: 1 !important;
    visibility: visible !important;
  }
}

.prompt-loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 10;
  border-radius: 4px;
}

.system-prompt-label {
  display: flex;
  align-items: center;
  justify-content: center;
}

.system-prompt-badge {
  margin-left: 5px;
  font-size: 16px;
  font-weight: normal;
  color: #4caf50;
}

.add-prompt-btn {
  background: #26a69a;
  color: white;
}

.prompt-config-btn {
  height: 56px;
  font-size: 20px;
  padding: 0 20px;
  min-height: unset;
  align-self: center;
}

.batch-scrape-btn {
  height: 56px;
  font-size: 20px;
  padding: 0 20px;
  min-height: unset;
  align-self: center;
}

.complete-btn {
  height: 56px;
  font-size: 18px;
  padding: 0 20px;
  min-height: unset;
  align-self: center;
  background: #673ab7;
  color: white;
  transition: transform 0.2s, box-shadow 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(103, 58, 183, 0.3);
  }
}

/* Paper crawling styles */
.url-input {
  :deep(.q-field__label) {
    font-size: 20px;
    top: 18px;
  }
  :deep(.q-field__native) {
    font-size: 20px;
    padding-top: 18px;
    padding-bottom: 2px;
  }
  :deep(.q-field__marginal) {
    font-size: 20px;
    height: 66px;
    padding: 0;
  }
  :deep(.q-field__control) {
    height: 66px;
  }
  :deep(.q-field--focused) .q-field__label, :deep(.q-field--float) .q-field__label {
    top: 12px;
    font-size: 20px;
    transform: translateY(-20px);
  }
  :deep(.q-field__append) {
    height: 100%;
    align-items: stretch;
    padding: 0;
  }
}

/* 添加表格相关样式 */
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

.prompt-versions-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 4px;
}

.prompt-versions {
  display: flex;
  align-items: center;
  gap: 8px;  /* 圆圈之间的间距，减小为8px */
  justify-content: center;
}

.prompt-version-circle {
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
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
}

.no-versions {
  color: #666;
  font-style: italic;
}

.more-versions {
  background-color: #607D8B;  /* 灰蓝色背景，与其他颜色区分 */
  font-size: 14px;
  font-weight: bold;
}

.all-versions-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  padding: 10px;
  max-height: 300px;
  overflow-y: auto;
}

:deep(.q-tooltip) {
  font-size: 14px;
  background: rgba(0, 0, 0, 0.8);
  padding: 8px 12px;
  border-radius: 4px;
  max-width: none;
}
</style>