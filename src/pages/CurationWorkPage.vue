<template>
  <q-page class="q-pa-md">
    <!-- 顶部导航区域 -->
    <div class="row items-center justify-between q-mb-lg top-nav">
      <q-btn
        flat
        round
        color="primary"
        icon="arrow_back"
        class="q-mr-sm back-btn"
        @click="$router.push('/relations-curation')"
        size="md"
      >
        <q-tooltip class="custom-tooltip" style="font-size: 16px !important;">Back To Curation Page</q-tooltip>
      </q-btn>
      <div class="text-center col">
        <div v-if="pmid" style="font-size: 24px" class="text-primary q-mb-sm">
          PMID: {{ pmid }}
        </div>
      </div>
    </div>

    <!-- 整体内容区域 -->
    <div class="content-container">
      <!-- Abstract 标题部分 (绿色框，可以滚动) -->
      <div class="abstract-header text-h5 text-center">Abstract</div>
      
      <!-- Abstract 内容部分 (红色框，固定位置) -->
      <div class="sticky-content">
        <q-card class="abstract-container">
          <q-card-section class="q-pt-xs q-pb-xs">
            <div v-if="isLoading" class="text-center">
              <q-spinner-dots size="40px" />
              <div class="text-subtitle1 q-mt-md">Fetching paper data...</div>
            </div>
            <div v-else-if="!title && !abstract" class="text-center text-grey-7">
              No data available
            </div>
            <template v-else>
              <!-- Title -->
              <div class="text-h6 q-mb-xs">
                {{ title }}
              </div>
              <!-- Abstract -->
              <div
                class="text-body1 abstract"
                ref="abstractText"
                v-html="processedAbstract"
              ></div>
            </template>
          </q-card-section>
        </q-card>
      </div>

      <!-- 下方可滚动的Relations部分 -->
      <div class="relations-section">
        <div class="relations-header text-h5 text-center">
          <span v-if="currentArea === 'area1'" style="color: #4caf50;" :class="{ 'fade-in': isAreaSwitching }">Same Relations</span>
          <span v-else style="color: #f44336;" :class="{ 'fade-in': isAreaSwitching }">Different Relations</span>
        </div>
        <q-card class="relations-container" :class="{ 'fade-in': isAreaSwitching }">
          <q-card-section class="header-section">
            <div class="header-container">
              <!-- 左侧导航按钮 -->
              <div class="nav-button left-nav">
                <q-btn 
                  round
                  color="primary" 
                  icon="arrow_back" 
                  class="navigation-btn"
                  @click="switchArea('prev')"
                  :disable="isBatchMode"
                />
              </div>
              
              <!-- Start Curation按钮 -->
              <div class="start-curation-container">
                <!-- 非curation模式下显示Start Curation按钮 -->
                <q-btn 
                  v-if="!isCurationMode"
                  color="green"
                  class="start-curation-btn q-px-md"
                  icon="play_circle"
                  label="START CURATION"
                  no-caps
                  @click="startCuration"
                />
                
                <!-- curation模式下显示Cancel和Save按钮 -->
                <div v-else class="curation-actions-row">
                  <q-btn 
                    color="red" 
                    class="curation-action-btn q-mr-md" 
                    icon="cancel"
                    label="CANCEL"
                    no-caps
                    @click="cancelCuration"
                  >
                    <q-tooltip class="tooltip-16px">Discard changes from this curation session</q-tooltip>
                  </q-btn>
                  <q-btn 
                    color="green" 
                    class="curation-action-btn" 
                    icon="save"
                    label="SAVE"
                    no-caps
                    @click="saveCuration"
                  >
                    <q-tooltip class="tooltip-16px">Save changes from this curation session</q-tooltip>
                  </q-btn>
                </div>
              </div>
              
              <!-- 批量操作按钮，位于左侧和中间之间 -->
              <div class="batch-btn-container">
                <!-- 非批量模式显示的按钮 -->
                <q-btn 
                  v-if="!isBatchMode"
                  color="primary" 
                  class="batch-btn q-px-md" 
                  label="BATCH OPERATIONS" 
                  @click="toggleBatchMode"
                  :disable="!isCurationMode"
                >
                  <q-tooltip v-if="!isCurationMode" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                </q-btn>
                
                <!-- 批量模式下显示的按钮组 -->
                <div v-if="isBatchMode" class="batch-actions-row">
                  <q-btn 
                    color="blue" 
                    class="batch-action-btn select-all-btn q-mr-sm" 
                    :label="selectAllButtonLabel" 
                    @click="selectAllRows"
                    :disable="!isCurationMode"
                  >
                    <q-tooltip v-if="!isCurationMode" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                  </q-btn>
                  <q-btn 
                    round 
                    color="green" 
                    icon="check" 
                    class="batch-action-btn q-mr-sm" 
                    @click="batchAccept"
                    :disable="!isCurationMode"
                  >
                    <q-tooltip v-if="isCurationMode">Accept Selected</q-tooltip>
                    <q-tooltip v-if="!isCurationMode" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                  </q-btn>
                  <q-btn 
                    round 
                    color="red" 
                    icon="close" 
                    class="batch-action-btn q-mr-sm" 
                    @click="batchReject"
                    :disable="!isCurationMode"
                  >
                    <q-tooltip v-if="isCurationMode">Reject Selected</q-tooltip>
                    <q-tooltip v-if="!isCurationMode" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                  </q-btn>
                  <q-btn 
                    round 
                    color="primary" 
                    icon="autorenew" 
                    class="batch-action-btn q-mr-sm" 
                    @click="batchReset"
                    :disable="!isCurationMode"
                  >
                    <q-tooltip v-if="isCurationMode">Reset Selected</q-tooltip>
                    <q-tooltip v-if="!isCurationMode" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                  </q-btn>
                  <q-btn 
                    round 
                    color="grey" 
                    icon="exit_to_app" 
                    class="batch-action-btn" 
                    @click="exitBatchMode"
                  >
                    <q-tooltip>Exit Batch Mode</q-tooltip>
                  </q-btn>
                </div>
              </div>
              
              <!-- 中央标题 -->
              <!-- 已移除中央标题区域，标题已上移到relations-header位置 -->
              
              <!-- 添加统计信息区域 -->
              <div class="stats-container">
                <div class="resolution-stats">
                  Resolved: {{ resolvedCount }}/{{ totalCount }} ({{ resolvedPercentage }}%)
                </div>
                <q-btn
                  color="purple"
                  class="merge-btn q-ml-lg"
                  label="MERGE"
                  icon="merge_type"
                  :disable="resolvedCount < totalCount || isCurationMode"
                  :style="resolvedCount < totalCount || isCurationMode ? 'background-color: #a0a0a0 !important; color: white;' : ''"
                  @click="handleMerge"
                >
                  <q-tooltip v-if="resolvedCount < totalCount" class="merge-tooltip">
                    All relations must be resolved before merging
                  </q-tooltip>
                  <q-tooltip v-else-if="isCurationMode" class="merge-tooltip">
                    Please save and verify changes before merging
                  </q-tooltip>
                </q-btn>
              </div>
              
              <!-- 右侧导航按钮 -->
              <div class="nav-button right-nav">
                <q-btn 
                  round
                  color="primary" 
                  icon="arrow_forward" 
                  class="navigation-btn"
                  @click="switchArea('next')"
                  :disable="isBatchMode"
                />
              </div>
            </div>
          </q-card-section>
          <q-card-section>
            <div v-if="isLoading" class="text-center">
              <q-spinner-dots size="40px" />
              <div class="text-subtitle1 q-mt-md">Processing data...</div>
            </div>
            <div v-else-if="!tableData.length" class="text-center text-grey-7">
              No relations available
            </div>
            <template v-else>
              <!-- 区域一 -->
              <q-table
                v-if="currentArea === 'area1'"
                :rows="area1Relations"
                :columns="isBatchMode ? columnsWithSelection : columns"
                row-key="id"
                hide-pagination
                :rows-per-page-options="[0]"
                class="analysis-table"
              >
                <!-- Custom template for body cells in Area 1 -->
                <template v-slot:body="props">
                  <q-tr 
                    :props="props" 
                    @mouseover="highlightText(props.row, 'hover')" 
                    @mouseout="clearHighlight('hover')"
                    @click="highlightText(props.row, 'click', $event)"
                    :class="{'hovered-row': hoveredRowId === props.row.id, 'clicked-row': clickedRowId === props.row.id}"
                    :data-row-id="props.row.id"
                  >
                    <!-- 统一处理所有列 -->
                    <q-td 
                      v-for="col in props.cols.filter((c: QTableColumn) => c.name !== 'actions')" 
                      :key="col.name" 
                      :props="props" 
                      :class="[
                        props.row.status === 'accepted' ? 'bg-green-1' : 
                        props.row.status === 'rejected' ? 'bg-red-1' : '', 
                        'text-center',
                        col.name === 'users' ? 'text-left users-cell' : '',
                        !isCurationMode ? 'dimmed-row' : 
                        hasEditingRow && props.row.status !== 'editing' ? 'dimmed-row' : ''
                      ]"
                      :style="col.name === 'selection' ? 'width: 50px; padding-left: 16px;' : 
                             col.name === 'users' ? 'width: 100px; padding-left: 16px; padding-right: 0;' : ''"
                    >
                      <!-- Expand button -->
                      <template v-if="col.name === 'expand'">
                        <q-btn
                          flat
                          dense
                          round
                          size="md"
                          :icon="isExpanded(props.row) ? 'expand_more' : 'chevron_right'"
                          @click.stop="toggleExpand(props.row)"
                          class="expand-button"
                        />
                      </template>

                      <!-- Selection checkbox -->
                      <template v-else-if="col.name === 'selection'">
                        <q-checkbox 
                          v-model="props.row._selected" 
                          @update:model-value="toggleRowSelection(props.row)"
                          :disable="hasEditingRow"
                        />
                      </template>

                      <!-- Users column -->
                      <template v-else-if="col.name === 'users'">
                        <div class="user-circles-container">
                          <template v-if="props.row.users && props.row.users.length > 0">
                            <div v-for="(user, index) in props.row.users.slice(0, 3)" :key="index" 
                                 class="user-circle" 
                                 :style="`background-color: ${getUserColor(user)};`">
                              {{ getUserInitials(user) }}
                            </div>
                            <span v-if="props.row.users.length > 3" class="more-users-text">
                              +{{ props.row.users.length - 3 }}
                            </span>
                          </template>
                          <q-tooltip class="users-tooltip" max-width="none" style="white-space: nowrap !important;">
                            {{ props.row.users ? props.row.users.join(', ') : '' }}
                          </q-tooltip>
                        </div>
                      </template>

                      <!-- Data columns (head, label, tail) -->
                      <template v-else>
                        <div v-if="props.row.status === 'editing' && ['head', 'label', 'tail'].includes(col.name)">
                          <q-input 
                            v-model="props.row[col.name]" 
                            dense 
                            outlined
                            class="edit-input"
                            align="center"
                            @blur="updateFieldPreview(props.row, col.name)"
                          />
                        </div>
                        <div v-else class="relation-cell-content">
                          {{ col.value }}
                        </div>
                      </template>
                    </q-td>

                    <!-- Actions column -->
                    <q-td 
                      v-for="col in props.cols.filter((c: QTableColumn) => c.name === 'actions')" 
                      :key="col.name"
                      :props="props" 
                      :class="[
                        props.row.status === 'accepted' ? 'bg-green-1' : 
                        props.row.status === 'rejected' ? 'bg-red-1' : '', 
                        'text-center',
                        !isCurationMode ? 'dimmed-row' : 
                        hasEditingRow && props.row.status !== 'editing' ? 'dimmed-row' : ''
                      ]"
                    >
                      <!-- 保持原有的actions列内容不变 -->
                      <!-- 正常状态下的按钮 -->
                      <div v-if="props.row.status !== 'editing'" class="row justify-center items-center no-wrap">
                        <!-- 已接受状态下的按钮 -->
                        <template v-if="props.row.status === 'accepted'">
                          <q-btn flat round dense color="primary" icon="autorenew" class="action-btn" 
                            @click="resetRowStatus(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Reset Status</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="red" icon="close" class="action-btn" 
                            @click="rejectRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Reject</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="blue" icon="edit" class="action-btn" 
                            @click="editRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Edit</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                        </template>
                        
                        <!-- 已拒绝状态下的按钮 -->
                        <template v-else-if="props.row.status === 'rejected'">
                          <q-btn flat round dense color="green" icon="check" class="action-btn" 
                            @click="acceptRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Accept</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="primary" icon="autorenew" class="action-btn" 
                            @click="resetRowStatus(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Reset Status</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="blue" icon="edit" class="action-btn" 
                            @click="editRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Edit</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                        </template>
                        
                        <!-- 默认状态下的按钮 -->
                        <template v-else>
                          <q-btn flat round dense color="green" icon="check" class="action-btn" 
                            @click="acceptRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Accept</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="red" icon="close" class="action-btn" 
                            @click="rejectRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Reject</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="blue" icon="edit" class="action-btn" 
                            @click="editRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Edit</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                        </template>
                      </div>
                      
                      <!-- 编辑状态下的按钮 -->
                      <div v-else class="row justify-center items-center no-wrap">
                        <q-btn flat round dense color="red" icon="cancel" class="action-btn" @click="cancelEdit(props.row)">
                          <q-tooltip anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Cancel</q-tooltip>
                        </q-btn>
                        <q-btn flat round dense color="green" icon="save" class="action-btn" @click="saveEdit(props.row)">
                          <q-tooltip anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Save</q-tooltip>
                        </q-btn>
                      </div>
                    </q-td>
                  </q-tr>

                  <!-- 展开的内容区域 -->
                  <q-tr v-show="isExpanded(props.row)" class="meta-relation-row">
                    <q-td :colspan="isBatchMode ? props.cols.length : props.cols.length">
                      <div class="meta-relations q-pa-md">
                        <!-- Supporting Text -->
                        <div class="text-input q-mb-lg">
                          <div class="section-title text-center q-mb-md">Supporting Text</div>
                          <template v-if="props.row.status === 'editing'">
                            <q-input
                              v-model="props.row.text"
                              type="textarea"
                              filled
                              placeholder="Enter supporting text here..."
                              class="supporting-text-input"
                              @blur="updateTextPreview(props.row)"
                            />
                          </template>
                          <template v-else>
                            <div class="supporting-text-display">
                              {{ props.row.text || 'EMPTY' }}
                            </div>
                          </template>
                        </div>

                        <!-- Note -->
                        <div class="text-input q-mb-lg">
                          <div class="section-title text-center q-mb-md">Note</div>
                          <template v-if="props.row.status === 'editing'">
                            <div class="note-display note-edit-mode">
                              <template v-for="(noteContent, index) in parseNotes(props.row.note)" :key="index">
                                <div class="note-user-section">
                                  <div class="note-user-header">
                                    <div class="note-user-name">{{ noteContent.user }}</div>
                                    <q-btn
                                      flat
                                      round
                                      dense
                                      color="negative"
                                      icon="delete"
                                      size="sm"
                                      class="delete-note-btn"
                                      @click="deleteNoteContent(props.row, noteContent.user)"
                                    >
                                      <q-tooltip>Delete this note</q-tooltip>
                                    </q-btn>
                                  </div>
                                  <q-input
                                    v-model="noteContent.content"
                                    type="textarea"
                                    filled
                                    placeholder="Enter your notes here..."
                                    class="note-content-input"
                                    @update:model-value="updateNoteContent(props.row, noteContent.user, noteContent.content)"
                                  />
                                </div>
                              </template>
                              <div v-if="!props.row.note" class="empty-note">EMPTY</div>
                              
                              <!-- 添加笔记按钮 -->
                              <div class="text-center q-mt-md">
                                <q-btn 
                                  round 
                                  color="primary" 
                                  icon="add" 
                                  size="md"
                                  class="add-note-btn"
                                  @click="showAddNoteDialog(props.row)"
                                >
                                  <q-tooltip>Add new note</q-tooltip>
                                </q-btn>
                              </div>
                            </div>
                          </template>
                          <template v-else>
                            <div class="note-display">
                              <template v-for="(noteContent, index) in parseNotes(props.row.note)" :key="index">
                                <div class="note-user-section">
                                  <div class="note-user-name">{{ noteContent.user }}</div>
                                  <div class="note-user-content">{{ noteContent.content }}</div>
                                </div>
                              </template>
                              <div v-if="!props.row.note" class="empty-note">EMPTY</div>
                            </div>
                          </template>
                        </div>

                        <!-- Meta Relations -->
                        <div class="text-input q-mb-lg">
                          <div class="section-title text-center q-mb-md">Meta Relations</div>
                          <div class="row q-col-gutter-md">
                            <div class="col-12">
                              <template v-if="props.row.status === 'editing'">
                                <q-markup-table flat bordered>
                                  <thead>
                                    <tr>
                                      <th class="text-center">Target</th>
                                      <th class="text-center">Label</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    <tr v-for="(meta, index) in props.row.metaRelations || []" :key="index">
                                      <td class="text-center">
                                        <q-input v-model="meta.target" dense outlined class="meta-input" />
                                      </td>
                                      <td class="text-center" style="position: relative;">
                                        <div class="row items-center no-wrap">
                                          <q-input v-model="meta.label" dense outlined class="meta-input" />
                                          <q-btn flat round dense color="red" icon="delete" class="delete-meta-btn" @click="removeMetaRelation(props.row, index)">
                                            <q-tooltip>Delete</q-tooltip>
                                          </q-btn>
                                        </div>
                                      </td>
                                    </tr>
                                    <!-- Add button row -->
                                    <tr>
                                      <td colspan="2" class="text-center q-py-md">
                                        <q-btn round color="primary" icon="add" size="md" class="add-meta-btn" @click="addMetaRelation(props.row)" />
                                      </td>
                                    </tr>
                                  </tbody>
                                </q-markup-table>
                              </template>
                              <template v-else>
                                <q-markup-table flat bordered>
                                  <thead>
                                    <tr>
                                      <th class="text-center">Target</th>
                                      <th class="text-center">Label</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    <template v-if="props.row.metaRelations?.length > 0">
                                      <tr v-for="(meta, index) in props.row.metaRelations" :key="index">
                                        <td class="text-center">{{ meta.target }}</td>
                                        <td class="text-center">{{ meta.label }}</td>
                                      </tr>
                                    </template>
                                    <template v-else>
                                      <tr>
                                        <td class="text-center">NULL</td>
                                        <td class="text-center">NULL</td>
                                      </tr>
                                    </template>
                                  </tbody>
                                </q-markup-table>
                              </template>
                            </div>
                          </div>
                        </div>
                      </div>
                    </q-td>
                  </q-tr>
                </template>
              </q-table>
              
              <!-- 区域二 -->
              <q-table
                v-else
                :rows="area2Relations"
                :columns="isBatchMode ? columnsWithSelection : columns"
                row-key="id"
                hide-pagination
                :rows-per-page-options="[0]"
                class="analysis-table"
              >
                <!-- 为区域二复制相同的模板 -->
                <template v-slot:body="props">
                  <q-tr 
                    :props="props" 
                    @mouseover="highlightText(props.row, 'hover')" 
                    @mouseout="clearHighlight('hover')"
                    @click="highlightText(props.row, 'click', $event)"
                    :class="{'hovered-row': hoveredRowId === props.row.id, 'clicked-row': clickedRowId === props.row.id}"
                    :data-row-id="props.row.id"
                  >
                    <!-- 统一处理所有列 -->
                    <q-td 
                      v-for="col in props.cols.filter((c: QTableColumn) => c.name !== 'actions')" 
                      :key="col.name" 
                      :props="props" 
                      :class="[
                        props.row.status === 'accepted' ? 'bg-green-1' : 
                        props.row.status === 'rejected' ? 'bg-red-1' : '', 
                        'text-center',
                        col.name === 'users' ? 'text-left users-cell' : '',
                        !isCurationMode ? 'dimmed-row' : 
                        hasEditingRow && props.row.status !== 'editing' ? 'dimmed-row' : ''
                      ]"
                      :style="col.name === 'selection' ? 'width: 50px; padding-left: 16px;' : 
                             col.name === 'users' ? 'width: 100px; padding-left: 16px; padding-right: 0;' : ''"
                    >
                      <!-- Expand button -->
                      <template v-if="col.name === 'expand'">
                        <q-btn
                          flat
                          dense
                          round
                          size="md"
                          :icon="isExpanded(props.row) ? 'expand_more' : 'chevron_right'"
                          @click.stop="toggleExpand(props.row)"
                          class="expand-button"
                        />
                      </template>

                      <!-- Selection checkbox -->
                      <template v-else-if="col.name === 'selection'">
                        <q-checkbox 
                          v-model="props.row._selected" 
                          @update:model-value="toggleRowSelection(props.row)"
                          :disable="hasEditingRow"
                        />
                      </template>

                      <!-- Users column -->
                      <template v-else-if="col.name === 'users'">
                        <div class="user-circles-container">
                          <template v-if="props.row.users && props.row.users.length > 0">
                            <div v-for="(user, index) in props.row.users.slice(0, 3)" :key="index" 
                                 class="user-circle" 
                                 :style="`background-color: ${getUserColor(user)};`">
                              {{ getUserInitials(user) }}
                            </div>
                            <span v-if="props.row.users.length > 3" class="more-users-text">
                              +{{ props.row.users.length - 3 }}
                            </span>
                          </template>
                          <q-tooltip class="users-tooltip" max-width="none" style="white-space: nowrap !important;">
                            {{ props.row.users ? props.row.users.join(', ') : '' }}
                          </q-tooltip>
                        </div>
                      </template>

                      <!-- Data columns (head, label, tail) -->
                      <template v-else>
                        <div v-if="props.row.status === 'editing' && ['head', 'label', 'tail'].includes(col.name)">
                          <q-input 
                            v-model="props.row[col.name]" 
                            dense 
                            outlined
                            class="edit-input"
                            align="center"
                            @blur="updateFieldPreview(props.row, col.name)"
                          />
                        </div>
                        <div v-else class="relation-cell-content">
                          {{ col.value }}
                        </div>
                      </template>
                    </q-td>

                    <!-- Actions column -->
                    <q-td 
                      v-for="col in props.cols.filter((c: QTableColumn) => c.name === 'actions')" 
                      :key="col.name"
                      :props="props" 
                      :class="[
                        props.row.status === 'accepted' ? 'bg-green-1' : 
                        props.row.status === 'rejected' ? 'bg-red-1' : '', 
                        'text-center',
                        !isCurationMode ? 'dimmed-row' : 
                        hasEditingRow && props.row.status !== 'editing' ? 'dimmed-row' : ''
                      ]"
                    >
                      <!-- 保持原有的actions列内容不变 -->
                      <!-- 正常状态下的按钮 -->
                      <div v-if="props.row.status !== 'editing'" class="row justify-center items-center no-wrap">
                        <!-- 已接受状态下的按钮 -->
                        <template v-if="props.row.status === 'accepted'">
                          <q-btn flat round dense color="primary" icon="autorenew" class="action-btn" 
                            @click="resetRowStatus(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Reset Status</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="red" icon="close" class="action-btn" 
                            @click="rejectRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Reject</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="blue" icon="edit" class="action-btn" 
                            @click="editRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Edit</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                        </template>
                        
                        <!-- 已拒绝状态下的按钮 -->
                        <template v-else-if="props.row.status === 'rejected'">
                          <q-btn flat round dense color="green" icon="check" class="action-btn" 
                            @click="acceptRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Accept</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="primary" icon="autorenew" class="action-btn" 
                            @click="resetRowStatus(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Reset Status</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="blue" icon="edit" class="action-btn" 
                            @click="editRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Edit</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                        </template>
                        
                        <!-- 默认状态下的按钮 -->
                        <template v-else>
                          <q-btn flat round dense color="green" icon="check" class="action-btn" 
                            @click="acceptRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Accept</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="red" icon="close" class="action-btn" 
                            @click="rejectRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Reject</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                          <q-btn flat round dense color="blue" icon="edit" class="action-btn" 
                            @click="editRow(props.row)"
                            :disable="(hasEditingRow && !isCurrentEditingRow(props.row)) || !isCurationMode">
                            <q-tooltip v-if="(!hasEditingRow || isCurrentEditingRow(props.row)) && isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Edit</q-tooltip>
                            <q-tooltip v-if="!isCurationMode" anchor="center right" self="center left" :offset="[10, 0]" class="tooltip-16px" style="font-size: 15px">Please start curation first</q-tooltip>
                          </q-btn>
                        </template>
                      </div>
                      
                      <!-- 编辑状态下的按钮 -->
                      <div v-else class="row justify-center items-center no-wrap">
                        <q-btn flat round dense color="red" icon="cancel" class="action-btn" @click="cancelEdit(props.row)">
                          <q-tooltip anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Cancel</q-tooltip>
                        </q-btn>
                        <q-btn flat round dense color="green" icon="save" class="action-btn" @click="saveEdit(props.row)">
                          <q-tooltip anchor="center right" self="center left" :offset="[10, 0]" style="font-size: 16px">Save</q-tooltip>
                        </q-btn>
                      </div>
                    </q-td>
                  </q-tr>

                  <!-- 展开的内容区域 -->
                  <q-tr v-show="isExpanded(props.row)" class="meta-relation-row">
                    <q-td :colspan="isBatchMode ? props.cols.length : props.cols.length">
                      <div class="meta-relations q-pa-md">
                        <!-- Supporting Text -->
                        <div class="text-input q-mb-lg">
                          <div class="section-title text-center q-mb-md">Supporting Text</div>
                          <template v-if="props.row.status === 'editing'">
                            <q-input
                              v-model="props.row.text"
                              type="textarea"
                              filled
                              placeholder="Enter supporting text here..."
                              class="supporting-text-input"
                              @blur="updateTextPreview(props.row)"
                            />
                          </template>
                          <template v-else>
                            <div class="supporting-text-display">
                              {{ props.row.text || 'EMPTY' }}
                            </div>
                          </template>
                        </div>

                        <!-- Note -->
                        <div class="text-input q-mb-lg">
                          <div class="section-title text-center q-mb-md">Note</div>
                          <template v-if="props.row.status === 'editing'">
                            <div class="note-display note-edit-mode">
                              <template v-for="(noteContent, index) in parseNotes(props.row.note)" :key="index">
                                <div class="note-user-section">
                                  <div class="note-user-header">
                                    <div class="note-user-name">{{ noteContent.user }}</div>
                                    <q-btn
                                      flat
                                      round
                                      dense
                                      color="negative"
                                      icon="delete"
                                      size="sm"
                                      class="delete-note-btn"
                                      @click="deleteNoteContent(props.row, noteContent.user)"
                                    >
                                      <q-tooltip>Delete this note</q-tooltip>
                                    </q-btn>
                                  </div>
                                  <q-input
                                    v-model="noteContent.content"
                                    type="textarea"
                                    filled
                                    placeholder="Enter your notes here..."
                                    class="note-content-input"
                                    @update:model-value="updateNoteContent(props.row, noteContent.user, noteContent.content)"
                                  />
                                </div>
                              </template>
                              <div v-if="!props.row.note" class="empty-note">EMPTY</div>
                              
                              <!-- 添加笔记按钮 -->
                              <div class="text-center q-mt-md">
                                <q-btn 
                                  round 
                                  color="primary" 
                                  icon="add" 
                                  size="md"
                                  class="add-note-btn"
                                  @click="showAddNoteDialog(props.row)"
                                >
                                  <q-tooltip>Add new note</q-tooltip>
                                </q-btn>
                              </div>
                            </div>
                          </template>
                          <template v-else>
                            <div class="note-display">
                              <template v-for="(noteContent, index) in parseNotes(props.row.note)" :key="index">
                                <div class="note-user-section">
                                  <div class="note-user-name">{{ noteContent.user }}</div>
                                  <div class="note-user-content">{{ noteContent.content }}</div>
                                </div>
                              </template>
                              <div v-if="!props.row.note" class="empty-note">EMPTY</div>
                            </div>
                          </template>
                        </div>

                        <!-- Meta Relations -->
                        <div class="text-input q-mb-lg">
                          <div class="section-title text-center q-mb-md">Meta Relations</div>
                          <div class="row q-col-gutter-md">
                            <div class="col-12">
                              <template v-if="props.row.status === 'editing'">
                                <q-markup-table flat bordered>
                                  <thead>
                                    <tr>
                                      <th class="text-center">Target</th>
                                      <th class="text-center">Label</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    <tr v-for="(meta, index) in props.row.metaRelations || []" :key="index">
                                      <td class="text-center">
                                        <q-input v-model="meta.target" dense outlined class="meta-input" />
                                      </td>
                                      <td class="text-center" style="position: relative;">
                                        <div class="row items-center no-wrap">
                                          <q-input v-model="meta.label" dense outlined class="meta-input" />
                                          <q-btn flat round dense color="red" icon="delete" class="delete-meta-btn" @click="removeMetaRelation(props.row, index)">
                                            <q-tooltip>Delete</q-tooltip>
                                          </q-btn>
                                        </div>
                                      </td>
                                    </tr>
                                    <!-- Add button row -->
                                    <tr>
                                      <td colspan="2" class="text-center q-py-md">
                                        <q-btn round color="primary" icon="add" size="md" class="add-meta-btn" @click="addMetaRelation(props.row)" />
                                      </td>
                                    </tr>
                                  </tbody>
                                </q-markup-table>
                              </template>
                              <template v-else>
                                <q-markup-table flat bordered>
                                  <thead>
                                    <tr>
                                      <th class="text-center">Target</th>
                                      <th class="text-center">Label</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    <template v-if="props.row.metaRelations?.length > 0">
                                      <tr v-for="(meta, index) in props.row.metaRelations" :key="index">
                                        <td class="text-center">{{ meta.target }}</td>
                                        <td class="text-center">{{ meta.label }}</td>
                                      </tr>
                                    </template>
                                    <template v-else>
                                      <tr>
                                        <td class="text-center">NULL</td>
                                        <td class="text-center">NULL</td>
                                      </tr>
                                    </template>
                                  </tbody>
                                </q-markup-table>
                              </template>
                            </div>
                          </div>
                        </div>
                      </div>
                    </q-td>
                  </q-tr>
                </template>
              </q-table>
            </template>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
  
  <!-- 添加笔记对话框 -->
  <q-dialog v-model="addNoteDialogVisible" persistent>
    <q-card style="min-width: 800px; width: 70%;">
      <q-card-section class="row items-center">
        <div class="text-h5">Add New Note</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup size="md" />
      </q-card-section>

      <q-card-section>
        <q-input
          v-model="newNoteUser"
          label="Username"
          outlined
          class="q-mb-md add-note-input"
          style="font-size: 18px"
        />
        
        <q-input
          v-model="newNoteContent"
          type="textarea"
          label="Note Content"
          outlined
          autogrow
          class="note-content-input add-note-input"
          style="font-size: 18px"
          rows="9"
        />
      </q-card-section>

      <q-card-actions align="right" class="q-pa-md">
        <q-btn flat label="Cancel" color="negative" v-close-popup class="text-body1" style="font-size: 16px" />
        <q-btn flat label="Add" color="primary" @click="addNewNote" :disable="!newNoteUser || !newNoteContent" v-close-popup class="text-body1" style="font-size: 16px" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, nextTick, onUnmounted } from 'vue'
