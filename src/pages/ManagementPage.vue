<template>
  <q-page class="q-pa-md">
    <!-- 标题栏 -->
    <div class="header-row q-mb-lg">
      <q-btn 
        color="primary" 
        label="Back to Project Selection" 
        @click="goToProjectSelection"
        flat
        class="back-btn"
        icon="arrow_back"
        icon-left
      />
      <div class="text-h4 text-center flex-grow">HOME</div>
      <div class="invisible-spacer">
        <!-- 占位元素，保持标题居中 -->
      </div>
    </div>
    
    <!-- Papers table -->
    <div class="table-wrapper">
      <q-table
        :rows="papers"
        :columns="computedColumns"
        row-key="pmid"
        :loading="loading"
        class="management-table q-mb-xl"
        :rows-per-page-options="[5, 10, 15, 20, 0]"
        bordered
        flat
      >
        <!-- 添加自定义的selection列 -->
        <template v-if="showCheckboxes" v-slot:body-cell-selection="props">
          <q-td :props="props" auto-width>
            <q-checkbox
              :model-value="selectedPapers.includes(props.row.pmid)"
              @update:model-value="toggleSelection(props.row.pmid)"
            />
          </q-td>
        </template>

        <!-- Custom template for title column -->
        <template v-slot:body-cell-title="props">
          <q-td :props="props" style="font-size: 18px" class="text-center">
            <div class="ellipsis" style="max-width: 950px">
              {{ formatTitle(props.value) }}
              <q-tooltip>{{ props.value }}</q-tooltip>
            </div>
          </q-td>
        </template>

        <!-- Custom template for other cells -->
        <template v-slot:body-cell="props">
          <q-td :props="props" style="font-size: 18px" class="text-center">
            {{ props.value }}
          </q-td>
        </template>

        <!-- Custom template for assigned users column -->
        <template v-slot:body-cell-assigned_user="props">
          <q-td :props="props" style="font-size: 18px" class="text-center">
            <div class="user-links">
              <template v-for="(user, index) in props.row.assigned_user" :key="user">
                <router-link
                  :to="{
                    name: 'analysis',
                    query: {
                      url: `https://pubmed.ncbi.nlm.nih.gov/${props.row.pmid}`,
                      user: user,
                      mode: user === 'Main' ? 'temp' : 'view',
                    },
                  }"
                  class="user-link"
                >
                  {{ user === 'Main' ? 'Start' : user }}
                </router-link>
                <span v-if="index < props.row.assigned_user.length - 1">, </span>
              </template>
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
      </q-table>
      
      <!-- DOWN button positioned absolutely -->
      <q-btn v-if="!showCheckboxes" color="primary" label="DOWNLOAD" class="down-btn" @click="handleDownClick" />
      
      <!-- 操作按钮组 -->
      <div v-if="showCheckboxes" class="action-buttons">
        <q-btn 
          color="primary" 
          :label="isAllSelected ? 'UNSELECT ALL' : 'SELECT ALL'" 
          class="select-all-btn q-mr-sm" 
          @click="selectAllPapers" 
        />
        <q-btn color="negative" label="CANCEL" class="cancel-btn q-mr-sm" @click="cancelSelection" />
        <q-btn 
          :color="selectedPapers.length > 0 ? 'positive' : 'green-7'" 
          label="DOWNLOAD" 
          class="action-down-btn" 
          :disable="selectedPapers.length === 0"
          @click="handleActionDown" 
        />
      </div>
    </div>

    <!-- Scraping progress section -->
    <div v-if="showProgress" class="text-h6 q-mb-md text-center">
      <div class="row items-center justify-center">
        <div class="q-mr-sm">Processing Papers: {{ totalPapers - remainingPapersInQueue }}/{{ totalPapers }}</div>
        <q-spinner color="primary" size="1.5em" />
      </div>
    </div>
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import type { QTableColumn } from 'quasar'
import { useQuasar } from 'quasar'
import { useRouter } from 'vue-router'
import { BACKEND_URL } from '../config/api'

interface Paper {
  pmid: string
  title: string
  context: string
  assigned_user: string[]
  extraction_time?: string
}

