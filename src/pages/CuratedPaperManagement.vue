<template>
  <q-page class="q-pa-md">
    <!-- 添加返回Dashboard按钮 -->
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
    
    <div class="text-h4 q-mb-lg text-center">Curated Papers</div>

    <!-- Papers table -->
    <div class="table-wrapper">
      <q-table
        :rows="papers"
        :columns="computedColumns"
        row-key="pmid"
        :loading="loading"
        class="management-table q-mb-xl"
        :rows-per-page-options="[0]"
        :pagination="{rowsPerPage: 0}"
        hide-pagination
        bordered
        flat
      >
        <!-- Add selection column template -->
        <template v-if="showCheckboxes" v-slot:body-cell-selection="props">
          <q-td :props="props" auto-width>
            <q-checkbox
              :model-value="selectedPapers.includes(props.row.pmid)"
              @update:model-value="toggleSelection(props.row.pmid)"
            />
          </q-td>
        </template>

        <!-- 添加整行点击事件 -->
        <template v-slot:body="props">
          <q-tr
            :props="props"
          >
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              style="font-size: 18px"
              class="text-center"
            >
              <!-- 根据列类型调用不同的渲染方法 -->
              <template v-if="col.name === 'selection'">
                <q-checkbox
                  :model-value="selectedPapers.includes(props.row.pmid)"
                  @update:model-value="toggleSelection(props.row.pmid)"
                />
              </template>
              <template v-else-if="col.name === 'title'">
                <div class="ellipsis" style="max-width: 950px">
                  {{ formatTitle(props.row[col.name]) }}
                  <q-tooltip>{{ props.row[col.name] }}</q-tooltip>
                </div>
              </template>
              <template v-else-if="col.name === 'curation_time'">
                {{ formatDateTime(props.row[col.name]) }}
              </template>
              <template v-else-if="col.name === 'action'">
                <q-btn
                  round
                  flat
                  dense
                  color="primary"
                  icon="restart_alt"
                  @click.stop="sendResetRequest(props.row.pmid)"
                >
                  <q-tooltip>Reset to pre-merge version</q-tooltip>
                </q-btn>
                <q-btn
                  round
                  flat
                  dense
                  color="primary"
                  icon="visibility"
                  @click.stop="viewPaperDetails(props.row.pmid)"
                  class="q-ml-sm"
                >
                  <q-tooltip>View this paper</q-tooltip>
                </q-btn>
              </template>
              <template v-else>
                {{ props.row[col.name] }}
              </template>
            </q-td>
          </q-tr>
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
        
        <!-- 当没有论文时显示提示信息 -->
        <template v-slot:no-data>
          <div class="full-width row flex-center q-py-xl">
            <div class="text-center">
              <q-icon name="info" size="2rem" color="grey" />
              <p class="text-h6 text-grey q-mt-md">No curated papers found</p>
              <p class="text-subtitle1 text-grey-7">Papers will appear here after they have been curated</p>
              <q-btn 
                color="primary" 
                label="Back to Dashboard" 
                @click="goToDashboard" 
                class="q-mt-md"
              />
            </div>
          </div>
        </template>
      </q-table>
    </div>
    
    <div class="download-container">
      <!-- Add DOWN button -->
      <q-btn v-if="!showCheckboxes" color="primary" label="DOWNLOAD" class="down-btn" @click="handleDownClick" />
      
      <!-- Add action buttons -->
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
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue'
import axios from 'axios'
import type { QTableColumn } from 'quasar'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { BACKEND_URL } from '../config/api'

interface Paper {
  pmid: string
  title: string
  curation_time: string
  extraction_time: string
}