import type { QTableColumn } from 'quasar'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useQuasar } from 'quasar'
import { BACKEND_URL } from '../config/api'

/**
 * 表格行数据结构
 */
interface TableRow {
  id: number // 行唯一标识符
  head: string // 头实体
  label: string // 关系
  tail: string // 尾实体
  text?: string // 关系的文本描述
  status?: 'accepted' | 'rejected' | 'editing' | null // 行状态
  originalHead?: string // 编辑前的头实体(用于恢复)
  originalLabel?: string // 编辑前的关系(用于恢复)
  originalTail?: string // 编辑前的尾实体(用于恢复)
  originalStatus?: 'accepted' | 'rejected' | 'editing' | null // 编辑前的状态(用于恢复)
  originalText?: string // 编辑前的text值(用于恢复)
  originalNote?: string // 编辑前的note值(用于恢复)
  originalMetaRelations?: MetaRelation[] // 编辑前的metaRelations值(用于恢复)
  _selected?: boolean // 是否被选中(批量操作)
  users: string[] // 对于different_relations，记录关联的用户
  metaRelations?: MetaRelation[] // 添加metaRelations字段
  note?: string // 添加note字段
}

// 定义 MetaRelation 接口
interface MetaRelation {
  label: string;
  target: string;
}

// 接口定义：来自服务器的same_relation数据结构
interface SameRelation {
  head: string
  tail: string
  label: string
  text: string
  status: string
  metaRelations?: MetaRelation[]
  users: string[] // 添加users字段
  note?: string // 添加note字段
}