export default defineComponent({
  name: 'ManagementPage',

  setup() {
    const $q = useQuasar()
    const router = useRouter()
    const papers = ref<Paper[]>([])
    const loading = ref(true)
    const showProgress = ref(false)
    const totalPapers = ref(0)
    let statusCheckInterval: number | null = null
    const showCheckboxes = ref(false)
    const selectedPapers = ref<string[]>([])
    const isAllSelected = ref(false)
    const isAdmin = ref(false)
    const remainingPapersInQueue = ref(0)

    const goToProjectSelection = () => {
      router.push('/project-select')
    }

    const formatTitle = (val: string) => {
      return val.length > 94 ? val.substring(0, 94) + '...' : val
    }

    const columns: QTableColumn[] = [
      {
        name: 'pmid',
        label: 'PMID',
        field: 'pmid',
        align: 'center' as const,
        style: 'width: 150px',
      },
      {
        name: 'title',
        label: 'Title',
        field: 'title',
        align: 'center' as const,
        style: 'width: 750px',
      },
      {
        name: 'assigned_user',
        label: 'Status',
        field: 'assigned_user',
        align: 'center' as const,
        style: 'width: 200px',
      },
    ]

    // 计算属性：根据showCheckboxes状态动态返回列配置
    const computedColumns = computed(() => {
      if (showCheckboxes.value) {
        return [
          {
            name: 'selection',
            label: '',
            field: 'selection',
            align: 'center' as const,
            style: 'width: 50px',
          },
          ...columns
        ];
      }
      return columns;
    });

    const loadPapers = async () => {
      try {
        // 从localStorage获取当前用户名
        const currentUser = localStorage.getItem('currentUser')
        let username = currentUser || 'Guest' // 确保username不为null
        
        // 如果currentUser是JSON字符串，解析它并获取username
        try {
          const userObj = JSON.parse(currentUser || '{}')
          if (userObj && userObj.username) {
            username = userObj.username
          }
        } catch (error) {
          // 如果解析失败，使用原始值
          console.log('Failed to parse user object, using original value:', error)
        }
        
        console.log('Using username:', username)  // 添加日志以便调试
        
        const response = await axios.get(`${BACKEND_URL}/api/papers`, {
          params: {
            username: username
          }
        })
        
        papers.value = response.data.papers.sort((a: Paper, b: Paper) => {
          const timeA = new Date(a.extraction_time || 0).getTime()
          const timeB = new Date(b.extraction_time || 0).getTime()
          return timeA - timeB
        })
      } catch (error) {
        console.error('Error loading papers:', error)
        papers.value = []
      } finally {
        loading.value = false
      }
    }

    // 添加爬取状态检查方法
    const checkScrapingStatus = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/scraping-status`);
        const { total_papers, completed_papers, remaining_papers } = response.data

        remainingPapersInQueue.value = remaining_papers

        // 如果有总数大于0，说明有爬取任务在进行
        if (total_papers > 0) {
          showProgress.value = true;
          totalPapers.value = total_papers;

          // Since the backend now clears the completed_papers list on read,
          // we process all papers received.
          for (const paper of completed_papers) {
            if (paper.status === 'success') {
              // 成功时刷新论文列表
              loadPapers();
              
              // 显示成功通知 (仅管理员)
              $q.notify({
                type: 'positive',
                message: `Paper ${paper.pmid} processed successfully`,
                position: 'top',
                html: true,
                classes: 'notification-message',
                timeout: 3000,
              });
            } else if (paper.status === 'error' || paper.status === 'failed') {
              // 显示错误通知 (仅管理员)
              $q.notify({
                type: 'negative',
                message: `Failed to process paper ${paper.pmid}: ${paper.error || 'Unknown error'}`,
                position: 'top',
                html: true,
                classes: 'notification-message',
                timeout: 3000,
              });
            }
          }

          // 如果所有论文都处理完毕
          if (remaining_papers === 0) {
            if (total_papers > 0) { // Only show completion notification if a batch was running
              $q.notify({
                type: 'positive',
                message: `Completed processing all papers`,
                position: 'top',
                html: true,
                classes: 'notification-message',
                timeout: 3000,
              });
            }

            // 最后再刷新一次论文列表
            loadPapers();
          }
        } else {
          // 如果没有正在处理的论文，但正在显示进度条，则隐藏它
          if (showProgress.value) {
            showProgress.value = false;
            totalPapers.value = 0;
            
            // 清除定时器
            if (statusCheckInterval !== null) {
              clearInterval(statusCheckInterval);
              statusCheckInterval = null;
            }
          }
        }
      } catch (error: unknown) {
        console.error('Error checking scraping status:', error);
      }
    };

    const handleDownClick = () => {
      // 切换显示勾选框状态
      showCheckboxes.value = !showCheckboxes.value;
      // 如果隐藏勾选框，清空选中状态
      if (!showCheckboxes.value) {
        selectedPapers.value = [];
        isAllSelected.value = false;
      }
    }

    const toggleSelection = (pmid: string) => {
      if (selectedPapers.value.includes(pmid)) {
        selectedPapers.value = selectedPapers.value.filter((p) => p !== pmid);
        // 如果取消选择了某个论文，那么肯定不是全选状态
        isAllSelected.value = false;
      } else {
        selectedPapers.value.push(pmid);
        // 检查是否所有论文都被选中
        isAllSelected.value = selectedPapers.value.length === papers.value.length;
      }
    }

    const selectAllPapers = () => {
      if (isAllSelected.value) {
        // 如果已经全选，则取消选择所有论文
        selectedPapers.value = [];
        isAllSelected.value = false;
      } else {
        // 否则选择所有论文
        selectedPapers.value = papers.value.map(paper => paper.pmid);
        isAllSelected.value = true;
      }
    }

    const cancelSelection = () => {
      // 取消选择模式，隐藏勾选框，清空选中状态
      showCheckboxes.value = false;
      selectedPapers.value = [];
      isAllSelected.value = false;
    }

    const handleActionDown = async () => {
      if (selectedPapers.value.length === 0) {
        return;
      }
      
      try {
        // 显示加载状态
        const loadingNotif = $q.notify({
          type: 'ongoing',
          message: 'Preparing download files...',
          position: 'top',
          timeout: 0,
          html: true,
          classes: 'notification-message',
          spinner: true,
        });
        
        // 调用后端API，下载选中的论文
        const response = await axios({
          method: 'post',
          url: `${BACKEND_URL}/api/download-papers`,
          data: {
            pmids: selectedPapers.value
          },
          responseType: 'blob', // 重要：指定响应类型为blob
        });
        
        // 关闭加载通知
        loadingNotif();
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'Papers.zip');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // 显示成功消息
        $q.notify({
          type: 'positive',
          message: 'File is ready, starting download',
          position: 'top',
          html: true,
          classes: 'notification-message',
          timeout: 3000,
        });
        
        // 操作完成后，退出选择模式
        showCheckboxes.value = false;
        selectedPapers.value = [];
        isAllSelected.value = false;
      } catch (error) {
        console.error('Error downloading file:', error);
        
        // 正确处理 unknown 类型的错误
        const errorMessage = (() => {
          if (error && typeof error === 'object') {
            // 检查是否有 response.data.message
            if ('response' in error && 
                error.response && 
                typeof error.response === 'object' && 
                'data' in error.response && 
                error.response.data && 
                typeof error.response.data === 'object' && 
                'message' in error.response.data) {
              return String(error.response.data.message);
            }
            
            // 检查是否有 message 属性
            if ('message' in error && error.message) {
              return String(error.message);
            }
          }
          return 'Unknown error';
        })();
        
        $q.notify({
          type: 'negative',
          message: 'Error downloading file: ' + errorMessage,
          position: 'top',
          html: true,
          classes: 'notification-message',
          timeout: 5000,
        });
      }
    }

    onMounted(() => {
      const userStr = localStorage.getItem('currentUser')
      if (userStr) {
        try {
          const userObj = JSON.parse(userStr)
          if (userObj && userObj.username) {
            isAdmin.value = userObj.username === 'Admin'
          }
        } catch (error) {
          console.error('Failed to parse user object from localStorage:', error)
        }
      }

      loadPapers()
      
      // Only start status checking for admin users
      if (isAdmin.value) {
        if (statusCheckInterval !== null) {
          clearInterval(statusCheckInterval)
        }
        statusCheckInterval = setInterval(checkScrapingStatus, 2500) as unknown as number
        checkScrapingStatus()
      }
    })

    onUnmounted(() => {
      if (statusCheckInterval !== null) {
        clearInterval(statusCheckInterval)
        statusCheckInterval = null
      }
    })

    return {
      papers,
      columns,
      loading,
      formatTitle,
      showProgress,
      totalPapers,
      handleDownClick,
      showCheckboxes,
      selectedPapers,
      toggleSelection,
      computedColumns,
      selectAllPapers,
      cancelSelection,
      handleActionDown,
      isAllSelected,
      goToProjectSelection,
      isAdmin,
      remainingPapersInQueue,
    }
  },
})
</script>

<style lang="scss" scoped>
.table-wrapper {
  position: relative;
}

.down-btn {
  position: absolute;
  bottom: 5px;
  left: 16px;
  z-index: 10;
  font-size: 16px;
  padding: 0 16px;
  height: 36px;
  background-color: #1976d2;
  color: white;
}

.management-table {
  :deep(.q-table__bottom) {
    font-size: 18px !important;
    padding-left: 300px; /* 为操作按钮留出更多空间 */

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

  .user-links {
    .user-link {
      color: #1976d2;
      text-decoration: none;
      font-size: 18px;

      &:hover {
        text-decoration: underline;
      }
    }
  }

  .ellipsis {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

/* DOWN button styles */
.down-btn {
  font-size: 16px;
  padding: 0 16px;
  height: 36px;
  background-color: #1976d2;
  color: white;
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

/* 全局通知样式 */
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

/* Add styles for button group */
:deep(.q-btn-group) {
  .q-btn {
    font-size: 16px;
    padding: 8px 16px;
  }
}

/* Add styles for action buttons */
.action-buttons {
  position: absolute;
  bottom: 5px;
  left: 16px;
  z-index: 10;
  display: flex;
  gap: 12px;
}

.select-all-btn {
  font-size: 16px;
  padding: 0 16px;
  height: 36px;
}

.cancel-btn {
  font-size: 16px;
  padding: 0 16px;
  height: 36px;
}

.action-down-btn {
  font-size: 16px;
  padding: 0 16px;
  height: 36px;
}

/* 返回按钮样式 */
.back-btn {
  font-size: 16px;
  padding: 8px 16px;
}

/* 标题栏样式 */
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.flex-grow {
  flex-grow: 1;
}

.invisible-spacer {
  width: 205px; /* 与返回按钮宽度相同，保持标题居中 */
  visibility: hidden;
}
</style>