export default defineComponent({
  name: 'CuratedPaperManagement',

  setup() {
    const router = useRouter()
    const $q = useQuasar()
    const papers = ref<Paper[]>([])
    const loading = ref(true)

    const formatTitle = (val: string) => {
      return val.length > 94 ? val.substring(0, 94) + '...' : val
    }

    const formatDateTime = (dateTimeStr: string) => {
      if (!dateTimeStr) return ''
      const date = new Date(dateTimeStr)
      return date.toLocaleString()
    }

    const goToDashboard = () => {
      router.push('/admin-dashboard')
    }

    const viewPaperDetails = (pmid: string) => {
      // 跳转到论文详情页面
      router.push({
        path: '/analysis',
        query: { 
          url: `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`,
          mode: 'view',
          user: 'Main'  // 查看Main版本
        }
      })
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
        name: 'curation_time',
        label: 'Curation Time',
        field: 'curation_time',
        align: 'center' as const,
        style: 'width: 200px',
      },
      {
        name: 'action',
        label: 'Action',
        field: 'action',
        align: 'center' as const,
        style: 'width: 150px',
      }
    ]

    // Add download-related refs
    const showCheckboxes = ref(false)
    const selectedPapers = ref<string[]>([])
    const isAllSelected = ref(false)

    // Add computed columns
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

    // Add download-related methods
    const handleDownClick = () => {
      showCheckboxes.value = !showCheckboxes.value;
      if (!showCheckboxes.value) {
        selectedPapers.value = [];
        isAllSelected.value = false;
      }
    }

    const toggleSelection = (pmid: string) => {
      if (selectedPapers.value.includes(pmid)) {
        selectedPapers.value = selectedPapers.value.filter((p) => p !== pmid);
        isAllSelected.value = false;
      } else {
        selectedPapers.value.push(pmid);
        isAllSelected.value = selectedPapers.value.length === papers.value.length;
      }
    }

    const selectAllPapers = () => {
      if (isAllSelected.value) {
        selectedPapers.value = [];
        isAllSelected.value = false;
      } else {
        selectedPapers.value = papers.value.map(paper => paper.pmid);
        isAllSelected.value = true;
      }
    }

    const cancelSelection = () => {
      showCheckboxes.value = false;
      selectedPapers.value = [];
      isAllSelected.value = false;
    }

    const handleActionDown = async () => {
      if (selectedPapers.value.length === 0) {
        return;
      }
      
      try {
        const loadingNotif = $q.notify({
          type: 'ongoing',
          message: 'Preparing download files...',
          position: 'top',
          timeout: 0,
          html: true,
          classes: 'notification-message',
          spinner: true,
        });
        
        // 直接使用环境变量中的API URL
        const apiUrl = `${BACKEND_URL}/api/download-papers`;
        
        const response = await axios({
          method: 'post',
          url: apiUrl,
          data: {
            pmids: selectedPapers.value
          },
          responseType: 'blob',
        });
        
        loadingNotif();
        
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'Papers.zip');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        $q.notify({
          type: 'positive',
          message: 'File is ready, starting download',
          position: 'top',
          html: true,
          classes: 'notification-message',
          timeout: 3000,
        });
        
        showCheckboxes.value = false;
        selectedPapers.value = [];
        isAllSelected.value = false;
      } catch (error) {
        console.error('Error downloading file:', error);
        
        const errorMessage = (() => {
          if (error && typeof error === 'object') {
            if ('response' in error && 
                error.response && 
                typeof error.response === 'object' && 
                'data' in error.response && 
                error.response.data && 
                typeof error.response.data === 'object' && 
                'message' in error.response.data) {
              return String(error.response.data.message);
            }
            
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

    // 使用新的API端点获取已完成curation的论文
    const loadPapers = async () => {
      try {
        // 直接使用环境变量中的API URL
        const apiUrl = `${BACKEND_URL}/api/curated-papers`;

        const response = await axios.get(apiUrl)
        console.log("加载已完成curation的论文:", response.data);
        
        if (response.data && response.data.papers) {
          papers.value = response.data.papers;
        } else {
          papers.value = [];
        }
      } catch (error) {
        console.error('Error loading papers:', error)
        papers.value = []
      } finally {
        loading.value = false
      }
    }

    // 添加重置功能
    const sendResetRequest = async (pmid: string) => {
      try {
        // 直接使用环境变量中的API URL
        const apiUrl = `${BACKEND_URL}/api/reset-curation`;

        // 发送重置请求
        const response = await axios.post(apiUrl, { pmid });
        console.log("重置请求响应:", response.data);
        
        // 如果成功重置，重定向到CurationWorkPage进行重新curation
        if (response.data && response.data.success) {
          // 重定向到CurationWorkPage
          router.push({
            path: '/curation-work',
            query: { pmid }
          });
        }
      } catch (error) {
        console.error('Error sending reset request:', error);
      }
    }

    onMounted(() => {
      loadPapers()
    })

    return {
      papers,
      columns,
      computedColumns,
      loading,
      formatTitle,
      formatDateTime,
      goToDashboard,
      viewPaperDetails,
      sendResetRequest,
      // Add new return values
      showCheckboxes,
      selectedPapers,
      isAllSelected,
      handleDownClick,
      toggleSelection,
      selectAllPapers,
      cancelSelection,
      handleActionDown,
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
  margin-bottom: 50px; /* 为下载按钮留出空间 */
}

.download-container {
  position: relative;
  margin-top: -48px; /* 上移到表格底部 */
  margin-bottom: 20px;
  z-index: 5;
}

.down-btn {
  margin-left: 16px;
  font-size: 16px;
  padding: 0 16px;
  height: 36px;
  background-color: #1976d2;
  color: white;
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

  .cursor-pointer {
    cursor: pointer;
    transition: background-color 0.3s;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.03);
    }
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

/* Update tooltip styles */
:deep(.tooltip-text) {
  font-size: 18px !important;
}

/* Add styles for action buttons */
.action-buttons {
  margin-left: 16px;
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
</style> 