// 接口定义：来自服务器的different_relation数据结构
interface DifferentRelation {
  head: string
  tail: string
  label: string
  text: string
  users: string[]
  status: string
  metaRelations?: MetaRelation[] // 添加metaRelations字段
  note?: string // 添加note字段
}

// 接口定义：向服务器发送的数据结构
interface RelationDataToSave {
  head: string
  tail: string
  label: string
  text: string
  status: string // 'accept' | 'reject' | 'undecided'
  users: string[]
  metaRelations?: MetaRelation[]
  note?: string // 添加note字段
}

// 接口定义：服务器返回的curation数据结构
interface CurationData {
  same_relations: SameRelation[]
  different_relations: DifferentRelation[]
}

export default defineComponent({
  name: 'CurationWorkPage',

  setup() {
    const router = useRouter();
    const route = useRoute()
    const $q = useQuasar()
    
    // 获取当前用户名
    const username = ref('')
    
    // 从localStorage中获取用户信息
    const updateCurrentUser = () => {
      const userStr = localStorage.getItem('currentUser')
      if (userStr) {
        const currentUser = JSON.parse(userStr)
        username.value = currentUser.username
      }
    }
    
    // 初始化时获取用户信息
    updateCurrentUser()
    
    // 响应式状态变量
    const pmid = ref(route.query.pmid as string || '')
    const title = ref('')
    const abstract = ref('')
    const isLoading = ref(true)
    const tableData = ref<TableRow[]>([])
    const editingRow = ref<TableRow | null>(null)
    
    // 批量操作相关状态
    const isBatchMode = ref(false)
    const selectedRows = ref<number[]>([])
    
    // Curation模式状态
    const isCurationMode = ref(false)
    
    // 跟踪是否有未保存的更改
    const hasChanges = ref(false)
    
    // 当前显示的区域（区域一或区域二）- 默认显示区域一（Same Relations）
    const currentArea = ref('area1')
    
    // 区域切换动画状态
    const isAreaSwitching = ref(false)

    // Add ref for abstract container
    const abstractText = ref<HTMLElement | null>(null)

    // 表格列定义
    const columns: QTableColumn[] = [
      {
        name: 'expand',
        label: '',
        field: row => row.id,
        align: 'center' as const,
        style: 'width: 50px',
      },
      {
        name: 'users',
        label: '',
        field: 'users',
        align: 'left' as const,
      },
      {
        name: 'head',
        label: 'Head Entity',
        field: 'head',
        align: 'center' as const,
      },
      {
        name: 'label',
        label: 'Relation',
        field: 'label',
        align: 'center' as const,
      },
      {
        name: 'tail',
        label: 'Tail Entity',
        field: 'tail',
        align: 'center' as const,
      },
      {
        name: 'actions',
        label: 'Actions',
        field: 'actions',
        align: 'center' as const,
      }
    ]
    
    // 带选择框的表格列定义
    const columnsWithSelection = computed(() => {
      return [
        {
          name: 'selection',
          label: '',
          field: '_selected',
          align: 'left' as const,
        },
        // 在批量模式下需要将users列单独处理，放在selection列后面
        {
          name: 'users',
          label: '',
          field: 'users',
          align: 'left' as const,
        },
        // 过滤掉users列，因为已经单独添加了
        ...columns.filter(col => col.name !== 'users')
      ]
    })
    
    // 计算属性：区域一的关系（same relations）
    const area1Relations = computed(() => {
      // 过滤出same relations
      return tableData.value
        .filter(row => row.id <= 10000) // 使用ID范围区分same relations
        .map(row => ({
          ...row,
          _selected: selectedRows.value.includes(row.id)
        }));
    })
    
    // 计算属性：区域二的关系（different relations）
    const area2Relations = computed(() => {
      // 过滤出different relations
      return tableData.value
        .filter(row => row.id > 10000) // 使用ID范围区分different relations
        .map(row => ({
          ...row,
          _selected: selectedRows.value.includes(row.id)
        }));
    })
    
    // 切换批量操作模式
    const toggleBatchMode = () => {
      isBatchMode.value = !isBatchMode.value;
      
      // 退出批量操作模式时清空选择
      if (!isBatchMode.value) {
        selectedRows.value = [];
      }
    }
    
    // 退出批量操作模式
    const exitBatchMode = () => {
      isBatchMode.value = false;
      selectedRows.value = [];
    }
    
    // 选中当前区域所有行
    const selectAllRows = () => {
      // 使用计算属性获取当前区域的行
      const currentRows = currentArea.value === 'area1' ? 
        area1Relations.value : 
        area2Relations.value;
      
      // 如果当前区域的所有行都已选中，则取消选择，否则全选
      const allSelected = currentRows.every(row => selectedRows.value.includes(row.id));
      
      if (allSelected) {
        // 取消当前区域的所有选择
        selectedRows.value = selectedRows.value.filter(id => 
          !currentRows.some(row => row.id === id)
        );
      } else {
        // 添加当前区域未选中的行
        currentRows.forEach(row => {
          if (!selectedRows.value.includes(row.id)) {
            selectedRows.value.push(row.id);
          }
        });
      }
    }
    
    // 切换行选择状态
    const toggleRowSelection = (row: TableRow) => {
      const index = selectedRows.value.indexOf(row.id);
      if (index === -1) {
        selectedRows.value.push(row.id);
      } else {
        selectedRows.value.splice(index, 1);
      }
    }
    
    // 批量接受选中的行
    const batchAccept = () => {
      if (selectedRows.value.length === 0) {
        $q.notify({
          type: 'warning',
          message: '<span style="font-size: 16px">Please select rows to accept</span>',
          position: 'top',
          html: true,
          timeout: 2000
        })
        return
      }
      
      tableData.value.forEach(row => {
        if (selectedRows.value.includes(row.id)) {
          row.status = 'accepted';
          hasChanges.value = true; // 标记数据已修改
        }
      });
      
      $q.notify({
        type: 'positive',
        message: `<span style="font-size: 16px">Batch accepted ${selectedRows.value.length} rows</span>`,
        position: 'top',
        html: true,
        timeout: 2000
      })
    }
    
    // 批量拒绝选中的行
    const batchReject = () => {
      if (selectedRows.value.length === 0) {
        $q.notify({
          type: 'warning',
          message: '<span style="font-size: 16px">Please select rows to reject</span>',
          position: 'top',
          html: true,
          timeout: 2000
        })
        return
      }
      
      tableData.value.forEach(row => {
        if (selectedRows.value.includes(row.id)) {
          row.status = 'rejected';
          hasChanges.value = true; // 标记数据已修改
        }
      });
      
      $q.notify({
        type: 'negative',
        message: `<span style="font-size: 16px">Batch rejected ${selectedRows.value.length} rows</span>`,
        position: 'top',
        html: true,
        timeout: 2000
      })
    }
    
    // 批量重置选中的行状态
    const batchReset = () => {
      if (selectedRows.value.length === 0) {
        $q.notify({
          type: 'warning',
          message: '<span style="font-size: 16px">Please select rows to reset</span>',
          position: 'top',
          html: true,
          timeout: 2000
        })
        return
      }
      
      tableData.value.forEach(row => {
        if (selectedRows.value.includes(row.id)) {
          row.status = null;
          hasChanges.value = true; // 标记数据已修改
        }
      });
      
      $q.notify({
        type: 'info',
        message: `<span style="font-size: 16px">Batch reset ${selectedRows.value.length} rows</span>`,
        position: 'top',
        html: true,
        timeout: 2000
      })
    }
    
    // 计算属性：是否有行正在编辑中
    const hasEditingRow = computed(() => {
      return tableData.value.some(row => row.status === 'editing');
    })

    // 判断行是否是当前正在编辑的行
    const isCurrentEditingRow = (row: TableRow) => {
      return row.status === 'editing';
    }

    // 接受一行
    const acceptRow = (row: TableRow) => {
      // 找到原始tableData中的对应行并直接修改它
      const originalRow = tableData.value.find(r => r.id === row.id);
      if (originalRow) {
        originalRow.status = 'accepted';
      }
    }
    
    // 拒绝一行
    const rejectRow = (row: TableRow) => {
      // 找到原始tableData中的对应行并直接修改它
      const originalRow = tableData.value.find(r => r.id === row.id);
      if (originalRow) {
        originalRow.status = 'rejected';
      }
    }
    
    // 重置一行状态
    const resetRowStatus = (row: TableRow) => {
      // 找到原始tableData中的对应行并直接修改它
      const originalRow = tableData.value.find(r => r.id === row.id);
      if (originalRow) {
        originalRow.status = null;
      }
    }
    
    // 编辑一行
    const editRow = (row: TableRow) => {
      const originalRow = tableData.value.find(r => r.id === row.id)
      if (originalRow) {
        // 保存原始值
        originalRow.originalHead = originalRow.head
        originalRow.originalLabel = originalRow.label
        originalRow.originalTail = originalRow.tail
        // 保存原始text，处理undefined情况
        originalRow.originalText = originalRow.text || ''
        // 保存原始note，处理undefined情况
        originalRow.originalNote = originalRow.note || ''
        // 保存原始metaRelations，处理undefined情况
        originalRow.originalMetaRelations = originalRow.metaRelations ? JSON.parse(JSON.stringify(originalRow.metaRelations)) : []
        
        // 保存原始状态
        if (originalRow.status === 'accepted' || originalRow.status === 'rejected' || originalRow.status === null) {
          originalRow.originalStatus = originalRow.status
        } else {
          originalRow.originalStatus = null
        }
        
        // 设置编辑状态
        originalRow.status = 'editing'
        editingRow.value = originalRow
        
        // 确保该行处于展开状态
        if (!expandedRows.value.includes(originalRow.id)) {
          expandedRows.value.push(originalRow.id)
          
          // 展开后滚动到可见位置
          nextTick(() => {
            const expandedRow = document.querySelector(`[data-row-id="${originalRow.id}"]`) as HTMLElement
            if (expandedRow) {
              expandedRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
          });
        }
      }
    }
    
    // 保存编辑
    const saveEdit = (row: TableRow) => {
      const originalRow = tableData.value.find(r => r.id === row.id)
      if (originalRow) {
        // 同步编辑的值回原始数据
        originalRow.head = row.head
        originalRow.label = row.label
        originalRow.tail = row.tail
        // 同步text，处理undefined情况
        originalRow.text = row.text || ''
        // 同步note，处理undefined情况
        originalRow.note = row.note || ''
        
        // 标记数据已修改
        hasChanges.value = true
        
        // 恢复原始状态
        if (originalRow.originalStatus !== undefined) {
          originalRow.status = originalRow.originalStatus
        } else {
          originalRow.status = null
        }
        
        editingRow.value = null

        // 如果批量操作模式是开启的，则关闭它
        if (isBatchMode.value) {
          exitBatchMode()
        }
      }
    }
    
    // 取消编辑
    const cancelEdit = (row: TableRow) => {
      // 找到原始tableData中的对应行
      const originalRow = tableData.value.find(r => r.id === row.id);
      if (originalRow) {
        // 恢复原始值
        originalRow.head = originalRow.originalHead || ''
        originalRow.label = originalRow.originalLabel || ''
        originalRow.tail = originalRow.originalTail || ''
        originalRow.text = originalRow.originalText || '' // 恢复原始text
        originalRow.note = originalRow.originalNote || '' // 恢复原始note
        // 恢复原始metaRelations
        originalRow.metaRelations = originalRow.originalMetaRelations ? JSON.parse(JSON.stringify(originalRow.originalMetaRelations)) : []
        
        // 恢复原始状态
        if (originalRow.originalStatus !== undefined) {
          originalRow.status = originalRow.originalStatus
        } else {
          originalRow.status = null
        }
        
        editingRow.value = null

        // 如果批量操作模式是开启的，则关闭它
        if (isBatchMode.value) {
          exitBatchMode()
        }
      }
    }

    // 获取论文数据和curation数据
    const fetchPaperData = async () => {
      if (!pmid.value) {
        isLoading.value = false;
        return;
      }
      
      try {
        isLoading.value = true;
        
        // 直接使用环境变量中的API URL
        const apiHost = `${BACKEND_URL}`;
        
        // 获取论文详情数据
        const paperApiUrl = `${apiHost}/api/curation-paper-detail?pmid=${pmid.value}`;
        console.log(`获取论文详情，API URL: ${paperApiUrl}`);
        const paperResponse = await axios.get(paperApiUrl);
        
        if (paperResponse.data) {
          title.value = paperResponse.data.title || '';
          abstract.value = paperResponse.data.abstract || '';
          console.log(`加载论文详情成功，PMID: ${pmid.value}`);
        } else {
          console.error('获取论文详情返回空数据');
          title.value = '';
          abstract.value = '';
        }
        
        // 获取curation数据
        const curationApiUrl = `${apiHost}/api/curation-data?pmid=${pmid.value}`;
        console.log(`获取curation数据，API URL: ${curationApiUrl}`);
        const curationResponse = await axios.get(curationApiUrl);
        
        if (curationResponse.data) {
          // 处理curation数据
          processCurationData(curationResponse.data);
        } else {
          console.error('获取curation数据返回空数据');
          // 清空表格数据
          tableData.value = [];
        }
        
      } catch (error) {
        console.error('获取数据失败:', error);
        title.value = '';
        abstract.value = '';
        tableData.value = [];
      } finally {
        isLoading.value = false;
      }
    }
    
    // 处理从服务器获取的curation数据
    const processCurationData = (data: CurationData) => {
      tableData.value = []
      
      // 处理same_relations
      data.same_relations.forEach((relation, index) => {
        const frontendStatus = relation.status === 'accept' ? 'accepted' : 
                              relation.status === 'reject' ? 'rejected' : null
        
        const rowData: TableRow = {
          id: index + 1,
          head: relation.head,
          label: relation.label,
          tail: relation.tail,
          text: relation.text,
          status: frontendStatus,
          users: relation.users || [],
          metaRelations: relation.metaRelations || [],
          note: relation.note || ''
        }
        
        tableData.value.push(rowData)
      })
      
      // 处理different_relations
      data.different_relations.forEach((relation, index) => {
        const frontendStatus = relation.status === 'accept' ? 'accepted' : 
                              relation.status === 'reject' ? 'rejected' : null
        
        const rowData: TableRow = {
          id: index + 10001,
          head: relation.head,
          label: relation.label,
          tail: relation.tail,
          text: relation.text,
          status: frontendStatus,
          users: relation.users || [],
          metaRelations: relation.metaRelations || [],
          note: relation.note || ''
        }
        
        tableData.value.push(rowData)
      })
    }

    // 切换区域的方法（支持循环）
    const switchArea = (direction: 'next' | 'prev') => {
      if (direction === 'next') {
        currentArea.value = currentArea.value === 'area1' ? 'area2' : 'area1';
      } else {
        currentArea.value = currentArea.value === 'area1' ? 'area2' : 'area1';
      }
      
      // 如果在批量操作模式，切换区域时清空选择
      if (isBatchMode.value) {
        selectedRows.value = [];
      }
      
      // 显示切换动画
      isAreaSwitching.value = true;
      setTimeout(() => {
        isAreaSwitching.value = false;
      }, 300);
    }

    // 计算属性：当前区域的全选按钮文本
    const selectAllButtonLabel = computed(() => {
      // 使用与selectAllRows相同的逻辑获取当前区域的行
      const currentRows = currentArea.value === 'area1' ? 
        area1Relations.value : 
        area2Relations.value;
      
      // 检查当前区域是否所有行都已选中
      const allSelected = currentRows.length > 0 && currentRows.every(row => selectedRows.value.includes(row.id));
      
      return allSelected ? 'UNSELECT ALL' : 'SELECT ALL';
    });

    // 计算属性：已解决的行数和百分比（所有区域）
    const resolvedCount = computed(() => {
      // 统计所有区域的已解决行数
      return tableData.value.filter(row => 
        row.status === 'accepted' || row.status === 'rejected'
      ).length;
    });

    // 计算属性：总行数（所有区域）
    const totalCount = computed(() => {
      return tableData.value.length;
    });

    // 计算属性：已解决的百分比
    const resolvedPercentage = computed(() => {
      if (totalCount.value === 0) return 0;
      return Math.round((resolvedCount.value / totalCount.value) * 100);
    });

    // 添加用于跟踪hover和点击状态的变量
    const hoveredRowId = ref<number | null>(null);
    const clickedRowId = ref<number | null>(null);
    
    // 处理高亮摘要文本的方法
    const processedAbstract = computed(() => {
      if (!abstract.value) return '';
      
      // 返回原始摘要，高亮由highlightText方法动态处理
      return abstract.value;
    });
    
    // 修改新增：保存原始摘要文本，避免高亮清除问题
    const originalAbstract = ref('');
    
    // 点击页面空白处清除高亮
    const handleDocumentClick = (event: MouseEvent) => {
      // 检查点击是否在表格行内
      const isTableRowClick = (event.target as HTMLElement).closest('tr') !== null;
      
      if (!isTableRowClick) {
        clearHighlight('click');
      }
    };
    
    // 监听document点击事件
    onMounted(() => {
      fetchPaperData();
      // 确保初始化时显示区域一（Same Relations）
      currentArea.value = 'area1';
      
      // 更新当前用户信息
      updateCurrentUser();
      
      // 添加全局点击事件监听器
      document.addEventListener('click', handleDocumentClick);
    });
    
    // 组件卸载时移除事件监听
    onUnmounted(() => {
      // 移除事件监听
      document.removeEventListener('click', handleDocumentClick);
    });
    
    // 跟踪当前高亮的文本内容和位置
    const currentHoverText = ref('');
    const currentClickText = ref('');
    
    // 高亮文本的方法
    const highlightText = (row: TableRow, action: 'hover' | 'click', event?: MouseEvent) => {
      if (!row.text || !abstractText.value) return;
      
      // 阻止事件冒泡
      if (action === 'click') {
        event?.stopPropagation();
      }
      
      // 更新状态变量
      if (action === 'hover') {
        hoveredRowId.value = row.id;
        currentHoverText.value = row.text;
        
        // hover逻辑 - 单独处理，不影响点击高亮
        nextTick(() => {
          const textToHighlight = row.text;
          if (!textToHighlight) return;
          
          const abstractElement = abstractText.value;
          if (!abstractElement) return;
          
          // 保存原始文本（如果尚未保存）
          if (!originalAbstract.value) {
            originalAbstract.value = abstract.value;
          }
          
          // 先清除之前的hover高亮，保留click高亮
          clearHoverHighlights();
          
          // 添加hover高亮
          highlightTextInElement(abstractElement, textToHighlight, 'hover');
        });
      } else if (action === 'click') {
        // 点击逻辑 - 如果点击同一行两次，则清除高亮
        if (clickedRowId.value === row.id) {
          clickedRowId.value = null;
          currentClickText.value = '';
          // 清除点击高亮
          clearClickHighlights();
          return;
        } else {
          // 切换到新的点击行
          clickedRowId.value = row.id;
          currentClickText.value = row.text;
          
          // 执行点击高亮
          nextTick(() => {
            const textToHighlight = row.text;
            if (!textToHighlight) return;
            
            const abstractElement = abstractText.value;
            if (!abstractElement) return;
            
            // 保存原始文本（如果尚未保存）
            if (!originalAbstract.value) {
              originalAbstract.value = abstract.value;
            }
            
            // 先清除之前的所有点击高亮
            clearClickHighlights();
            
            // 添加点击高亮
            highlightTextInElement(abstractElement, textToHighlight, 'click');
          });
        }
      }
    };
    
    // 清除特定类型的高亮
    const clearHighlight = (type: 'hover' | 'click') => {
      if (type === 'hover') {
        hoveredRowId.value = null;
        currentHoverText.value = '';
        clearHoverHighlights();
      } else if (type === 'click') {
        clickedRowId.value = null;
        currentClickText.value = '';
        clearClickHighlights();
      }
      
      // 如果两者都为空，重置为原始文本
      if (!currentHoverText.value && !currentClickText.value && abstractText.value) {
        // 如果有保存的原始文本，恢复
        if (originalAbstract.value) {
          abstractText.value.innerHTML = originalAbstract.value;
        }
      }
    };
    
    // 完全重写的高亮函数 - 直接处理文本，不递归处理DOM节点
    const highlightTextInElement = (element: HTMLElement, text: string, action: 'hover' | 'click') => {
      if (!element || !text) return;
      
      const highlightClass = action === 'hover' ? 'highlight-hover' : 'highlight-click';
      
      // 获取当前HTML内容，包括任何现有的高亮
      const currentHtml = element.innerHTML;
      
      // 创建一个临时DOM元素来操作HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = currentHtml;
      
      // 获取纯文本内容
      const textContent = tempDiv.textContent || '';
      
      // 查找文本在纯文本中的所有出现位置
      const textPositions: number[] = [];
      let startIndex = 0;
      let position;
      
      while ((position = textContent.indexOf(text, startIndex)) !== -1) {
        textPositions.push(position);
        startIndex = position + 1; // 使用+1而不是+text.length以找到所有重叠的实例
      }
      
      // 如果没有找到匹配项，返回
      if (textPositions.length === 0) return;
      
      // 遍历每个找到的位置，对文本进行高亮
      textPositions.forEach(pos => {
        // 创建DOM树遍历器
        const walker = document.createTreeWalker(
          tempDiv,
          NodeFilter.SHOW_TEXT,
          null
        );
        
        let node = walker.nextNode();
        let currentPos = 0;
        let startNode = null;
        let startOffset = 0;
        
        // 遍历文本节点，找到包含目标文本开始位置的节点
        while (node) {
          const nodeLength = (node.textContent || '').length;
          
          // 检查此节点是否包含匹配文本的开始
          if (currentPos <= pos && pos < currentPos + nodeLength) {
            startNode = node;
            startOffset = pos - currentPos;
            break;
          }
          
          currentPos += nodeLength;
          node = walker.nextNode();
        }
        
        // 如果找到了包含文本开始的节点
        if (startNode) {
          // 获取匹配文本结束的位置信息
          let endNode = startNode;
          let endOffset = startOffset + text.length;
          
          // 如果结束位置超出了起始节点的长度，需要找到跨越的其他节点
          if (endOffset > (startNode.textContent || '').length) {
            let remainingLength = text.length;
            let currentNode = startNode;
            
            // 减去已经在起始节点中匹配的部分
            remainingLength -= (currentNode.textContent || '').length - startOffset;
            
            // 继续遍历后续节点，直到找到包含文本结束的节点
            node = walker.nextNode();
            while (node && remainingLength > 0) {
              currentNode = node;
              const nodeLength = (node.textContent || '').length;
              
              if (remainingLength <= nodeLength) {
                // 找到了包含结束位置的节点
                endNode = node;
                endOffset = remainingLength;
                break;
              }
              
              remainingLength -= nodeLength;
              node = walker.nextNode();
            }
          }
          
          // 现在我们有了起始和结束节点/偏移量，创建范围
          const range = document.createRange();
          range.setStart(startNode, startOffset);
          range.setEnd(endNode, endOffset);
          
          // 获取范围内容，并用高亮元素替换
          const fragment = range.extractContents();
          const span = document.createElement('span');
          span.className = highlightClass;
          span.appendChild(fragment);
          range.insertNode(span);
        }
      });
      
      // 更新原始元素的内容
      element.innerHTML = tempDiv.innerHTML;
    };
    
    // 清除hover高亮元素
    const clearHoverHighlights = () => {
      if (!abstractText.value || !currentHoverText.value) return;
      
      if (currentClickText.value) {
        // 如果有点击高亮，需要保留这些高亮
        // 获取当前HTML
        const currentHtml = abstractText.value.innerHTML;
        
        // 创建临时元素
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = currentHtml;
        
        // 移除所有具有hover高亮类的元素（但保留其内容）
        const hoverElements = tempDiv.querySelectorAll('.highlight-hover:not(.highlight-click)');
        hoverElements.forEach(el => {
          const parent = el.parentNode;
          if (parent) {
            while (el.firstChild) {
              parent.insertBefore(el.firstChild, el);
            }
            parent.removeChild(el);
          }
        });
        
        // 对于同时具有hover和click类的元素，只移除hover类
        const combinedElements = tempDiv.querySelectorAll('.highlight-hover.highlight-click');
        combinedElements.forEach(el => {
          el.classList.remove('highlight-hover');
        });
        
        // 更新DOM
        abstractText.value.innerHTML = tempDiv.innerHTML;
      } else {
        // 没有点击高亮，恢复到原始文本
        if (originalAbstract.value && abstractText.value) {
          abstractText.value.innerHTML = originalAbstract.value;
        }
      }
    };
    
    // 清除点击高亮元素
    const clearClickHighlights = () => {
      if (!abstractText.value || !currentClickText.value) return;
      
      if (currentHoverText.value) {
        // 如果有hover高亮，需要保留这些高亮
        // 获取当前HTML
        const currentHtml = abstractText.value.innerHTML;
        
        // 创建临时元素
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = currentHtml;
        
        // 移除所有具有click高亮类的元素（但保留其内容）
        const clickElements = tempDiv.querySelectorAll('.highlight-click:not(.highlight-hover)');
        clickElements.forEach(el => {
          const parent = el.parentNode;
          if (parent) {
            while (el.firstChild) {
              parent.insertBefore(el.firstChild, el);
            }
            parent.removeChild(el);
          }
        });
        
        // 对于同时具有hover和click类的元素，只移除click类
        const combinedElements = tempDiv.querySelectorAll('.highlight-hover.highlight-click');
        combinedElements.forEach(el => {
          el.classList.remove('highlight-click');
        });
        
        // 更新DOM
        abstractText.value.innerHTML = tempDiv.innerHTML;
        
        // 重新应用hover高亮
        if (abstractText.value) {
          highlightTextInElement(abstractText.value, currentHoverText.value, 'hover');
        }
      } else {
        // 没有hover高亮，恢复到原始文本
        if (originalAbstract.value && abstractText.value) {
          abstractText.value.innerHTML = originalAbstract.value;
        }
      }
    };
    
    const startCuration = () => {
      // 进入curation模式
      isCurationMode.value = true;
      console.log('开始数据审核');
      
      // 不显示任何通知
    }
    
    // 取消数据审核
    const cancelCuration = () => {
      // 直接刷新数据，不显示确认对话框
      // 清除编辑状态
      editingRow.value = null
      
      // 关闭批量操作模式
      if (isBatchMode.value) {
        exitBatchMode()
      }
      
      // 重置更改标记
      hasChanges.value = false
      
      // 退出curation模式
      isCurationMode.value = false
      
      // 重新加载原始数据
      fetchPaperData()
      
      $q.notify({
        type: 'info',
        message: '<span style="font-size: 16px">Changes discarded, data refreshed</span>',
        position: 'top',
        html: true,
        timeout: 2000
      })
    }
    
    // 保存数据审核结果
    const saveCuration = async () => {
      try {
        // 立即退出curation模式，提供即时的视觉反馈
        isCurationMode.value = false;
        
        // 清除任何编辑状态
        editingRow.value = null;
        
        // 如果在批量操作模式下，退出批量操作模式
        if (isBatchMode.value) {
          exitBatchMode();
        }
        
        // 显示加载指示器
        isLoading.value = true;
        
        // 准备要发送到服务器的数据
        const dataToSave = {
          same_relations: tableData.value
            .filter(row => row.id <= 10000)
            .map(row => {
              const relationData: RelationDataToSave = {
                head: row.head,
                label: row.label,
                tail: row.tail,
                text: row.text || '',
                status: row.status === 'accepted' ? 'accept' : 
                      row.status === 'rejected' ? 'reject' : 'undecided',
                users: row.users || [],
                note: row.note || ''
              };
              
              // 如果有metaRelations，添加到对象
              if (row.metaRelations) {
                relationData.metaRelations = row.metaRelations
              }
              
              return relationData
            }),
          different_relations: tableData.value
            .filter(row => row.id > 10000)
            .map(row => {
              const relationData: RelationDataToSave = {
                head: row.head,
                label: row.label,
                tail: row.tail,
                text: row.text || '',
                status: row.status === 'accepted' ? 'accept' : 
                      row.status === 'rejected' ? 'reject' : 'undecided',
                users: row.users || [],
                note: row.note || ''
              };
              
              // 如果有metaRelations，添加到对象
              if (row.metaRelations) {
                relationData.metaRelations = row.metaRelations
              }
              
              return relationData
            })
        };
        
        // 直接使用环境变量中的API URL
        const apiUrl = `${BACKEND_URL}/api/save-curation-data`;
        
        // 发送数据到服务器
        const response = await axios.post(apiUrl, {
          pmid: pmid.value,
          data: dataToSave
        });
        
        if (response.data && response.data.success) {
          // 显示英文成功消息
          $q.notify({
            type: 'positive',
            message: '<span style="font-size: 16px">Curation data saved successfully</span>',
            position: 'top',
            html: true,
            timeout: 2000
          });
          
          // 标记为没有未保存的更改
          hasChanges.value = false;
          // 已经在函数开始时设置了isCurationMode = false，这里不再需要
          // isCurationMode.value = false;
          
          // 移除重定向到上一页的逻辑，保持在当前页面
        } else {
          console.error('保存curation数据失败:', response.data);
          $q.notify({
            type: 'negative',
            message: `<span style="font-size: 16px">Save failed: ${response.data.error || 'Unknown error'}</span>`,
            position: 'top',
            html: true,
            timeout: 2000
          });
        }
      } catch (error) {
        console.error('保存curation数据时出错:', error);
        isLoading.value = false;
        
        $q.notify({
          type: 'negative',
          message: `<span style="font-size: 16px">Save error: ${error instanceof Error ? error.message : 'Unknown error'}</span>`,
          position: 'top',
          html: true,
          timeout: 3000
        });
      } finally {
        // 隐藏加载指示器
        isLoading.value = false;
      }
    }

    // 合并功能
    const handleMerge = () => {
      if (resolvedCount.value < totalCount.value) {
        $q.notify({
          type: 'warning',
          message: '<span style="font-size: 16px">All relations must be resolved before merging</span>',
          position: 'top',
          html: true,
          timeout: 2000
        });
        return;
      }
      
      if (isCurationMode.value) {
        $q.notify({
          type: 'warning',
          message: '<span style="font-size: 16px">Please save and verify changes before merging</span>',
          position: 'top',
          html: true,
          timeout: 2000
        });
        return;
      }
      
      $q.dialog({
        title: 'Confirm Merge',
        message: '<span style="font-size: 16px">This will overwrite the existing main version.</span>',
        cancel: true,
        persistent: true,
        html: true
      }).onOk(async () => {
        try {
          isLoading.value = true;
          
          // 直接使用环境变量中的API URL
          const apiUrl = `${BACKEND_URL}/api/merge-curation-data`;
          
          // 发送合并请求
          const response = await axios.post(apiUrl, {
            pmid: pmid.value
          });
          
          if (response.data && response.data.success) {
            $q.notify({
              type: 'positive',
              message: '<span style="font-size: 16px">Data merged successfully</span>',
              position: 'top',
              html: true,
              timeout: 2000
            });
            
            // 返回到关系审核页
            router.push('/relations-curation');
          } else {
            $q.notify({
              type: 'negative',
              message: `<span style="font-size: 16px">Merge failed: ${response.data.error || 'Unknown error'}</span>`,
              position: 'top',
              html: true,
              timeout: 3000
            });
          }
        } catch (error) {
          console.error('合并数据时出错:', error);
          $q.notify({
            type: 'negative',
            message: `<span style="font-size: 16px">Merge error: ${error instanceof Error ? error.message : 'Unknown error'}</span>`,
            position: 'top',
            html: true,
            timeout: 3000
          });
        } finally {
          isLoading.value = false;
        }
      });
    }

    // 获取用户首字母的方法
    const getUserInitials = (username: string) => {
      if (!username) return '';
      return username.charAt(0).toUpperCase();
    }
    
    // 根据用户名获取不同背景色的方法
    const getUserColor = (username: string) => {
      // 预定义的颜色列表 - 扩展到15种颜色以支持更多用户
      const colors = [
        '#1976d2', // 蓝色
        '#e91e63', // 粉色
        '#ff9800', // 橙色
        '#4caf50', // 绿色
        '#9c27b0', // 紫色
        '#d32f2f', // 红色
        '#7b1fa2', // 深紫色
        '#0097a7', // 青色
        '#ffc107', // 琥珀色
        '#607d8b', // 蓝灰色
        '#795548', // 棕色
        '#006064', // 深青色
        '#827717', // 橄榄色
        '#bf360c', // 深橙色
        '#1a237e'  // 靛蓝色
      ];
      
      // 如果没有用户名，返回默认颜色
      if (!username) return colors[0];
      
      // 使用更可靠的哈希算法来为用户名分配一致的颜色
      let hash = 0;
      for (let i = 0; i < username.length; i++) {
        hash = ((hash << 5) - hash) + username.charCodeAt(i);
        hash = hash & hash; // 转换为32位整数
      }
      // 使用绝对值确保是正数，然后对颜色数组长度取模
      return colors[Math.abs(hash) % colors.length];
    }

    // 展开行相关的状态和方法
    const expandedRows = ref<number[]>([])

    const isExpandable = (row: TableRow) => {
      if (!row) return false
      return true // 所有行都可以展开，因为都有text和可能的metaRelations
    }

    const toggleExpand = (row: TableRow) => {
      const index = expandedRows.value.indexOf(row.id)
      if (index === -1) {
        expandedRows.value.push(row.id)
        
        // 在展开行后，让视图滚动到展开区域的位置
        nextTick(() => {
          const expandedRow = document.querySelector(`[data-row-id="${row.id}"]`) as HTMLElement
          if (expandedRow) {
            expandedRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        });
      } else {
        expandedRows.value.splice(index, 1)
      }
    }

    const isExpanded = (row: TableRow) => {
      return expandedRows.value.includes(row.id)
    }

    // Meta Relations相关方法
    const addMetaRelation = (row: TableRow) => {
      if (!row.metaRelations) {
        row.metaRelations = []
      }
      row.metaRelations.push({
        target: '',
        label: ''
      })
    }

    const removeMetaRelation = (row: TableRow, index: number) => {
      if (row.metaRelations) {
        row.metaRelations.splice(index, 1)
      }
    }

    // 当Supporting Text失去焦点时更新显示
    const updateTextPreview = (row: TableRow) => {
      // 找到原表格数据中对应的行
      const originalRow = tableData.value.find(r => r.id === row.id)
      if (originalRow) {
        // 更新text字段
        originalRow.text = row.text || ''
        // 标记有未保存的更改
        hasChanges.value = true
      }
    }

    // 添加updateFieldPreview方法
    const updateFieldPreview = (row: TableRow, fieldName: 'head' | 'label' | 'tail') => {
      // 找到原表格数据中对应的行
      const originalRow = tableData.value.find(r => r.id === row.id)
      if (originalRow) {
        // 更新对应字段
        originalRow[fieldName] = row[fieldName] || ''
        // 标记有未保存的更改
        hasChanges.value = true
      }
    }

    // 当Note失去焦点时更新显示
    const updateNotePreview = (row: TableRow) => {
      // 找到原表格数据中对应的行
      const originalRow = tableData.value.find(r => r.id === row.id)
      if (originalRow) {
        // 更新note字段
        originalRow.note = row.note || ''
        // 标记有未保存的更改
        hasChanges.value = true
      }
    }

    // 解析笔记内容，将其拆分为用户和内容
    const parseNotes = (note: string | undefined) => {
      if (!note) return [];
      
      const result = [];
      // 尝试将整个note按照"user1\n内容1\n\nuser2\n内容2"的格式分割
      const userBlocks = note.split('\n\n');
      
      for (const block of userBlocks) {
        // 查找第一个换行符位置
        const newlineIndex = block.indexOf('\n');
        if (newlineIndex !== -1) {
          const user = block.substring(0, newlineIndex);
          const content = block.substring(newlineIndex + 1);
          result.push({ user, content });
        } else {
          // 如果没有找到换行符，整个内容作为匿名用户的笔记
          result.push({ user: 'Anonymous', content: block });
        }
      }
      
      return result;
    };

    // 添加方法来更新特定用户的笔记内容
    const updateNoteContent = (row: TableRow, user: string, content: string) => {
      // 找到原始行
      const originalRow = tableData.value.find(r => r.id === row.id);
      if (!originalRow) return;

      // 解析当前的note内容
      const notes = parseNotes(originalRow.note);
      
      // 更新特定用户的笔记内容
      for (const note of notes) {
        if (note.user === user) {
          note.content = content;
          break;
        }
      }
      
      // 重新构建note字符串
      let newNote = '';
      for (let i = 0; i < notes.length; i++) {
        if (i > 0) newNote += '\n\n';
        // 添加类型安全检查和默认值
        const noteUser = notes[i]?.user || 'Anonymous';
        const noteContent = notes[i]?.content || '';
        newNote += noteUser + '\n' + noteContent;
      }
      
      // 更新到原始行
      originalRow.note = newNote;
      
      // 标记有未保存的更改
      hasChanges.value = true;
    };

    // 添加删除特定用户笔记的函数
    const deleteNoteContent = (row: TableRow, userToDelete: string) => {
      // 找到原始行
      const originalRow = tableData.value.find(r => r.id === row.id);
      if (!originalRow) return;
      
      // 解析当前的note内容
      const notes = parseNotes(originalRow.note);
      
      // 过滤掉要删除用户的笔记
      const filteredNotes = notes.filter(note => note.user !== userToDelete);
      
      // 如果没有剩余笔记，则设置为空
      if (filteredNotes.length === 0) {
        originalRow.note = '';
      } else {
        // 重新构建note字符串
        let newNote = '';
        for (let i = 0; i < filteredNotes.length; i++) {
          if (i > 0) newNote += '\n\n';
          const noteUser = filteredNotes[i]?.user || 'Anonymous';
          const noteContent = filteredNotes[i]?.content || '';
          newNote += noteUser + '\n' + noteContent;
        }
        
        // 更新到原始行
        originalRow.note = newNote;
      }
      
      // 标记有未保存的更改
      hasChanges.value = true;
    };

    // 添加笔记相关变量
    const addNoteDialogVisible = ref(false)
    const newNoteUser = ref('Admin')
    const newNoteContent = ref('')
    const currentEditingRow = ref<TableRow | null>(null)

    // 显示添加笔记对话框
    const showAddNoteDialog = (row: TableRow) => {
      currentEditingRow.value = row;
      newNoteUser.value = 'Admin'; // 默认用户名
      newNoteContent.value = ''; // 清空内容
      addNoteDialogVisible.value = true;
    };

    // 添加新笔记
    const addNewNote = () => {
      if (!currentEditingRow.value || !newNoteUser.value || !newNoteContent.value) return;
      
      // 找到原始行
      const originalRow = tableData.value.find(r => r.id === currentEditingRow.value?.id);
      if (!originalRow) return;
      
      // 解析当前的note内容
      const notes = parseNotes(originalRow.note);
      
      // 添加新笔记
      notes.push({
        user: newNoteUser.value,
        content: newNoteContent.value
      });
      
      // 重新构建note字符串
      let newNote = '';
      for (let i = 0; i < notes.length; i++) {
        if (i > 0) newNote += '\n\n';
        const noteUser = notes[i]?.user || 'Anonymous';
        const noteContent = notes[i]?.content || '';
        newNote += noteUser + '\n' + noteContent;
      }
      
      // 更新到原始行
      originalRow.note = newNote;
      
      // 清空新笔记表单
      newNoteUser.value = 'Admin';
      newNoteContent.value = '';
      
      // 重置当前编辑行引用
      currentEditingRow.value = null;
      
      // 标记有未保存的更改
      hasChanges.value = true;
    };

    return {
      pmid,
      title,
      abstract,
      isLoading,
      tableData,
      columns,
      columnsWithSelection,
      abstractText,
      currentArea,
      area1Relations,
      area2Relations,
      switchArea,
      acceptRow,
      rejectRow,
      resetRowStatus,
      editRow,
      saveEdit,
      cancelEdit,
      editingRow,
      hasEditingRow,
      isCurrentEditingRow,
      getUserInitials,
      getUserColor,
      // 批量操作相关
      isBatchMode,
      selectedRows,
      toggleBatchMode,
      selectAllRows,
      selectAllButtonLabel,
      toggleRowSelection,
      batchAccept,
      batchReject,
      batchReset,
      exitBatchMode,
      // 统计相关
      resolvedCount,
      totalCount,
      resolvedPercentage,
      // Curation相关
      isCurationMode,
      startCuration,
      cancelCuration,
      saveCuration,
      // 区域切换相关
      isAreaSwitching,
      // 合并功能
      handleMerge,
      hoveredRowId,
      clickedRowId,
      highlightText,
      clearHighlight,
      processedAbstract,
      expandedRows,
      isExpandable,
      toggleExpand,
      isExpanded,
      // Meta Relations相关
      addMetaRelation,
      removeMetaRelation,
      // 实时预览更新
      updateTextPreview,
      updateNotePreview,
      updateFieldPreview,
      parseNotes,
      updateNoteContent,
      deleteNoteContent,
      username,
      // 添加新的变量和函数
      addNoteDialogVisible,
      newNoteUser,
      newNoteContent,
      showAddNoteDialog,
      addNewNote,
    }
  },
})
</script>

<style lang="scss" scoped>
.back-btn {
  font-size: 18px;
}

.custom-tooltip {
  font-size: 16px !important;
  white-space: nowrap !important; /* 确保文本在一行显示 */
  min-width: max-content !important; /* 确保气泡宽度足够显示内容 */
}

/* 内容容器样式 */
.content-container {
  display: flex;
  flex-direction: column;
  padding-top: 5px; /* 增加顶部间距 */
}

/* Abstract 标题样式 (绿色框) */
.abstract-header {
  background-color: #f5f7fa;
  padding: 12px 0;
  margin: 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-bottom: none;
  border-radius: 4px 4px 0 0;
  font-weight: 500;
}

/* 固定内容区域 (红色框) */
.sticky-content {
  position: sticky;
  top: 40px; /* 调整到40px，下移5px */
  z-index: 10;
  margin-bottom: 16px;
}

.abstract-container {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 0 0 4px 4px;
  margin: 0;
  background-color: white;
  transition: box-shadow 0.3s ease, transform 0.2s ease;
  padding: 0;
}

.abstract-container:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.relations-section {
  margin-top: 24px;
}

.relations-header {
  background-color: #f5f7fa;
  padding: 12px 0;
  margin: 0 0 8px 0;
  border-radius: 4px 4px 0 0;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-bottom: none;
  font-weight: 500;
  text-align: center;
  position: relative;
}

.relations-container {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 0 0 4px 4px;
  overflow: hidden;
}

.abstract {
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 0;
}

.header-section {
  background-color: #f5f5f5;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  position: relative;
  min-height: 70px;
  padding: 0;
}

.header-container {
  position: relative;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-button {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}

.left-nav {
  left: 16px;
}

.right-nav {
  right: 16px;
}

.batch-btn-container {
  position: absolute;
  left: 425px; /* 调整位置，使按钮更加居中于左侧导航按钮和标题之间 */
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
}

.batch-actions-row {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
  padding: 0;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 3;
}

.area-title-container {
  position: absolute;
  left: 0;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  text-align: center;
  z-index: 1;
  pointer-events: none; /* 让标题可点击穿透 */
}

.area-title {
  font-size: 24px;
  font-weight: 500;
  display: inline-block;
  pointer-events: auto; /* 恢复标题元素的点击 */
}

.navigation-btn {
  width: 45px;
  height: 45px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
  }
}

.analysis-table {
  :deep(.q-table__container) {
    border: none;
  }

  :deep(.q-table) {
    box-shadow: none;
  }

  :deep(.q-table thead tr) {
    background-color: #eeeeee;
    
    th {
      font-size: 16px;
      font-weight: bold;
    }
  }
  
  :deep(.q-table tbody td) {
    padding: 8px 16px;
  }
}

.action-btn {
  margin: 0 2px;
  font-size: 18px;
}

:deep(.q-tooltip) {
  font-size: 16px !important;
  background: rgba(0, 0, 0, 0.8);
  max-width: 300px;
  white-space: normal;
  word-wrap: break-word;
  padding: 8px 12px;
}

/* 专门针对Back按钮的tooltip */
:deep(.back-btn .q-tooltip) {
  font-size: 16px !important;
}

.top-nav {
  position: relative;
  z-index: 20; /* 确保顶部导航栏在最上层 */
}

.edit-input {
  width: 90%;
  min-width: 120px;
  margin: 0 auto;
  
  :deep(.q-field__native) {
    text-align: center;
  }
  
  :deep(.q-field__control) {
    padding: 0 8px;
  }
}

.bg-green-1 {
  background-color: rgba(76, 175, 80, 0.1) !important;
}

.bg-red-1 {
  background-color: rgba(244, 67, 54, 0.1) !important;
}

.dimmed-row {
  opacity: 0.95;
  position: relative;
  transition: opacity 0.3s ease;
}

.dimmed-row::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.05);
  pointer-events: none;
}

