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
    
    <div class="text-h4 q-mb-lg text-center">Papers Need Curation</div>

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
        <!-- 添加整行点击事件 -->
        <template v-slot:body="props">
          <q-tr
            :props="props"
            class="cursor-pointer"
            @click="navigateToCurationWork(props.row.pmid)"
          >
            <q-td
              v-for="col in props.cols"
              :key="col.name"
              :props="props"
              style="font-size: 18px"
              class="text-center"
            >
              <!-- 根据列类型调用不同的渲染方法 -->
              <template v-if="col.name === 'title'">
                <div class="ellipsis" style="max-width: 950px">
                  {{ formatTitle(props.row[col.name]) }}
                  <q-tooltip>{{ props.row[col.name] }}</q-tooltip>
                </div>
              </template>
              <template v-else-if="col.name === 'assigned_user'">
                <div class="user-text">
                  <template v-for="(user, index) in props.row[col.name]" :key="user">
                    <span class="user-name">{{ user }}</span>
                    <span v-if="index < props.row[col.name].length - 1">, </span>
                  </template>
                </div>
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
        
        <!-- 当没有论文需要管理时显示提示信息 -->
        <template v-slot:no-data>
          <div class="full-width row flex-center q-py-xl">
            <div class="text-center">
              <q-icon name="info" size="2rem" color="grey" />
              <p class="text-h6 text-grey q-mt-md">No papers need curation at this time</p>
              <p class="text-subtitle1 text-grey-7">Papers will appear here when there are at least two user submissions for the same paper</p>
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
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'
import axios from 'axios'
import type { QTableColumn } from 'quasar'
import { useRouter } from 'vue-router'
import { BACKEND_URL } from '../config/api'

interface Paper {
  pmid: string
  title: string
  assigned_user: string[]
  extraction_time?: string
}

export default defineComponent({
  name: 'CurationManagementPage',

  setup() {
    const router = useRouter()
    const papers = ref<Paper[]>([])
    const loading = ref(true)

    const formatTitle = (val: string) => {
      return val.length > 94 ? val.substring(0, 94) + '...' : val
    }

    const goToDashboard = () => {
      router.push('/admin-dashboard')
    }

    const navigateToCurationWork = (pmid: string) => {
      router.push({
        path: '/curation-work',
        query: { pmid }
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
        name: 'assigned_user',
        label: 'Assigned User',
        field: 'assigned_user',
        align: 'center' as const,
        style: 'width: 200px',
      },
    ]

    // 使用新的API端点获取需要管理的论文
    const loadPapers = async () => {
      try {
        // 直接使用环境变量中的API URL
        const apiUrl = `${BACKEND_URL}/api/curation-papers`;

        const response = await axios.get(apiUrl)
        console.log("加载需要管理的论文:", response.data);
        
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

    onMounted(() => {
      loadPapers()
    })

    return {
      papers,
      columns,
      loading,
      formatTitle,
      goToDashboard,
      navigateToCurationWork
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

  .user-text {
    .user-name {
      color: #333;
      font-size: 18px;
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
</style> 