.batch-btn {
  margin-left: 16px;
  height: 36px;
  font-weight: 500;
  font-size: 16px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-transform: uppercase;
}

.batch-controls-container {
  position: relative;
  height: 36px;
}

.batch-action-btn {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  font-size: 14px;
  height: 36px;
  width: 36px;
}

.select-all-btn {
  height: 36px;
  padding: 0 12px;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  min-width: auto;
  width: auto !important;
}

.stats-container {
  position: absolute;
  right: 130px; /* 调整位置，使其位于右侧导航按钮之前 */
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  padding: 0 16px;
  display: flex;
  align-items: center;
}

.resolution-stats {
  font-size: 16px;
  font-weight: 500;
  color: white;
  background-color: var(--q-primary);
  height: 41px;
  line-height: 41px;
  padding: 0 16px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.merge-btn {
  height: 36px;
  font-weight: 500;
  font-size: 16px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-left: 72px !important; /* 增加左边距，覆盖q-ml-lg */
}

.merge-tooltip {
  font-size: 16px !important;
}

.start-curation-container {
  position: absolute;
  left: 150px; /* 调整位置，放在左侧导航按钮和批量操作按钮之间 */
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
}

.start-curation-btn {
  height: 45px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  font-weight: bold;
  font-size: 14px;
  border-radius: 4px;
  background-color: #4CAF50 !important; /* 确保按钮是绿色 */
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
    background-color: #45a049 !important; /* 悬停时的深绿色 */
  }
}

.curation-actions-row {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.curation-action-btn {
  height: 40px;
  min-width: 100px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  font-weight: bold;
  font-size: 14px;
  border-radius: 4px;
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.25);
  }
}

.tooltip-16px {
  font-size: 16px !important;
}

/* 表格单元格内容样式 */
.relation-cell-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
}

.text-tooltip {
  font-size: 14px !important;
  max-width: 400px !important;
  text-align: left;
  white-space: normal;
  word-break: normal;
  padding: 8px 12px;
  background-color: rgba(0, 0, 0, 0.8);
}

.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0.6;
  }
  to {
    opacity: 1;
  }
}

/* 高亮样式 */
:deep(.highlight-hover) {
  background-color: #ffe0b2; /* 浅橙色 */
  border-radius: 2px;
  transition: background-color 0.2s ease;
}

:deep(.highlight-click) {
  background-color: #ffb74d; /* 深橙色 */
  border-radius: 2px;
  transition: background-color 0.2s ease;
}

/* 当元素同时具有两种高亮类时的样式 - 优先显示点击高亮，但有一个特殊的边框表示hover状态 */
:deep(.highlight-hover.highlight-click) {
  background-color: #ffb74d; /* 使用点击高亮的颜色 */
  box-shadow: 0 0 0 2px #ffe0b2; /* 添加hover高亮颜色的边框效果 */
  border-radius: 2px;
}

/* 鼠标悬停和点击的行样式 */
.hovered-row {
  background-color: rgba(255, 224, 178, 0.2) !important;
}

.clicked-row {
  background-color: rgba(255, 183, 77, 0.2) !important;
}

/* 用户图标样式 */
.user-circles-container {
  display: flex;
  align-items: center;
  position: relative;
  height: 30px;
  padding-right: 15px; /* 为最后一个圆圈提供足够空间 */
}

.user-circle {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #1976d2; /* 主色调蓝色 */
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  margin-right: -15px; /* 负margin使圆圈重叠 */
  border: 2px solid white; /* 白色边框增加区分度 */
  position: relative;
  z-index: 3;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease;
}

.user-circle:hover {
  transform: translateY(-2px);
  box-shadow: 0 3px 5px rgba(0, 0, 0, 0.3);
}

/* 依次降低z-index，使圆圈从左到右有层叠感 */
.user-circle:nth-child(2) {
  z-index: 2;
}

.user-circle:nth-child(3) {
  z-index: 1;
  margin-right: 0; /* 最后一个圆圈不需要负margin */
}

.users-cell {
  padding-right: 0 !important;
}

.more-users-text {
  font-size: 13px;
  color: #607d8b;
  margin-left: 8px; /* 增加与最后一个圆圈的间距 */
  font-weight: 500;
  display: flex;
  align-items: center;
}

/* 用户列表tooltip样式 */
.users-tooltip {
  font-size: 16px !important;
  background: rgba(0, 0, 0, 0.8);
  padding: 8px 12px;
  white-space: nowrap;
}

/* 展开行样式 */
.meta-relation-row {
  background-color: #f5f7fa;
}

/* 展开内容样式 */
.meta-relations {
  padding: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

/* 区域标题样式 */
.section-title {
  font-size: 16px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 16px;
}

/* 支持文本样式 */
.text-input {
  margin-bottom: 24px;
}

/* 支持文本显示样式 */
.supporting-text-display {
  white-space: pre-wrap;
  font-size: 16px;
  line-height: 1.6;
  background-color: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

/* 笔记输入框样式 */
.note-input {
  :deep(.q-field__control) {
    background-color: white;
    height: 100px !important;
    min-height: 100px !important;
    max-height: 100px !important;
  }
  
  :deep(.q-field__native) {
    resize: none !important;
    height: 80px !important;
    max-height: 80px !important;
    overflow: auto !important;
    overflow-y: scroll !important;
    white-space: pre-wrap;
    word-wrap: break-word;
    word-break: break-word;
    font-size: 16px !important;
    
    textarea {
      height: 100% !important;
      overflow: auto !important;
      overflow-y: visible !important;
      resize: none !important;
    }
    
    /* 自定义滚动条样式 */
    &::-webkit-scrollbar {
      width: 8px;
      display: block !important;
    }
    
    &::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 4px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: #888;
      border-radius: 4px;
      
      &:hover {
        background: #555;
      }
    }
  }
}

/* 笔记显示样式 */
.note-display {
  background-color: white;
  padding: 12px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  min-height: 60px;
  font-size: 16px;
  line-height: 1.6;
  
  pre {
    font-family: inherit;
    margin: 0;
    padding: 0;
    background: none;
    border: none;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 16px;
  }
  
  .note-user-section {
    margin-bottom: 16px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .note-user-name {
    font-weight: bold;
    margin-bottom: 4px;
    color: #1976d2;
    background-color: rgba(25, 118, 210, 0.1);
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
  }
  
  .note-user-content {
    white-space: pre-wrap;
    word-wrap: break-word;
    padding-left: 10px;
    max-height: calc(1.6em * 4); /* 限制为4行文本高度 */
    overflow-y: auto; /* 添加垂直滚动条 */
  }
  
  .empty-note {
    color: #999;
    font-style: italic;
  }
}

/* 展开按钮样式 */
.expand-button {
  margin-right: 16px;
  font-size: 24px !important;
  width: 40px;
  height: 40px;
  
  :deep(.q-icon) {
    font-size: 24px;
  }
}

/* 支持文本输入框样式 */
.supporting-text-input {
  :deep(.q-field__control) {
    height: 120px !important;
    min-height: 120px !important;
    max-height: 120px !important;
  }
  
  :deep(.q-field__native) {
    resize: none !important;
    height: 120px !important;
    max-height: 120px !important;
    overflow: auto !important;
    overflow-y: scroll !important;
    white-space: pre-wrap;
    word-wrap: break-word;
    word-break: break-word;
    font-size: 16px !important;
    
    textarea {
      height: 100% !important;
      overflow: auto !important;
      overflow-y: visible !important;
      resize: none !important;
      font-size: 16px !important;
    }
    
    /* 自定义滚动条样式 */
    &::-webkit-scrollbar {
      width: 8px;
      display: block !important;
    }
    
    &::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 4px;
    }
    
    &::-webkit-scrollbar-thumb {
      background: #888;
      border-radius: 4px;
      
      &:hover {
        background: #555;
      }
    }
  }
}

/* 添加 note 输入框的样式 */
.text-input .q-field textarea {
  resize: none !important;
}

/* Meta Relations输入框样式 */
.meta-input {
  width: calc(100% - 40px); /* 为删除按钮留出空间 */
  margin-right: 8px;
  font-size: 16px; /* 设置输入框字体大小 */
  
  :deep(.q-field__control) {
    background-color: white;
  }
  
  :deep(.q-field__native) {
    font-size: 16px; /* 确保输入框内文字大小一致 */
  }
}

.delete-meta-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  margin-left: auto;
  opacity: 0.7;
  transition: all 0.3s ease;
  
  &:hover {
    opacity: 1;
    transform: scale(1.1);
  }
  
  :deep(.q-icon) {
    font-size: 20px !important;
  }
}

.row.items-center.no-wrap {
  display: flex;
  align-items: center;
  padding-right: 8px;
}

/* Meta Relations表格样式 */
.meta-relations-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid rgba(0, 0, 0, 0.22);
  
  th, td {
    padding: 8px;
    border: 1px solid rgba(0, 0, 0, 0.22);
    width: 50%;
    font-size: 16px;
  }
  
  th {
    background-color: #f5f7fa;
    font-weight: 500;
    font-size: 16px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.22);
  }

  tbody tr:last-child td {
    border-bottom: 1px solid rgba(0, 0, 0, 0.22);
  }
}

/* 编辑模式下的表格样式保持一致 */
.q-markup-table {
  border: 1px solid rgba(0, 0, 0, 0.22) !important;
  
  th, td {
    border: 1px solid rgba(0, 0, 0, 0.22) !important;
    width: 50% !important;
    font-size: 16px !important;
  }
  
  th {
    border-bottom: 1px solid rgba(0, 0, 0, 0.22) !important;
  }
}

/* 添加Meta Relation按钮样式 */
.add-meta-btn {
  width: 40px;
  height: 40px;
  
  :deep(.q-icon) {
    font-size: 24px;
  }
  
  &:hover {
    transform: scale(1.1);
    transition: transform 0.2s ease;
  }
}

/* 添加note-content-input和note-edit-mode的样式 */
.note-content-input {
  margin-top: 8px;
  
  :deep(.q-field__control) {
    min-height: 60px !important;
    max-height: calc(1.6em * 4 + 24px) !important; /* 限制为4行文本高度加上内边距 */
  }
  
  :deep(.q-field__native) {
    resize: none !important;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 16px !important;
    max-height: calc(1.6em * 4) !important; /* 限制为4行文本高度 */
    overflow-y: auto !important; /* 添加垂直滚动条 */
  }
}

.note-edit-mode {
  .note-user-section {
    margin-bottom: 24px;
  }
  
  .note-user-header {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    margin-bottom: 4px;
  }
  
  .delete-note-btn {
    margin-left: 8px;
    opacity: 0.7;
    transition: all 0.2s ease;
    
    &:hover {
      opacity: 1;
      transform: scale(1.1);
    }
  }
  
  .add-note-btn {
    margin: 8px auto;
    opacity: 0.9;
    transition: all 0.3s ease;
    
    &:hover {
      opacity: 1;
      transform: scale(1.1);
    }
  }
}

.delete-note-btn {
  margin-left: 8px;
  opacity: 0.7;
  transition: all 0.2s ease;
  
  &:hover {
    opacity: 1;
    transform: scale(1.1);
  }
}

.add-note-btn {
  margin: 8px auto;
  opacity: 0.9;
  transition: all 0.3s ease;
  
  &:hover {
    opacity: 1;
    transform: scale(1.1);
  }
}

/* 添加笔记对话框样式 */
:deep(.add-note-input) {
  .q-field__label {
    font-size: 16px;
  }
  
  .q-field__native,
  .q-field__input {
    font-size: 18px !important;
    line-height: 1.5;
  }
  
  .q-field__control {
    height: auto;
    min-height: 56px;
  }
  
  &.note-content-input .q-field__control {
    min-height: 200px;
  }
}

:deep(.text-h5) {
  font-size: 24px !important;
  font-weight: 500;
}

:deep(.q-card) {
  border-radius: 8px;
}
</style>