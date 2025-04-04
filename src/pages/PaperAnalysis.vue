/** * 论文分析系统主页面组件 * * 功能说明： * 1. 展示论文内容和分析结果 * 2.
处理用户交互（点击、输入等） * 3. 与后端 API 通信获取数据 * * 数据流向： * 1. 组件初始化时通过
fetchData() 从后端获取数据 * 2. 数据保存在 paperData 响应式变量中 * 3.
通过计算属性将数据处理后显示在界面上 */

<template>
  <q-page class="q-pa-md" style="--tooltip-font-size: 30px">
    <div class="row items-center justify-between q-mb-lg">
      <q-btn
        flat
        round
        color="primary"
        icon="arrow_back"
        class="q-mr-sm back-btn"
        @click="handleBackClick"
        size="md"
      >
        <q-tooltip class="custom-tooltip">{{ backButtonTooltip }}</q-tooltip>
      </q-btn>
      <div class="text-center col">
        <div v-if="pmid" style="font-size: 24px" class="text-primary q-mb-sm">
          PMID: {{ pmid }}
        </div>
        <div v-if="extractionTime" style="font-size: 24px" class="text-primary">
          Extracted Time: {{ extractionTime }}
        </div>
      </div>
    </div>

    <!-- Paper content and analysis area -->
    <div class="row q-mb-md q-col-gutter-md" v-if="!isGraphView">
      <!-- Left: Paper content -->
      <div class="col-6">
        <div class="text-h5 q-mb-md text-center">Abstract</div>
        <q-card class="abstract-container">
          <q-card-section>
            <div v-if="isLoading" class="text-center">
              <q-spinner-dots size="40px" />
              <div class="text-subtitle1 q-mt-md">Fetching paper data...</div>
            </div>
            <div v-else-if="!title && !abstract" class="text-center text-grey-7">
              No data available
            </div>
            <template v-else>
              <!-- Title -->
              <div class="text-h5 q-mb-lg">
                {{ title }}
              </div>
              <!-- Abstract -->
              <div
                class="text-body1 q-mb-md abstract"
                ref="abstractText"
                v-html="highlightedAbstract"
              ></div>
            </template>
          </q-card-section>
        </q-card>
      </div>

      <!-- Right: Analysis results -->
      <div class="col-6">
        <div class="text-h5 q-mb-md text-center row items-start justify-between">
          <div class="col-3 text-left" :style="isEditing ? 'display: flex; align-items: center;' : 'display: flex; align-items: center;'">
            <!-- 添加撤销/重做按钮在标题左侧 -->
            <div v-if="isEditing" class="history-buttons-title">
              <q-btn
                flat
                round
                dense
                color="negative"
                icon="undo"
                @click="undo"
                :disable="historyStack.length <= 1"
                class="history-btn"
                size="sm"
                style="min-width: 32px; min-height: 32px; width: 32px; height: 32px; background-color: #e0f2fe;"
              >
                <q-tooltip>Undo (Ctrl+Z)</q-tooltip>
              </q-btn>
              <q-btn
                flat
                round
                dense
                color="positive"
                icon="redo"
                @click="redo"
                :disable="redoStack.length === 0"
                class="history-btn"
                size="sm"
                style="min-width: 32px; min-height: 32px; width: 32px; height: 32px; background-color: #dbeafe;"
              >
                <q-tooltip>Redo (Ctrl+Y)</q-tooltip>
              </q-btn>
            </div>
            <!-- 添加VIEW GRAPH按钮，与VIEW RESPONSE对称 -->
            <div v-if="!isEditing" class="text-left">
              <q-btn
                flat
                dense
                class="view-switch-btn view-graph-btn"
                color="green-9"
                @click="toggleGraphView"
                size="sm"
              >
                <q-icon name="arrow_back" class="q-mr-sm" />
                VIEW GRAPH
              </q-btn>
            </div>
          </div>
          <div class="col-6 text-center" style="display: flex; align-items: center; justify-content: center;">
            {{ isResponseView ? 'Response' : 'Extracted Results' }}
          </div>
          <div class="col-3 text-right" style="display: flex; align-items: center; justify-content: flex-end;">
            <q-btn
              flat
              dense
              class="view-switch-btn view-response-btn"
              color="primary"
              @click="toggleView"
              size="sm"
            >
              {{ isResponseView ? 'VIEW TRIPLETS' : 'VIEW RESPONSE' }}
              <q-icon name="arrow_forward" class="q-ml-sm" />
            </q-btn>
          </div>
        </div>
        <q-card class="analysis-container">
          <!-- 新添加的容器 -->
          <q-card-section class="new-header-section">
            <div class="row full-width">
              <template v-if="isEditing">
                <div class="col-12">
                  <div class="edit-inputs-container">
                    <div class="row full-width">
                      <div class="col-6 text-center">
                        <q-select
                          v-model="contextTypeEdit"
                          :options="typeOptionsList"
                          dense
                          outlined
                          label="Type"
                          class="context-edit-input"
                          use-input
                          input-debounce="0"
                          @filter="filterTypeOptions"
                          @blur="onTypeBlur"
                          hide-selected
                          fill-input
                          new-value-mode="add-unique"
                          placeholder="Select or input Type"
                        >
                          <template v-slot:no-option>
                            <q-item>
                              <q-item-section class="text-italic text-grey">
                                No matches. Press Enter or leave field to add new value.
                              </q-item-section>
                            </q-item>
                          </template>
                        </q-select>
                      </div>
                      <div class="col-6 text-center">
                        <q-select
                          v-model="contextNameEdit"
                          :options="nameOptionsList"
                          dense
                          outlined
                          label="Name"
                          class="context-edit-input"
                          use-input
                          input-debounce="0"
                          @filter="filterNameOptions"
                          @blur="onNameBlur"
                          hide-selected
                          fill-input
                          new-value-mode="add-unique"
                          placeholder="Select or input Name"
                        >
                          <template v-slot:no-option>
                            <q-item>
                              <q-item-section class="text-italic text-grey">
                                No matches. Press Enter or leave field to add new value.
                              </q-item-section>
                            </q-item>
                          </template>
                        </q-select>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="col-12">
                  <div class="unified-context-display">
                    <div class="row full-width">
                      <div class="col-6 text-center">
                        <div class="field-text">Type: {{ contextType }}</div>
                      </div>
                      <div class="col-6 text-center">
                        <div class="field-text">Name: {{ contextName }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </q-card-section>
          
          <!-- 添加历史操作按钮组 - 仅在编辑模式下显示 -->
          <!-- <div v-if="isEditing" class="history-buttons-container">
            <q-btn
              flat
              round
              dense
              color="primary"
              icon="undo"
              @click="undo"
              :disable="historyStack.length === 0"
              class="history-btn"
            >
              <q-tooltip>Undo (Ctrl+Z)</q-tooltip>
            </q-btn>
            <q-btn
              flat
              round
              dense
              color="primary"
              icon="redo"
              @click="redo"
              :disable="redoStack.length === 0"
              class="history-btn"
            >
              <q-tooltip>Redo (Ctrl+Y)</q-tooltip>
            </q-btn>
          </div> -->
          
          <q-card-section class="analysis-scroll no-overflow no-border-top">
            <div v-if="isLoading" class="text-center">
              <q-spinner-dots size="40px" />
              <div class="text-subtitle1 q-mt-md">Processing data...</div>
            </div>
            <div v-else-if="!tableData.length" class="text-center text-grey-7">
              No data available
            </div>
            <template v-else>
              <!-- Triplets View -->
              <template v-if="!isResponseView">
                <q-table
                  :rows="tableData"
                  :columns="columns"
                  row-key="id"
                  hide-pagination
                  :rows-per-page-options="[0]"
                  @row-click="onRowClick"
                  class="analysis-table"
                  :class="{ 'editing-table': isEditing }"
                >
                  <!-- 添加表头区域插槽，在这里放置撤销/重做按钮 -->
                  <template v-slot:header>
                    <q-tr>
                      <q-th auto-width></q-th>
                      <q-th>Head</q-th>
                      <q-th>Relation</q-th>
                      <q-th>Tail</q-th>
                      <!-- 不再需要额外的列来放置按钮 -->
                    </q-tr>
                  </template>
                  
                  <template #body="props">
                    <q-tr :props="props" :class="getRowClass(props.row)" :data-row-id="props.row.id">
                      <!-- 展开按钮列 -->
                      <q-td auto-width>
                        <template v-if="isEditing || isExpandable(props.row)">
                          <q-btn
                            flat
                            dense
                            round
                            size="sm"
                            :icon="isExpanded(props.row) ? 'expand_more' : 'chevron_right'"
                            @click.stop="toggleExpand(props.row)"
                            :class="{ invisible: !isExpandable(props.row) && !isEditing }"
                            class="expand-button"
                          />
                        </template>
                      </q-td>
                      <!-- 数据列 -->
                      <q-td
                        v-for="col in props.cols.filter(
                          (col: QTableColumn<TableRow>) => col.name !== 'expand',
                        )"
                        :key="col.name"
                        :props="props"
                        @click="onRowClick($event, props.row)"
                        @mouseenter="onRowHover(props.row)"
                        @mouseleave="onRowLeave"
                        :class="{ 'cursor-pointer': !isEditing }"
                      >
                        <div v-if="isEditing">
                          <q-select
                            v-if="col.name === 'head' || col.name === 'tail'"
                            v-model="props.row[col.field as keyof TableRow]"
                            :options="nodesOptionsList"
                            dense
                            outlined
                            use-input
                            input-debounce="0"
                            @filter="filterNodesOptions"
                            @blur="(e) => onNodeBlur(e, props.row, col.field)"
                            @input="recordCurrentState"
                            hide-selected
                            fill-input
                            new-value-mode="add-unique"
                            :placeholder="`Select or input ${col.name}`"
                            @click.stop
                            :disable="props.row.isDeleted && props.row.isOriginal"
                            :class="{ 'disabled-input': props.row.isDeleted && props.row.isOriginal }"
                          >
                            <template v-slot:no-option>
                              <q-item>
                                <q-item-section class="text-italic text-grey">
                                  No matches. Press Enter or leave field to add new value.
                                </q-item-section>
                              </q-item>
                            </template>
                          </q-select>
                          <q-select
                            v-else-if="col.name === 'label'"
                            v-model="props.row[col.field as keyof TableRow]"
                            :options="relationsOptionsList"
                            dense
                            outlined
                            use-input
                            input-debounce="0"
                            @filter="filterRelationsOptions"
                            @blur="(e) => onRelationBlur(e, props.row)"
                            @input="recordCurrentState"
                            hide-selected
                            fill-input
                            new-value-mode="add-unique"
                            placeholder="Select or input relation"
                            @click.stop
                            :disable="props.row.isDeleted && props.row.isOriginal"
                            :class="{ 'disabled-input': props.row.isDeleted && props.row.isOriginal }"
                          >
                            <template v-slot:no-option>
                              <q-item>
                                <q-item-section class="text-italic text-grey">
                                  No matches. Press Enter or leave field to add new value.
                                </q-item-section>
                              </q-item>
                            </template>
                          </q-select>
                        </div>
                        <div v-else>
                          <span v-if="col.name === 'head' || col.name === 'tail'" class="entity-text">
                            {{ props.row[col.field as keyof TableRow] }}
                            <q-tooltip anchor="bottom middle" self="top middle" :offset="[0, 10]" class="entity-tooltip">
                              {{ getEntityInfo(props.row[col.field as keyof TableRow] as string) }}
                            </q-tooltip>
                          </span>
                          <span v-else>
                            {{ props.row[col.field as keyof TableRow] }}
                          </span>
                        </div>
                      </q-td>
                      <!-- 笔记图标列 -->
                      <q-td auto-width>
                        <q-btn
                          flat
                          round
                          dense
                          class="cursor-pointer"
                          @click.stop="toggleNotePopup(props.row)"
                          @mouseenter="onRowHover(props.row)"
                          @mouseleave="onRowLeave"
                        >
                          <q-icon name="edit_note" size="sm">
                            <!-- 悬浮提示 - 只在未固定时显示 -->
                            <q-tooltip
                              v-if="!props.row.showNote"
                              class="wide-tooltip"
                              max-width="500"
                              :offset="[10, 10]"
                              style="
                                background-color: #707070 !important;
                                color: #ffffff;
                                font-size: 20px !important;
                                padding: 15px;
                                white-space: pre-wrap !important;
                                min-width: 300px !important;
                              "
                            >
                              {{ props.row.note || 'Empty Note' }}
                            </q-tooltip>
                          </q-icon>
                        </q-btn>

                        <!-- 固定显示的笔记框 -->
                        <q-menu
                          v-model="props.row.showNote"
                          :offset="[10, 10]"
                          class="note-popup"
                          style="min-width: 300px !important; max-width: 500px !important;"
                        >
                          <div class="note-content" style="min-width: 300px !important; max-width: 500px !important;">
                            <div
                              class="note-header"
                              style="text-align: right; background-color: #707070"
                            >
                              <q-btn
                                flat
                                round
                                dense
                                icon="close"
                                size="sm"
                                style="color: #ffffff !important; font-size: 10px"
                                @click="props.row.showNote = false"
                              />
                            </div>
                            <div
                              class="note-body"
                              style="
                                background-color: #707070;
                                color: #ffffff;
                                font-size: 22px;
                                padding: 0 15px;
                                white-space: pre-wrap !important;
                              "
                            >
                              {{ props.row.note || 'Empty Note' }}
                            </div>
                          </div>
                        </q-menu>
                      </q-td>
                      <!-- 删除/恢复按钮列 -->
                      <q-td v-if="isEditing" auto-width>
                        <q-btn
                          v-if="props.row.isOriginal"
                          flat
                          dense
                          round
                          :color="!props.row.isDeleted ? 'primary' : 'grey-6'"
                          icon="refresh"
                          @click.stop="restoreRelation(props.row)"
                        >
                          <q-tooltip>{{
                            !props.row.isDeleted ? 'Restored' : 'Restore this relation'
                          }}</q-tooltip>
                        </q-btn>
                        <q-btn
                          v-else
                          flat
                          dense
                          round
                          color="negative"
                          icon="delete"
                          @click.stop="removeRelation(props.row)"
                        >
                          <q-tooltip>Delete this relation</q-tooltip>
                        </q-btn>
                      </q-td>
                    </q-tr>

                    <!-- 展开的元关系内容 -->
                    <q-tr
                      v-show="
                        isExpanded(props.row) && (props.row.metaRelations?.length > 0 || isEditing)
                      "
                      class="meta-relation-row"
                    >
                      <q-td />
                      <q-td colspan="3">
                        <div class="meta-relations q-pa-md">
                          <!-- 只在编辑模式下显示文本输入框 -->
                          <div v-if="isEditing" class="text-input q-mb-md">
                            <div class="text-subtitle2 q-mb-sm">Supporting Text</div>
                            <div class="supporting-text-container">
                              <q-input
                                v-model="props.row.text"
                                type="textarea"
                                filled
                                placeholder="Enter the supporting text for this relation..."
                                class="supporting-text-input"
                                maxlength="10000"
                                @input="recordCurrentState"
                                :disable="props.row.isDeleted && props.row.isOriginal"
                                :class="{ 'disabled-input': props.row.isDeleted && props.row.isOriginal }"
                              />
                            </div>
                          </div>
                          
                          <!-- 非编辑模式下显示文本区域 -->
                          <div v-else-if="props.row.text" class="text-input q-mb-md">
                            <div class="text-subtitle2 q-mb-sm">Supporting Text</div>
                            <div class="supporting-text-display">
                              {{ props.row.text }}
                            </div>
                          </div>

                          <!-- 添加笔记输入框 -->
                          <div v-if="isEditing" class="text-input q-mb-md">
                            <div class="text-subtitle2 q-mb-sm">Note</div>
                            <q-input
                              v-model="props.row.note"
                              type="textarea"
                              filled
                              autogrow
                              placeholder="Enter your notes here..."
                              @input="recordCurrentState"
                              :disable="props.row.isDeleted && props.row.isOriginal"
                              :class="{ 'disabled-input': props.row.isDeleted && props.row.isOriginal }"
                              class="note-textarea"
                            />
                          </div>
                          
                          <!-- 非编辑模式下显示笔记区域 -->
                          <div v-else-if="props.row.note" class="text-input q-mb-md">
                            <div class="text-subtitle2 q-mb-sm">Note</div>
                            <div class="note-display">
                              {{ props.row.note }}
                            </div>
                          </div>

                          <!-- Meta Relations 部分，只在有 metaRelations 或编辑模式下显示 -->
                          <template v-if="props.row.metaRelations?.length > 0 || isEditing">
                            <div class="text-subtitle2 q-mb-md">Meta Relations</div>
                            <div class="row q-col-gutter-md">
                              <div class="col-12">
                                <q-markup-table flat bordered>
                                  <thead>
                                    <tr>
                                      <template
                                        v-if="
                                          (props.row.metaRelations &&
                                            props.row.metaRelations.length > 0) ||
                                          isEditing
                                        "
                                      >
                                        <th class="text-center">Target</th>
                                        <th class="text-center">Label</th>
                                        <th v-if="isEditing" class="text-center"></th>
                                      </template>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    <template v-if="!props.row.metaRelations">
                                      <tr v-if="isEditing">
                                        <td colspan="3" class="text-center text-grey-7">
                                          No meta relations yet. Click + to add.
                                        </td>
                                      </tr>
                                    </template>
                                    <template v-else>
                                      <tr
                                        v-for="(meta, index) in props.row.metaRelations"
                                        :key="index"
                                      >
                                        <td class="text-center">
                                          <div v-if="isEditing">
                                            <q-input
                                              v-model="meta.target"
                                              dense
                                              outlined
                                              placeholder="Target"
                                              @input="recordCurrentState"
                                              class="text-center"
                                            />
                                          </div>
                                          <div v-else>{{ meta.target }}</div>
                                        </td>
                                        <td class="text-center">
                                          <div v-if="isEditing">
                                            <q-input
                                              v-model="meta.label"
                                              dense
                                              outlined
                                              placeholder="Label"
                                              @input="recordCurrentState"
                                              class="text-center"
                                            />
                                          </div>
                                          <div v-else>{{ meta.label }}</div>
                                        </td>
                                        <td v-if="isEditing" class="text-center" style="width: 50px">
                                          <q-btn
                                            flat
                                            round
                                            dense
                                            color="negative"
                                            icon="delete"
                                            @click="removeMetaRelation(props.row, index)"
                                          />
                                        </td>
                                      </tr>
                                    </template>
                                  </tbody>
                                  <!-- Meta Relations add button -->
                                  <tfoot v-if="isEditing">
                                    <tr>
                                      <td :colspan="3" class="text-center">
                                        <q-btn
                                          round
                                          dense
                                          color="primary"
                                          icon="add"
                                          class="meta-add-btn q-my-sm"
                                          @click="addMetaRelation(props.row)"
                                          :disable="props.row.isDeleted && props.row.isOriginal"
                                          :class="{ 'disabled-btn': props.row.isDeleted && props.row.isOriginal }"
                                        />
                                      </td>
                                    </tr>
                                  </tfoot>
                                </q-markup-table>
                              </div>
                            </div>
                          </template>
                        </div>
                      </q-td>
                    </q-tr>
                  </template>
                </q-table>
              </template>
              <!-- Response View -->
              <template v-else>
                <div class="response-view q-pa-md">
                  <div class="text-body1" style="white-space: pre-line">{{ analysisText }}</div>
                </div>
              </template>
            </template>

            <!-- 控制按钮组 -->
            <div v-if="!isResponseView" class="row justify-center q-mt-md full-width">
              <!-- Add relation button -->
              <q-btn
                v-if="isEditing"
                round
                dense
                color="primary"
                icon="add"
                class="relation-add-btn q-mx-sm"
                @click="addRelation"
              >
                <q-tooltip>Add new relation</q-tooltip>
              </q-btn>

              <q-btn
                v-if="isEditing"
                label="Cancel"
                color="negative"
                class="q-mx-sm"
                @click="cancelEdits"
              />
              <q-btn
                v-if="!isEditing && showCompleteButton"
                color="warning"
                label="Reset to Main"
                class="q-mx-sm"
                @click="confirmReset"
              >
                <q-tooltip>Reset to Main version</q-tooltip>
              </q-btn>
              <q-btn
                :label="isEditing ? 'Submit' : 'Edit'"
                :color="isEditing ? 'positive' : 'primary'"
                class="q-mx-sm"
                @click="isEditing ? submitEdits() : startEditing()"
                :disable="!isOwner"
                :class="{ 'disabled-btn': !isOwner }"
              >
                <q-tooltip v-if="!isOwner">{{ editTooltipText }}</q-tooltip>
              </q-btn>
              <q-btn
                v-if="!isEditing && showCompleteButton"
                label="Complete"
                color="secondary"
                class="q-mx-sm complete-btn"
                @click="completeAnalysis"
                :disable="!isOwner"
                :class="{ 'disabled-btn': !isOwner }"
              >
                <q-tooltip v-if="!isOwner">Only the owner user can edit</q-tooltip>
                <q-tooltip v-else>Submit modifications to Main folder</q-tooltip>
              </q-btn>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Bottom visualization area -->
    <div class="row q-mt-xxl" v-if="!isGraphView && showBottomGraph">
      <div class="col-12">
        <div class="text-h5 q-mb-md text-center">Graph</div>
        <q-card>
          <q-card-section>
            <!-- 使用GraphVisualizer组件替换iframe，传递entities数据 -->
            <div class="visualization-container">
              <GraphVisualizer 
                :key="graphUpdateKey"
                :entities="entities"
              />
            </div>
          </q-card-section>
          <!-- 移除这里的VIEW GRAPH按钮 -->
        </q-card>
      </div>
    </div>
    
    <!-- Full screen graph view -->
    <div v-if="isGraphView" class="row q-mb-md full-width">
      <div class="col-12">
        <div class="text-h5 q-mb-md text-center">
          <q-btn
            flat
            class="view-switch-btn view-text-btn"
            color="green-9"
            @click="toggleGraphView"
          >
            <q-icon name="arrow_back" class="q-mr-sm" />
            VIEW TEXT
          </q-btn>
        </div>
        <q-card>
          <q-card-section>
            <div class="visualization-container full-height">
              <GraphVisualizer 
                :key="graphUpdateKey"
                :entities="entities"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Add comment section -->
    <div class="row q-mt-xl">
      <div class="col-12">
        <CommentSection :paper-url="paperUrl" :current-user="currentUser" />
      </div>
    </div>
  </q-page>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed, onUnmounted, nextTick, watch } from 'vue'
import type { QTableColumn } from 'quasar'
import axios from 'axios'
import CommentSection from 'src/components/CommentSection.vue'
import GraphVisualizer from 'src/components/GraphVisualizer.vue'
import { useQuasar } from 'quasar'
import { useRoute, useRouter } from 'vue-router'
import typeOptions from '../../data/type_name_database.json'
import nodesRelationsData from '../../data/nodes_relations_database.json'
import { BACKEND_URL } from '../config/api'

/**
 * context数据项结构
 */
interface ContextItem {
  name: string;
  type: string;
  [key: string]: string; // 允许其他可能的属性
}

/**
 * 分析结果数据结构
 */
interface Analysis {
  key_points: string // 关键要点（head）
  implications: string // 关系（label）
  suggestions: string // 建议（tail）
}

/**
 * 实体数据类型定义
 */
type EntityValue = string[] // 例如 ["protein", "NULL"]
type EntitiesArray = string[] // 例如 ["ERK", "SHP-2"]
type EntitiesObject = Record<string, EntityValue> // 例如 {"ERK": ["protein", "NULL"]}
type EntitiesData = EntitiesArray | EntitiesObject // 可能是数组或对象

/**
 * 论文内容数据结构（与后端接口对应）
 */
interface PaperContent {
  id: number
  type: 'title' | 'abstract' | 'analysis' | 'context' | 'entities'
  content: string
  analysis?: Analysis
  text?: string
  metaRelations?: Array<{
    target: string
    label: string
  }>
  note?: string // 添加笔记字段
  extraction_time?: string // 添加抽取时间字段
  context?: ContextItem[] // 添加context数据
  entities?: EntitiesData // 添加entities数据
}

/**
 * 表格行数据结构
 */
interface TableRow {
  id: number // 行唯一标识符
  section: string // 章节名称
  head: string // 头实体
  label: string // 关系
  tail: string // 尾实体
  text?: string // 对应的文本位置
  expand?: string // 展开列
  metaRelations?: Array<{
    // 元关系数组
    target: string
    label: string
  }>
  note?: string // 添加笔记字段
  showNote?: boolean
  isOriginal?: boolean
  isDeleted?: boolean
  isNew?: boolean
}

interface OriginalRelation {
  head: string
  tail: string
  label: string
  text?: string
  metaRelations?: Array<{
    target: string
    label: string
  }>
}

export default defineComponent({
  name: 'PaperAnalysis',

  components: {
    CommentSection,
    GraphVisualizer,
  },

  setup() {
    const $q = useQuasar()
    const route = useRoute()
    const router = useRouter()  // 添加router

    // 响应式态变量
    const paperUrl = ref((route.query.url as string) || 'https://pubmed.ncbi.nlm.nih.gov/29795461') // 使用路由参数中的 URL，如果没有则使用默认值
    const selectedRow = ref(-1)
    const paperData = ref<PaperContent[]>([])
    const isEditing = ref(false) // 新增：是否处于编辑状态
    const isLoading = ref(false) // 添加加载状态
    const notes = ref<Record<string, string>>({}) // 存储笔记数据
    const extractionTime = ref('') // 添加抽取时间
    const extractionTimeSize = ref(24) // 将抽取时间字体大小增大到24px
    const urlInputSize = ref(20) // 添加 URL 输入框字体大小控制
    const originalRelations = ref<TableRow[]>([])
    const currentUser = ref(JSON.parse(localStorage.getItem('currentUser') || '{}'))
    const entities = ref<Record<string, string[]>>({}) // 添加实体数据存储

    // Add ref for abstract container
    const abstractText = ref<HTMLElement | null>(null)

    // Add method to sync heights
    const syncContainerHeights = () => {
      nextTick(() => {
        const abstractContainer = document.querySelector('.abstract-container') as HTMLElement
        const analysisContainer = document.querySelector('.analysis-container') as HTMLElement

        if (abstractContainer && analysisContainer) {
          const abstractHeight = abstractContainer.offsetHeight
          // 设置整个analysis-container的高度与abstract-container一致
          // 新添加的header-section固定高度为45px，analysis-scroll高度会自动调整为剩余空间
          // 移除编辑状态下的额外高度，确保编辑状态下容器高度也保持与abstract-container一致
          const additionalHeight = 0  // 从 isEditing.value ? 50 : 0 改为 0
          analysisContainer.style.height = `${abstractHeight + additionalHeight}px`
          
          // 确保非编辑状态下元组关系展示容器有固定高度和滚动能力
          if (!isEditing.value) {
            const analysisTable = document.querySelector('.analysis-table') as HTMLElement
            if (analysisTable) {
              analysisTable.style.overflow = 'auto';
            }
          }
        }
      })
    }

    // 格数据
    const tableData = ref<TableRow[]>([])
    // 添加一个变量用于存储编辑前的数据快照
    const originalTableData = ref<TableRow[]>([])

    // 添加isGraphView状态来控制图形视图的显示 - 移到这里确保它在 watch 之前声明
    const isGraphView = ref(false)
    
    // 添加控制底部Graph区域显示的变量，默认隐藏
    const showBottomGraph = ref(false)

    // Watch for changes that might affect height
    watch([paperData, tableData, isLoading], () => {
      syncContainerHeights()
    })
    
    // 监听 isGraphView 的变化，确保在切换回 Text 视图时同步容器高度
    watch(isGraphView, (newVal) => {
      if (!newVal) {  // 当从 Graph 视图切换回 Text 视图时
        nextTick(() => {
          syncContainerHeights()
        })
      }
    })

    // 初始化会话 ID
    onMounted(() => {
      // 添加点击事件监听器
      document.addEventListener('click', handlePageClick)
      window.addEventListener('resize', syncContainerHeights)
      
      // 添加键盘事件监听器，支持快捷键
      document.addEventListener('keydown', handleKeyDown);
    })

    // 在组件卸载时移除事件监听器
    onUnmounted(() => {
      document.removeEventListener('click', handlePageClick)
      window.removeEventListener('resize', syncContainerHeights)
      
      // 移除键盘事件监听器
      document.removeEventListener('keydown', handleKeyDown);
    })
    
    // 处理键盘快捷键
    const handleKeyDown = (event: KeyboardEvent) => {
      // 只在编辑模式下启用快捷键
      if (!isEditing.value) return;
      
      // Ctrl+Z: 撤销
      if (event.ctrlKey && event.key === 'z') {
        event.preventDefault();
        undo();
      }
      
      // Ctrl+Y: 重做
      if (event.ctrlKey && event.key === 'y') {
        event.preventDefault();
        redo();
      }
    };

    /**
     * 计算属性：获取论文标题
     * 从 paperData 中筛选 type 为 'title' 的内容
     */
    const title = computed(() => {
      const titleData = paperData.value.find((item) => item.type === 'title')
      return titleData?.content || ''
    })

    /**
     * 计算属性：获取论文摘要
     * 从 paperData 中筛选 type 为 'abstract' 的内容
     */
    const abstract = computed(() => {
      const abstractData = paperData.value.find((item) => item.type === 'abstract')
      return abstractData?.content || ''
    })

    // 当前选中的文本
    const selectedText = ref('')

    // 在 setup 中添加一个新的 ref 来存储悬浮状态的文本
    const hoverText = ref('')

    /**
     * 计算属性：生成带有高亮的 HTML
     */
    const highlightedAbstract = computed(() => {
      const text = abstract.value
      if (!text) return text

      // 创建一个标准化函数，忽略大小写、标点符号和空格
      const normalizeText = (str: string) => {
        return str.toLowerCase().replace(/[^\w\s]|_/g, '').replace(/\s+/g, ' ').trim()
      }

      // 在原始文本中查找匹配
      const findMatchInOriginal = (originalText: string, searchText: string) => {
        if (!searchText) return null
        
        // 标准化搜索文本
        const normalizedSearch = normalizeText(searchText)
        
        // 如果标准化后的搜索文本为空，返回null
        if (!normalizedSearch) return null
        
        // 标准化原始文本用于搜索
        const normalizedOriginal = normalizeText(originalText)
        
        // 查找匹配位置
        const matchIndex = normalizedOriginal.indexOf(normalizedSearch)
        if (matchIndex === -1) return null
        
        // 计算匹配长度（不能直接使用normalizedSearch.length，因为需要考虑原始文本的实际匹配）
        let originalIndex = 0
        let normalizedIndex = 0
        let startPos = -1
        let endPos = -1
        
        // 找到匹配开始位置
        while (normalizedIndex < matchIndex && originalIndex < originalText.length) {
          // 忽略标点符号和多余空格对索引的影响
          const char = originalText.charAt(originalIndex)
          if (/[a-zA-Z0-9\s]/.test(char)) {
            normalizedIndex++
          }
          originalIndex++
        }
        startPos = originalIndex
        
        // 继续查找直到匹配结束
        let remainingCharsToMatch = normalizedSearch.length
        while (remainingCharsToMatch > 0 && originalIndex < originalText.length) {
          // 只计算字母、数字和空格
          const char = originalText.charAt(originalIndex)
          if (/[a-zA-Z0-9\s]/.test(char)) {
            remainingCharsToMatch--
          }
          originalIndex++
        }
        endPos = originalIndex
        
        return { start: startPos, end: endPos }
      }

      // 使用滑动窗口查找匹配
      const findMatchWithSlidingWindow = (originalText: string, searchText: string) => {
        if (!searchText) return null
        
        // 标准化文本
        const normalizedSearch = normalizeText(searchText)
        const normalizedOriginal = normalizeText(originalText)
        
        // 如果标准化后的搜索文本为空，返回null
        if (!normalizedSearch) return null
        
        // 将搜索文本分割为单词
        const searchWords = normalizedSearch.split(' ')
        if (searchWords.length < 3) return null // 至少需要3个单词才能进行滑动窗口匹配
        
        // 计算前缀和后缀的长度
        const prefixLength = Math.max(2, Math.floor(searchWords.length * 0.3)) // 前缀取30%的单词数，最少2个
        const suffixLength = Math.max(2, Math.floor(searchWords.length * 0.5)) // 后缀取50%的单词数，最少2个
        
        // 获取前缀和后缀
        const prefix = searchWords.slice(0, prefixLength).join(' ')
        const suffix = searchWords.slice(-suffixLength).join(' ')
        
        // 在原始文本中查找前缀和后缀
        const prefixIndex = normalizedOriginal.indexOf(prefix)
        if (prefixIndex === -1) return null
        
        const suffixIndex = normalizedOriginal.indexOf(suffix, prefixIndex)
        if (suffixIndex === -1) return null
        
        // 创建辅助函数来转换标准化索引到原始索引
        const mapNormalizedIndexToOriginal = (normalizedTargetIndex: number) => {
          let normalizedCount = 0
          let originalIndex = 0
          
          while (normalizedCount < normalizedTargetIndex && originalIndex < originalText.length) {
            const char = originalText.charAt(originalIndex).toLowerCase()
            if (/[a-zA-Z0-9\s]/.test(char) && char !== '_') {
              normalizedCount++
            }
            originalIndex++
          }
          
          return originalIndex
        }
        
        // 计算原始文本中的匹配起始和结束位置
        const startPos = mapNormalizedIndexToOriginal(prefixIndex)
        const endPos = mapNormalizedIndexToOriginal(suffixIndex + suffix.length)
        
        return { start: startPos, end: endPos }
      }

      // 新增：使用分段匹配方法
      const findMatchWithChunks = (originalText: string, searchText: string) => {
        if (!searchText) return null
        
        // 标准化文本
        const normalizedSearch = normalizeText(searchText)
        
        // 如果标准化后的搜索文本为空，返回null
        if (!normalizedSearch) return null

        // 将原始文本分割成句子（基于句号、问号、感叹号等）
        const sentences = originalText.split(/[.!?]+/).filter(s => s.trim().length > 0)
        const normalizedSentences = sentences.map(s => normalizeText(s))
        
        // 首先尝试找到最有特点的子串作为锚点
        // 选择搜索文本的关键特征词（如命名实体、特殊术语等）
        const searchWords = normalizedSearch.split(' ')
        
        // 找到最长或最不常见的词作为锚点（简单实现：取长度最长的词）
        let anchorWord = ''
        for (const word of searchWords) {
          if (word.length > anchorWord.length && word.length > 3) {
            anchorWord = word
          }
        }
        
        // 如果没有足够长的词，就使用中间的几个词作为锚点
        if (anchorWord.length <= 3) {
          const midIndex = Math.floor(searchWords.length / 2)
          const startIdx = Math.max(0, midIndex - 1)
          const endIdx = Math.min(searchWords.length, midIndex + 2)
          anchorWord = searchWords.slice(startIdx, endIdx).join(' ')
        }
        
        // 找到锚点在原文中的位置
        let bestMatchScore = 0
        let bestSentenceIndex = -1
        
        // 遍历每个句子查找最佳匹配
        for (let i = 0; i < normalizedSentences.length; i++) {
          const sentence = normalizedSentences[i]
          
          // 检查锚点是否在句子中（添加空值检查）
          if (sentence && sentence.includes(anchorWord)) {
            // 计算这个句子与搜索文本的相似度
            let matchedChars = 0
            const totalChars = normalizedSearch.length
            
            for (const word of searchWords) {
              if (sentence.includes(word)) {
                matchedChars += word.length
              }
            }
            
            const similarityScore = matchedChars / totalChars
            
            // 如果相似度超过阈值，并且比之前找到的最佳匹配更好
            if (similarityScore > 0.75 && similarityScore > bestMatchScore) {
              bestMatchScore = similarityScore
              bestSentenceIndex = i
            }
          }
        }
        
        // 如果找到了好的匹配
        if (bestSentenceIndex >= 0) {
          // 映射回原始文本中的位置
          let startPos = 0
          for (let i = 0; i < bestSentenceIndex; i++) {
            // 添加空值检查
            const sentence = sentences[i]
            if (sentence) {
              startPos += sentence.length + 1
            }
          }
          
          // 添加空值检查
          const matchedSentence = sentences[bestSentenceIndex]
          if (!matchedSentence) return null
          
          const endPos = startPos + matchedSentence.length
          
          return { start: startPos, end: endPos }
        }
        
        return null
      }

      // 主函数：查找匹配
      const findMatch = (originalText: string, searchText: string) => {
        // 首先尝试精确匹配
        const exactMatch = findMatchInOriginal(originalText, searchText)
        if (exactMatch) return exactMatch
        
        // 如果精确匹配失败，尝试滑动窗口匹配
        const slidingMatch = findMatchWithSlidingWindow(originalText, searchText)
        if (slidingMatch) return slidingMatch
        
        // 如果滑动窗口匹配失败，尝试分段匹配
        return findMatchWithChunks(originalText, searchText)
      }

      // 新增：处理重叠区域的函数
      const processOverlappingRegions = (text: string, regions: Array<{start: number, end: number, type: 'click' | 'hover'}>) => {
        // 按开始位置排序
        regions.sort((a, b) => {
          // 首先按照开始位置排序
          if (a.start !== b.start) return a.start - b.start
          // 如果开始位置相同，click类型优先
          if (a.type === 'click' && b.type === 'hover') return -1
          if (a.type === 'hover' && b.type === 'click') return 1
          // 如果类型也相同，按结束位置排序
          return a.end - b.end
        })
        
        let result = ''
        let currentPos = 0
        let activeRegions: typeof regions = []
        
        // 创建所有区域的边界点
        const boundaries = regions.reduce((acc, region) => {
          if (!region) return acc
          acc.push({ pos: region.start, type: 'start', region })
          acc.push({ pos: region.end, type: 'end', region })
          return acc
        }, [] as Array<{pos: number, type: 'start' | 'end', region: typeof regions[0]}>)
        
        // 按位置排序边界点
        boundaries.sort((a, b) => {
          if (a.pos !== b.pos) return a.pos - b.pos
          // 确保结束点在开始点之前处理
          if (a.type === 'end' && b.type === 'start') return -1
          if (a.type === 'start' && b.type === 'end') return 1
          return 0
        })
        
        // 处理每个边界点
        for (let i = 0; i < boundaries.length; i++) {
          const boundary = boundaries[i]
          if (!boundary) continue
          
          // 添加当前位置到边界点之间的文本
          if (boundary.pos > currentPos) {
            // 处理当前活动区域的文本
            if (activeRegions.length > 0) {
              const text_segment = text.substring(currentPos, boundary.pos)
              // 优先使用click类型的高亮
              const hasClick = activeRegions.some(r => r?.type === 'click')
              const hasHover = !hasClick && activeRegions.some(r => r?.type === 'hover')
              
              if (hasClick) {
                result += `<span class="highlighted">${text_segment}</span>`
              } else if (hasHover) {
                result += `<span class="hover-highlighted">${text_segment}</span>`
              } else {
                result += text_segment
              }
            } else {
              result += text.substring(currentPos, boundary.pos)
            }
          }
          
          // 更新活动区域
          if (boundary.type === 'start') {
            activeRegions.push(boundary.region)
          } else {
            activeRegions = activeRegions.filter(r => r !== boundary.region)
          }
          
          currentPos = boundary.pos
        }
        
        // 添加剩余的文本
        if (currentPos < text.length) {
          result += text.substring(currentPos)
        }
        
        return result
      }

      // 收集需要高亮的区域
      const regions: Array<{start: number, end: number, type: 'click' | 'hover'}> = []
      
      // 处理选中的文本
      if (selectedText.value) {
        const match = findMatch(text, selectedText.value)
        if (match) {
          regions.push({...match, type: 'click'})
        }
      }
      
      // 处理悬浮的文本
      if (hoverText.value && hoverText.value !== selectedText.value) {
        const match = findMatch(text, hoverText.value)
        if (match) {
          regions.push({...match, type: 'hover'})
        }
      }
      
      // 如果没有需要高亮的区域，直接返回原文
      if (regions.length === 0) {
        return text
      }
      
      // 处理所有高亮区域
      return processOverlappingRegions(text, regions)
    })

    /**
     * 行点击事件处理
     * 更新选中的行，触发高亮效果
     */
    const onRowClick = (_evt: Event, row: TableRow) => {
      // 如果点击的是当前选中的行，则取消选中
      if (selectedRow.value === row.id) {
        selectedRow.value = -1
        selectedText.value = ''
      } else {
        // 否则选中新的行
        selectedRow.value = row.id
        selectedText.value = row.text || ''
      }
    }

    /**
     * 单元格获取焦点时处理
     * 更新选中的行，保持一致的高亮效果
     */
    const onCellFocus = (row: TableRow) => {
      selectedRow.value = row.id
      selectedText.value = row.text || ''
    }

    // 添加点击页面其他区域取消高亮的处理函数
    const handlePageClick = (event: MouseEvent) => {
      // 检查点击的元素是否在表格内
      const isClickInTable = (event.target as HTMLElement)?.closest('.q-table')

      // 如果点击的不是表格区域，则取消高亮
      if (!isClickInTable) {
        selectedRow.value = -1
        selectedText.value = ''
        hoverText.value = ''
      }
    }

    // 表格列定义
    const columns = ref<QTableColumn<TableRow>[]>([
      {
        name: 'expand',
        label: '',
        field: (row) => row.id,
        align: 'center',
        style: 'width: 50px',
      },
      {
        name: 'head',
        label: 'Head',
        field: 'head',
        align: 'center',
        style: 'padding-right: 24px !important',
      },
      {
        name: 'label',
        label: 'Relation',
        field: 'label',
        align: 'center',
        style: 'padding-left: 24px !important; padding-right: 24px !important',
      },
      {
        name: 'tail',
        label: 'Tail',
        field: 'tail',
        align: 'center',
        style: 'padding-left: 24px !important',
      },
    ])

    /**
     * 从后端获取数据的方法
     * 使用 axios 发起 HTTP GET 请求到端 API
     */
    const fetchData = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/paper-analysis`, {
          params: {
            url: paperUrl.value,
            username: currentUser.value.username,
            mode: route.query.mode || 'view',
            user: route.query.user,
          },
        })

        // 检查是否有错误响应
        if (response.data.error) {
          console.error('Error from server:', response.data.error)
          paperData.value = []
          tableData.value = []
          originalRelations.value = []
          contextData.value = []
          extractionTime.value = ''
          pmid.value = ''
          return
        }

        paperData.value = response.data
        // 提取context数据
        const contextItem = response.data.find((item: PaperContent) => item.type === 'context')
        if (contextItem && contextItem.context) {
          contextData.value = contextItem.context
        } else {
          contextData.value = []
        }
        
        // 提取entities数据
        const entitiesItem = response.data.find((item: PaperContent) => item.type === 'entities')
        if (entitiesItem && entitiesItem.entities) {
          // 调用处理entities的方法
          processEntitiesData(entitiesItem.entities)
        } else {
          // 如果在paper-analysis中找不到entities，则回退到original-relations
          await fetchEntitiesData()
        }
        
        // 设置抽取时间
        const titleData = response.data.find((item: PaperContent) => item.type === 'title')
        if (titleData && titleData.extraction_time) {
          extractionTime.value = titleData.extraction_time
        }

        // 获取原始数据
        try {
          const extractedPmid = paperUrl.value.replace(/\/$/, '').split('/').pop() || ''
          pmid.value = extractedPmid // 设置PMID值
          const originalResponse = await axios.get(
            `${BACKEND_URL}/api/original-relations?pmid=${extractedPmid}`,
          )

          // 转换原始数据格式
          originalRelations.value = originalResponse.data.relations.map(
            (relation: OriginalRelation, index: number) => ({
              id: index + 1000, // 使用不同的 ID 范围避免冲突
              section: `Original Relation ${index + 1}`,
              head: relation.head,
              tail: relation.tail,
              label: relation.label,
              text: relation.text || '',
              metaRelations: relation.metaRelations || [],
              isOriginal: true,
            }),
          )
        } catch (error) {
          console.error('Error fetching original relations:', error)
          originalRelations.value = []
        }

        // 转换当前数据格式以适应表格显示
        const currentRelations = response.data
          .filter((item: PaperContent) => item.type === 'analysis')
          .map((item: PaperContent) => ({
            id: item.id,
            section: item.content,
            head: item.analysis?.key_points || '',
            tail: item.analysis?.suggestions || '',
            label: item.analysis?.implications || '',
            text: item.text || '',
            metaRelations: item.metaRelations || [],
            note: item.note || '',
            showNote: false,
          }))

        // 合并原始关系和当前关系
        const mergedRelations = [...currentRelations]

        // 加载笔记数据
        await loadNotes()

        // 添加在原始数据中存在但当前数据中不存在的关系
        originalRelations.value.forEach((originalRelation) => {
          const exists = currentRelations.some(
            (currentRelation: TableRow) =>
              currentRelation.head === originalRelation.head &&
              currentRelation.label === originalRelation.label &&
              currentRelation.tail === originalRelation.tail,
          )

          if (!exists) {
            // 为已删除的关系添加笔记
            const noteKey = `${originalRelation.head}|${originalRelation.label}|${originalRelation.tail}`
            mergedRelations.push({
              ...originalRelation,
              isDeleted: true, // 标记为已删除
              note: notes.value[noteKey] || '', // 添加笔记
            })
          }
        })

        // 标记新增的关系并添加笔记
        mergedRelations.forEach((relation) => {
          const noteKey = `${relation.head}|${relation.label}|${relation.tail}`
          relation.note = notes.value[noteKey] || '' // 确保每个关系都有笔记字段

          if (!relation.isDeleted) {
            // 如果不是已删除的关系
            const existsInOriginal = originalRelations.value.some(
              (originalRelation) =>
                originalRelation.head === relation.head &&
                originalRelation.label === relation.label &&
                originalRelation.tail === relation.tail,
            )

            if (!existsInOriginal) {
              relation.isNew = true // 标记为新增
            }
          }
        })

        tableData.value = mergedRelations

        // 获取数据后重新生成可视化
        try {
          // 获取当前模式和目标用户
          const currentMode = route.query.mode || 'view'
          const targetUser = route.query.user

          // 只在以下情况发送update-analysis请求:
          // 1. 临时模式(temp) - 允许编辑
          // 2. 查看模式(view)且查看的是自己的数据(没有指定user或user等于当前用户)
          if (currentMode === 'temp' || 
              (currentMode === 'view' && (!targetUser || targetUser === currentUser.value.username))) {
            
            console.log('Regenerating visualization for current user data')
            await axios.post(`${BACKEND_URL}/api/update-analysis`, {
              data: tableData.value,
              url: paperUrl.value,
              username: currentUser.value.username,
              mode: currentMode,
              entities: entities.value, // 添加实体数据，保持类型信息
              context: contextData.value // 确保context数据也一起提交
            })
          } else {
            console.log('Skipping update-analysis in view mode for other user data')
          }
        } catch (error) {
          console.error('Error regenerating visualization:', error)
        }
      } catch (error) {
        console.error('Error fetching data:', error)
        paperData.value = []
        tableData.value = []
      }
    }

    /**
     * 处理实体数据的方法
     */
    const processEntitiesData = (entitiesData: EntitiesData) => {
      console.log('处理实体数据:', JSON.stringify(entitiesData))
      
      // 检查entities的数据类型
      if (Array.isArray(entitiesData)) {
        console.log('entities是数组格式，转换为对象格式')
        // 如果是数组，转换为对象格式，但不默认分配protein类型
        const entitiesObj: Record<string, string[]> = {}
        entitiesData.forEach((entity: string) => {
          entitiesObj[entity] = ["NULL", "NULL"]
        })
        entities.value = entitiesObj
      } else {
        // 如果已经是对象格式，直接使用
        entities.value = entitiesData
      }
    }

    /**
     * 从后端获取实体数据（仅在paper-analysis没有返回entities时作为备用）
     */
    const fetchEntitiesData = async () => {
      try {
        const extractedPmid = paperUrl.value.replace(/\/$/, '').split('/').pop() || ''
        pmid.value = extractedPmid // 设置PMID值
        
        // 从原始关系数据接口获取entities数据
        const originalResponse = await axios.get(
          `${BACKEND_URL}/api/original-relations?pmid=${extractedPmid}`,
        )
        
        // 调试打印原始数据结构
        console.log('原始entities数据结构(从original-relations获取):', JSON.stringify(originalResponse.data.entities))
        
        // 处理实体数据
        if (originalResponse.data && originalResponse.data.entities) {
          processEntitiesData(originalResponse.data.entities)
        }
      } catch (error) {
        console.error('Error fetching entities data:', error)
        entities.value = {}
      }
    }

    // 展开行相关的状态和方法
    const expandedRows = ref<number[]>([])

    const isExpandable = (row: TableRow) => {
      if (!row) return false
      return Array.isArray(row.metaRelations) && row.metaRelations.length > 0
    }

    const toggleExpand = (row: TableRow) => {
      console.log('Toggling row:', row.id, 'metaRelations:', row.metaRelations)
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
      console.log('Expanded rows:', expandedRows.value)
    }

    const isExpanded = (row: TableRow) => {
      return expandedRows.value.includes(row.id)
    }

    // 添加用于记录编辑时间的变量
    const editStartTime = ref<number>(0);

    // 添加历史记录相关的变量
    const historyStack = ref<TableRow[][]>([]);
    const redoStack = ref<TableRow[][]>([]);
    const maxHistorySize = 20; // 历史记录最大长度

    // 添加记录当前状态的方法
    const recordCurrentState = () => {
      // 记录当前的tableData状态到historyStack
      historyStack.value.push(JSON.parse(JSON.stringify(tableData.value)));
      
      // 如果历史记录超过最大长度，移除最旧的记录
      if (historyStack.value.length > maxHistorySize) {
        historyStack.value.shift();
      }
      
      // 每次记录新状态时，清空重做栈
      redoStack.value = [];
    };

    // 添加撤销功能
    const undo = () => {
      // 如果历史栈为空，无法撤销
      if (historyStack.value.length === 0) return;
      
      // 将当前状态保存到重做栈
      redoStack.value.push(JSON.parse(JSON.stringify(tableData.value)));
      
      // 恢复上一个状态
      const previousState = historyStack.value.pop();
      if (previousState) {
        tableData.value = previousState;
      }
    };

    // 添加重做功能
    const redo = () => {
      // 如果重做栈为空，无法重做
      if (redoStack.value.length === 0) return;
      
      // 将当前状态保存到历史栈
      historyStack.value.push(JSON.parse(JSON.stringify(tableData.value)));
      
      // 恢复下一个状态
      const nextState = redoStack.value.pop();
      if (nextState) {
        tableData.value = nextState;
      }
    };

    // 提交编辑后的数据
    const submitEdits = async () => {
      try {
        // 计算编辑用时（毫秒）
        const editDuration = Date.now() - editStartTime.value
        
        // 更新笔记的key
        const updatedNotes: Record<string, string> = {}

        // 遍历所有关系，更新笔记
        tableData.value.forEach((row) => {
          const newKey = `${row.head}|${row.label}|${row.tail}`
          // 如果这个关系有笔记，记录它
          if (row.note) {
            updatedNotes[newKey] = row.note
          }
        })

        // 直接替换整个notes对象
        notes.value = updatedNotes

        // 保存更新后的笔记
        await saveNotes()

        // 更新context数据
        if (contextData.value.length > 0) {
          // 查找并更新type和name属性
          const typeItem = contextData.value.find(item => item.type)
          const nameItem = contextData.value.find(item => item.name)
          
          if (typeItem) {
            typeItem.type = contextTypeEdit.value
          } else if (contextTypeEdit.value !== 'NULL') {
            // 如果不存在type项但有编辑值，则添加一个新项
            contextData.value.push({ type: contextTypeEdit.value, name: '' })
          }
          
          if (nameItem) {
            nameItem.name = contextNameEdit.value
          } else if (contextNameEdit.value !== 'NULL') {
            // 如果不存在name项但有编辑值，则添加一个新项
            contextData.value.push({ name: contextNameEdit.value, type: '' })
          }
        } else if (contextTypeEdit.value !== 'NULL' || contextNameEdit.value !== 'NULL') {
          // 如果contextData为空但有编辑值，创建一个新的context项
          contextData.value = [{
            type: contextTypeEdit.value !== 'NULL' ? contextTypeEdit.value : '',
            name: contextNameEdit.value !== 'NULL' ? contextNameEdit.value : ''
          }]
        }

        console.log('Submitting edited data:', tableData.value)
        
        // 构建要发送的数据，包括context数据和编辑用时
        const dataToSubmit = {
          data: tableData.value,
          url: paperUrl.value,
          username: currentUser.value.username,
          mode: route.query.mode || 'view',
          context: contextData.value, // 添加context数据
          entities: entities.value, // 添加entities数据，保持类型信息
          editDuration: editDuration // 添加编辑用时（毫秒）
        }
        
        const response = await axios.post(`${BACKEND_URL}/api/update-analysis`, dataToSubmit)
        
        console.log('Server response:', response.data)
        isEditing.value = false
        
        // 清空expandedRows，收起所有展开的行
        expandedRows.value = []

        // 添加延时等待文件生成完成
        await new Promise((resolve) => setTimeout(resolve, 500))

        // 更新graphUpdateKey触发GraphVisualizer组件重新渲染
        graphUpdateKey.value = Date.now()

        // 重新获取数据以更新高亮状态和图形
        await fetchData()

        // 显示成功通知
        $q.notify({
          type: 'positive',
          message: 'Changes saved successfully',
          position: 'top',
          timeout: 2000,
        })
      } catch (error) {
        console.error('Error submitting edits:', error)
        $q.notify({
          type: 'negative',
          message: 'Error saving changes',
          position: 'top',
          timeout: 2000,
        })
      }
    }

    // 取消编辑
    const cancelEdits = () => {
      // 直接从快照恢复数据，不进行网络请求
      tableData.value = JSON.parse(JSON.stringify(originalTableData.value))
      // 重置context编辑值
      contextTypeEdit.value = contextType.value
      contextNameEdit.value = contextName.value
      // 清空expandedRows，收起所有展开的行
      expandedRows.value = []
      // 立即退出编辑模式
      isEditing.value = false
    }

    // 添加进入编辑模式的函数
    const startEditing = () => {
      // 保存当前数据的深拷贝作为快照
      originalTableData.value = JSON.parse(JSON.stringify(tableData.value))
      // 初始化context编辑值
      contextTypeEdit.value = contextType.value
      contextNameEdit.value = contextName.value
      // 记录开始编辑的时间
      editStartTime.value = Date.now()
      // 进入编辑模式
      isEditing.value = true
      
      // 清空历史记录和重做栈
      historyStack.value = [];
      redoStack.value = [];
      // 记录初始状态到historyStack，但不要立即启用撤销功能
      // 当用户开始编辑后，我们会记录第二个状态，这时撤销功能才会启用
      historyStack.value.push(JSON.parse(JSON.stringify(tableData.value)));
      // 不再调用recordCurrentState()，避免记录两次初始状态
    }

    // 添加新的 Meta Relation
    const addMetaRelation = (row: TableRow) => {
      // 记录当前状态，用于撤销
      recordCurrentState();
      
      if (!row.metaRelations) {
        row.metaRelations = []
      }
      row.metaRelations.push({
        target: '',
        label: '',
      })
      if (row.metaRelations.length === 1) {
        expandedRows.value.push(row.id)
      }
    }

    // 删除 Meta Relation
    const removeMetaRelation = (row: TableRow, index: number) => {
      // 记录当前状态，用于撤销
      recordCurrentState();
      
      if (row.metaRelations) {
        row.metaRelations.splice(index, 1)
      }
    }

    // 修改 addRelation 方法
    const addRelation = () => {
      // 记录当前状态，用于撤销
      recordCurrentState();
      
      const newId = Math.max(...tableData.value.map((row) => row.id), 0) + 1
      tableData.value.push({
        id: newId,
        section: `Relation ${newId - 2}`,
        head: '',
        tail: '',
        label: '',
        text: '',
        note: '',
        metaRelations: [],
        showNote: false,
      })
      expandedRows.value.push(newId)
      // 初始化笔记
      notes.value[newId.toString()] = ''
    }

    // 删除关系
    const removeRelation = (row: TableRow) => {
      // 记录当前状态，用于撤销
      recordCurrentState();
      
      const index = tableData.value.findIndex((item) => item.id === row.id)
      if (index !== -1) {
        // 删除对应的笔记
        const noteKey = `${row.head}|${row.label}|${row.tail}`
        delete notes.value[noteKey]

        tableData.value.splice(index, 1)
      }
    }

    // 处理提交按钮点击
    const handleSubmit = async () => {
      if (!paperUrl.value) {
        return
      }

      isLoading.value = true
      try {
        // 先获取并显示基本信息
        await fetchBasicData()
        // 然后异步加载分析数据
        await fetchAnalysisData()
      } catch (error) {
        console.error('Error fetching data:', error)
        // 确保在错误时也清空数据
        paperData.value = []
        tableData.value = []
      } finally {
        isLoading.value = false
      }
    }

    // 组件挂载时获取数据
    onMounted(async () => {
      // 添加点击事件监听器
      document.addEventListener('click', handlePageClick)

      // 加载初始数据
      isLoading.value = true
      try {
        await fetchData()
        await loadNotes()
      } finally {
        isLoading.value = false
      }
    })

    // 获取基本数据（标题和摘要）
    const fetchBasicData = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/paper-analysis`, {
          params: {
            url: paperUrl.value,
            username: currentUser.value.username,
            mode: route.query.mode || 'view',
            user: route.query.user, // 添加目标用户参数
          },
        })

        if (response.data.error) {
          console.error('Error from server:', response.data.error)
          paperData.value = []
          return
        }

        // 只设置标题和摘要
        paperData.value = response.data.filter(
          (item: PaperContent) => item.type === 'title' || item.type === 'abstract',
        )

        // 设置抽取时间
        const titleData = response.data.find((item: PaperContent) => item.type === 'title')
        if (titleData && titleData.extraction_time) {
          extractionTime.value = titleData.extraction_time
        }
      } catch (error) {
        console.error('Error fetching basic data:', error)
        paperData.value = []
      }
    }

    // 获取分析数据
    const fetchAnalysisData = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/paper-analysis`, {
          params: {
            url: paperUrl.value,
            username: currentUser.value.username,
            mode: route.query.mode || 'view',
            user: route.query.user, // 添加目标用户参数
          },
        })

        if (response.data.error) {
          console.error('Error from server:', response.data.error)
          tableData.value = []
          return
        }

        // 设置分析数据
        const analysisItems = response.data.filter((item: PaperContent) => item.type === 'analysis')
        paperData.value = [...paperData.value, ...analysisItems]

        // 转换数据格式以适应表格显示
        tableData.value = analysisItems.map((item: PaperContent) => ({
          id: item.id,
          section: item.content,
          head: item.analysis?.key_points || '',
          tail: item.analysis?.suggestions || '',
          label: item.analysis?.implications || '',
          text: item.text || '',
          metaRelations: item.metaRelations || [],
          note: item.note || '',
          showNote: false,
        }))

        // 获取数据后重新生成可视化
        try {
          await axios.post(`${BACKEND_URL}/api/update-analysis`, {
            data: tableData.value,
            url: paperUrl.value,
            username: currentUser.value.username,
            mode: route.query.mode || 'view',
          })
        } catch (error) {
          console.error('Error regenerating visualization:', error)
        }
      } catch (error) {
        console.error('Error fetching analysis data:', error)
        tableData.value = []
      }
    }

    // 修改 onRowHover 和 onRowLeave 方法
    const onRowHover = (row: TableRow) => {
      if (row.text) {
        hoverText.value = row.text
      }
    }

    const onRowLeave = () => {
      hoverText.value = ''
    }

    // 加载笔记
    const loadNotes = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/load-notes`, {
          params: {
            url: paperUrl.value,
            username: currentUser.value.username,
            mode: route.query.mode || 'view',
            target_user: route.query.user || currentUser.value.username,
          },
        })
        if (response.data.success) {
          notes.value = response.data.notes
        }
      } catch (error) {
        console.error('Error loading notes:', error)
      }
    }

    // 保存笔记
    const saveNotes = async () => {
      try {
        const notesData: Record<string, string> = {}
        tableData.value.forEach((row) => {
          if (row.note) {
            // 使用一致的key格式
            const key = `${row.head}|${row.label}|${row.tail}`
            notesData[key] = row.note
          }
        })

        await axios.post(`${BACKEND_URL}/api/save-notes`, {
          notes: notesData,
          url: paperUrl.value,
          username: currentUser.value.username,
          mode: route.query.mode || 'view',
          target_user: route.query.user || currentUser.value.username,
        })
      } catch (error) {
        console.error('Error saving notes:', error)
      }
    }

    // 添加点击事件
    const toggleNotePopup = (row: TableRow) => {
      // 关闭其他所有笔记弹窗
      tableData.value.forEach((r) => {
        if (r.id !== row.id) {
          r.showNote = false
        }
      })
      // 切换当前笔记弹窗
      row.showNote = !row.showNote
    }

    // 修改表格行的样式
    const getRowClass = (row: TableRow) => {
      const classes = []
      if (row.isDeleted && row.isOriginal) classes.push('bg-red-1') // 红色背景表示已删除的原始关系
      if (row.isNew) classes.push('bg-green-1') // 绿色背景表示新增
      if (selectedRow.value === row.id) classes.push('bg-yellow-2') // 选中行的高亮
      return classes.join(' ')
    }

    // 修改恢复关系的方法
    const restoreRelation = (row: TableRow) => {
      // 记录当前状态，用于撤销
      recordCurrentState();
      
      row.isDeleted = !row.isDeleted // 切换删除状态
    }

    // 在 setup 函数中添加 completeAnalysis 方法
    const completeAnalysis = async () => {
      try {
        // 不需要再次调用 submitEdits，因为用户在点击 Complete 之前应该已经保存了修改
        const response = await axios.post(`${BACKEND_URL}/api/complete-analysis`, {
          url: paperUrl.value,
          username: currentUser.value.username,
        })

        if (response.data.success) {
          $q.notify({
            type: 'positive',
            message: 'Analysis completed and saved to Main folder successfully',
            position: 'top',
            timeout: 2000,
            html: true,
            classes: 'text-h6',
          })
        }
      } catch (error) {
        console.error('Error completing analysis:', error)
        $q.notify({
          type: 'negative',
          message: 'Error completing analysis',
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      }
    }

    // 在 setup 中添加计算属性
    const isOwner = computed(() => {
      // 如果是 Main folder 模式，允许所有用户编辑
      if (route.query.mode === 'temp') return true
      // 否则检查当前用户是否是所属用户
      return route.query.user === currentUser.value.username
    })

    // 添加新的计算属性控制 Complete 按钮的显示
    const showCompleteButton = computed(() => {
      return route.query.mode === 'temp'
    })

    // 在 setup 函数中添加 graphUpdateKey
    const graphUpdateKey = ref(Date.now())

    // 修改为计算属性
    const visualizationUrl = computed(() => {
      const pmid = paperUrl.value.split('/').pop()?.replace('/', '') || ''
      const mode = route.query.mode || 'view'
      const targetUser = route.query.user || currentUser.value.username

      // 构建基础 URL
      let baseUrl = `${BACKEND_URL}/api/graph?`
      baseUrl += `pmid=${pmid}`
      baseUrl += `&username=${currentUser.value.username}`
      baseUrl += `&mode=${mode}`
      baseUrl += `&target_user=${targetUser}`

      // 使用 graphUpdateKey 作为时间戳
      baseUrl += `&t=${graphUpdateKey.value}`

      return baseUrl
    })

    // 在 setup 函数中添加重置功能
    const confirmReset = () => {
      $q.dialog({
        title: 'Confirm Reset',
        message:
          '<div style="font-size: 18px">Are you sure you want to reset to the Main version? This will overwrite your current changes.</div>',
        html: true,
        persistent: true,
        ok: {
          color: 'warning',
          label: 'Reset',
        },
        cancel: {
          color: 'grey',
          label: 'Cancel',
        },
      }).onOk(async () => {
        try {
          const response = await axios.post(`${BACKEND_URL}/api/reset-to-main`, {
            url: paperUrl.value,
            username: currentUser.value.username,
          })

          if (response.data.success) {
            // 重新加载数据
            await fetchData()
            $q.notify({
              type: 'positive',
              message: 'Successfully reset to Main version',
              position: 'top',
              timeout: 2000,
              html: true,
              classes: 'text-size-18',
            })
          }
        } catch (error) {
          console.error('Error resetting to main:', error)
          $q.notify({
            type: 'negative',
            message: 'Error resetting to Main version',
            position: 'top',
            timeout: 2000,
            html: true,
            classes: 'text-size-18',
          })
        }
      })
    }

    // 添加isResponseView状态
    const isResponseView = ref(false)
    const analysisText = ref('')
    
    // 切换视图的方法
    const toggleView = async () => {
      isResponseView.value = !isResponseView.value
      if (isResponseView.value) {
        // 获取原始数据
        try {
          const extractedPmid = paperUrl.value.replace(/\/$/, '').split('/').pop() || ''
          const originalResponse = await axios.get(
            `${BACKEND_URL}/api/original-relations?pmid=${extractedPmid}`,
          )
          analysisText.value = originalResponse.data.analysis || ''
        } catch (error) {
          console.error('Error fetching original relations:', error)
          analysisText.value = ''
        }
      }
    }
    
    // 切换图形视图的方法
    const toggleGraphView = () => {
      isGraphView.value = !isGraphView.value
      
      if (!isGraphView.value) {
        // 从 Graph 视图切换回 Text 视图时，确保布局正确恢复
        nextTick(() => {
          // 使用多层 nextTick 确保 DOM 完全更新后再处理布局
          nextTick(() => {
            // 同步容器高度
            syncContainerHeights()
            
            // 通过刷新布局来确保左右列布局正确
            const container = document.querySelector('.row.q-mb-md.q-col-gutter-md') as HTMLElement
            if (container) {
              // 保存原始 display 值
              const originalDisplay = container.style.display
              
              // 通过快速切换 display 属性来触发重排
              container.style.display = 'none'
              // 强制浏览器重新计算布局
              void container.offsetHeight  // 触发回流
              // 恢复原来的 display 值
              container.style.display = originalDisplay || 'flex'
              
              // 额外处理：确保 col-6 类正确应用
              const cols = container.querySelectorAll('.col-6')
              cols.forEach(col => {
                // 重新应用 col-6 类的 flex 属性
                const element = col as HTMLElement
                element.style.flex = '0 0 50%'
                element.style.maxWidth = '50%'
              })
            }
            
            // 最终确认整体布局同步
            window.requestAnimationFrame(() => {
              syncContainerHeights()
            })
          })
        })
      }
    }

    // 添加用于context的变量
    const contextData = ref<ContextItem[]>([])
    const contextType = computed(() => {
      const typeItem = contextData.value.find((item) => item.type)
      return typeItem ? typeItem.type : 'NULL'
    })
    const contextName = computed(() => {
      const nameItem = contextData.value.find((item) => item.name)
      return nameItem ? nameItem.name : 'NULL'
    })
    // 添加用于编辑context的变量
    const contextTypeEdit = ref('')
    const contextNameEdit = ref('')
    // 添加type选项列表
    const typeOptionsList = ref<string[]>(typeOptions.type)
    // 添加name选项列表
    const nameOptionsList = ref<string[]>(typeOptions.name)

    // 添加过滤type选项的方法
    const filterTypeOptions = (val: string, update: (callback: () => void) => void) => {
      if (val === '') {
        update(() => {
          typeOptionsList.value = typeOptions.type
        })
        return
      }

      update(() => {
        const needle = val.toLowerCase()
        typeOptionsList.value = typeOptions.type.filter(
          v => v.toLowerCase().indexOf(needle) > -1
        )
      })
    }
    
    // 添加失去焦点时处理新值的方法
    const onTypeBlur = (e: Event) => {
      // 将Event类型转换为HTMLInputElement
      const target = e.target as HTMLInputElement;
      if (target && target.value && !typeOptionsList.value.includes(target.value)) {
        // 如果输入的值不在选项列表中，将其添加到选项列表
        if (!typeOptionsList.value.includes(target.value)) {
          typeOptionsList.value.push(target.value);
        }
        // 将输入的值设置为当前选中值
        contextTypeEdit.value = target.value;
      }
    }

    // 添加过滤name选项的方法
    const filterNameOptions = (val: string, update: (callback: () => void) => void) => {
      if (val === '') {
        update(() => {
          nameOptionsList.value = typeOptions.name
        })
        return
      }

      update(() => {
        const needle = val.toLowerCase()
        nameOptionsList.value = typeOptions.name.filter(
          v => v.toLowerCase().indexOf(needle) > -1
        )
      })
    }
    
    // 添加失去焦点时处理新值的方法
    const onNameBlur = (e: Event) => {
      // 将Event类型转换为HTMLInputElement
      const target = e.target as HTMLInputElement;
      if (target && target.value && !nameOptionsList.value.includes(target.value)) {
        // 如果输入的值不在选项列表中，将其添加到选项列表
        if (!nameOptionsList.value.includes(target.value)) {
          nameOptionsList.value.push(target.value);
        }
        // 将输入的值设置为当前选中值
        contextNameEdit.value = target.value;
      }
    }

    // 添加pmid变量
    const pmid = ref('')

    // 定义自定义事件的类型接口
    interface GraphDataUpdatedEvent extends CustomEvent {
      detail: {
        pmid: string;
        username: string;
        mode: string;
        timestamp: number;
      }
    }

    // 添加图表数据更新事件监听函数
    const handleGraphDataUpdated = async (event: GraphDataUpdatedEvent) => {
      console.log('图表数据已更新，正在刷新分析结果...', event.detail);
      
      // 显示加载提示
      $q.notify({
        message: 'Synchronizing analysis results...',
        color: 'accent',
        position: 'top',
        timeout: 2000
      });
      
      // 重新获取数据
      await fetchData();

      // 显示同步成功提示
      $q.notify({
        message: 'Synchronization completed successfully',
        color: 'positive',
        position: 'top',
        timeout: 1000
      });

    };

    // 在组件挂载时添加事件监听器
    onMounted(() => {
      window.addEventListener('graph-data-updated', handleGraphDataUpdated as unknown as EventListener);
    });
    
    // 在组件卸载时移除事件监听器
    onUnmounted(() => {
      window.removeEventListener('graph-data-updated', handleGraphDataUpdated as unknown as EventListener);
    });

    // 添加计算属性用于tooltip文本
    const editTooltipText = computed(() => {
      if (currentUser.value.username === 'Admin' && route.query.mode === 'view') {
        return 'View mode, cannot edit'
      }
      return 'Only the owner user can edit'
    })

    // 添加返回按钮相关的计算属性
    const backButtonTooltip = computed(() => {
      return currentUser.value.username === 'Admin' ? 
        'Back To Curated Papers Page' : 
        'Back To Management Page'
    })

    const handleBackClick = () => {
      if (currentUser.value.username === 'Admin') {
        router.push('/curated-papers')
      } else {
        router.push('/management')
      }
    }

    // 添加获取实体类型和名称的方法
    const getEntityInfo = (entityName: string) => {
      console.log('获取实体信息:', entityName, entities.value[entityName])
      
      if (!entities.value || !entities.value[entityName] || !Array.isArray(entities.value[entityName])) {
        return 'NULL，NULL'
      }
      
      const entityInfo = entities.value[entityName]
      const type = entityInfo[0] || 'NULL'
      const name = entityInfo[1] || 'NULL'
      
      return `${type}，${name}`
    }

    // 在setup函数中添加新的数据变量
    const nodesOptionsList = ref<string[]>(nodesRelationsData.nodes)
    const relationsOptionsList = ref<string[]>(nodesRelationsData.relations)

    // 添加节点过滤方法
    const filterNodesOptions = (val: string, update: (callback: () => void) => void) => {
      if (val === '') {
        update(() => {
          nodesOptionsList.value = nodesRelationsData.nodes
        })
        return
      }

      update(() => {
        const needle = val.toLowerCase()
        nodesOptionsList.value = nodesRelationsData.nodes.filter(
          v => v.toLowerCase().indexOf(needle) > -1
        )
      })
    }

    // 添加关系过滤方法
    const filterRelationsOptions = (val: string, update: (callback: () => void) => void) => {
      if (val === '') {
        update(() => {
          relationsOptionsList.value = nodesRelationsData.relations
        })
        return
      }

      update(() => {
        const needle = val.toLowerCase()
        relationsOptionsList.value = nodesRelationsData.relations.filter(
          v => v.toLowerCase().indexOf(needle) > -1
        )
      })
    }

    // 修改节点失焦处理方法
    const onNodeBlur = (e: Event, row: TableRow, field: 'head' | 'tail') => {
      const target = e.target as HTMLInputElement
      if (target && target.value) {
        // 如果输入的值不在选项列表中，将其添加到选项列表
        if (!nodesOptionsList.value.includes(target.value)) {
          nodesOptionsList.value.push(target.value)
        }
        // 将输入的值设置为当前选中值
        row[field] = target.value
      }
    }

    // 添加关系失焦处理方法
    const onRelationBlur = (e: Event, row: TableRow) => {
      const target = e.target as HTMLInputElement
      if (target && target.value) {
        // 如果输入的值不在选项列表中，将其添加到选项列表
        if (!relationsOptionsList.value.includes(target.value)) {
          relationsOptionsList.value.push(target.value)
        }
        // 将输入的值设置为当前选中值
        row.label = target.value
      }
    }

    return {
      paperUrl,
      title,
      abstract,
      tableData,
      columns,
      selectedRow,
      onRowClick,
      onCellFocus,
      isLoading,
      handleSubmit,
      fetchBasicData,
      fetchAnalysisData,
      highlightedAbstract,
      visualizationUrl,
      isExpandable,
      toggleExpand,
      isExpanded,
      expandedRows,
      isEditing,
      submitEdits,
      cancelEdits,
      startEditing,
      addMetaRelation,
      removeMetaRelation,
      addRelation,
      removeRelation,
      restoreRelation,
      currentUser,
      completeAnalysis,
      isOwner,
      showCompleteButton,
      graphUpdateKey,
      confirmReset,
      isResponseView,
      analysisText,
      toggleView,
      contextData,
      contextType,
      contextName,
      contextTypeEdit,
      contextNameEdit,
      typeOptionsList,
      filterTypeOptions,
      onTypeBlur,
      nameOptionsList,
      filterNameOptions,
      onNameBlur,
      pmid,
      handleGraphDataUpdated,
      editTooltipText,
      backButtonTooltip,
      handleBackClick,
      fetchEntitiesData,
      getEntityInfo,
      entities,
      nodesOptionsList,
      relationsOptionsList,
      filterNodesOptions,
      filterRelationsOptions,
      onNodeBlur,
      onRelationBlur,
      getRowClass,
      onRowHover,
      onRowLeave,
      handlePageClick,
      abstractText,
      toggleNotePopup,
      extractionTime,
      extractionTimeSize,
      urlInputSize,
      notes,
      saveNotes,
      loadNotes,
      // 添加撤销/重做相关函数到返回对象
      undo,
      redo,
      historyStack,
      redoStack,
      recordCurrentState, // 添加recordCurrentState方法到返回对象
      // 添加新的图形视图状态和方法
      isGraphView,
      toggleGraphView,
      showBottomGraph,
    }
  },
})
</script>

<style lang="scss" scoped>
.q-page {
  --tooltip-font-size: 30px;
}

// 添加tooltip样式
:deep(.custom-tooltip) {
  white-space: nowrap !important;
  font-size: 14px !important;
  padding: 4px 8px !important;
  width: max-content !important;
  text-align: center !important;
  background: rgba(0, 0, 0, 0.8) !important;
}

// 添加新header容器的样式
.new-header-section {
  height: 45px; /* 增加高度从30px到45px */
  display: flex;
  align-items: center;
  padding: 16px 16px; /* 增加顶部padding从8px到16px */
  font-weight: bold;
  background-color: white;
  border: 1px solid #2196f3; /* 添加蓝色边框 */
  border-radius: 4px; /* 添加圆角 */
  margin-bottom: 0; /* 移除底部间距 */
  border-bottom: none; /* 移除底部边框 */
  
  /* 添加context编辑输入框样式 */
  .context-edit-input {
    width: 100%;
    margin-top: 8px; /* 添加上边距确保两个输入框垂直对齐 */
    
    :deep(.q-field__control) {
      height: 36px; /* 统一高度 */
      padding: 0 8px;
    }
    
    :deep(.q-field__native) {
      text-align: center;
      font-weight: bold;
      font-size: 14px; /* 统一字体大小 */
      color: #000; /* 统一字体颜色 */
      font-family: inherit; /* 保持字体系列一致 */
    }
    
    /* 设置选择项的样式 */
    :deep(.q-field__input) {
      text-align: center !important;
      font-weight: bold !important;
      font-size: 14px !important;
      color: #000 !important;
    }
    
    /* 确保下拉框和输入框一致 */
    :deep(.q-field__append) {
      height: 36px;
      padding-top: 0;
      padding-bottom: 0;
    }
  }
  
  /* 确保Type和Name输入框相同的样式 */
  .col-6:first-child .context-edit-input, .col-6:nth-child(2) .context-edit-input {
    /* 统一输入框内文本样式 */
    :deep(input) {
      text-align: center !important;
      font-weight: bold !important;
      font-size: 14px !important;
      color: #000 !important;
    }
    
    /* 统一标签样式 */
    :deep(.q-field__label) {
      font-size: 12px !important;
      font-weight: normal !important;
    }
  }
  
  /* 隐藏Type输入框的光标 */
  .col-6:first-child .context-edit-input {
    /* 确保整个区域的鼠标样式都是指针，但输入时恢复文本光标 */
    :deep(.q-field) {
      cursor: pointer !important;
    }
    
    /* 调整清除按钮X的大小 */
    :deep(.q-field__focusable-action) {
      font-size: 14px !important; /* 减小X符号的大小 */
      opacity: 0.7; /* 稍微降低不透明度 */
      margin-right: 4px; /* 提供一些右侧间距 */
      
      i.material-icons, i.q-icon {
        font-size: 18px !important; /* 确保图标大小一致 */
      }
    }
    
    :deep(.q-field__native) {
      caret-color: black; /* 恢复输入时的光标 */
      cursor: text; /* 恢复输入时的文本光标 */
      user-select: text; /* 确保文本可选 */
      font-weight: bold; /* 保持与Name一致的字体粗细 */
    }
    
    /* 设置下拉菜单中的项目字体样式 */
    :deep(.q-item) {
      font-size: inherit;
      font-weight: normal;
    }
    
    :deep(input) {
      cursor: text !important; /* 输入区域使用文本光标 */
      user-select: text; /* 确保文本可选 */
    }
    
    :deep(input:focus) {
      cursor: text !important; /* 聚焦时确保是文本光标 */
    }
    
    /* 确保其他元素的鼠标样式一致 */
    :deep(.q-field__control), 
    :deep(.q-field__marginal),
    :deep(.q-field__control-container),
    :deep(.q-field__label) {
      cursor: pointer !important;
    }
    
    /* 调整聚焦时的蓝色边框 */
    :deep(.q-field--focused) {
      .q-field__control {
        box-shadow: 0 0 0 2px #2196f3; /* 添加更明显的聚焦边框 */
        height: 42px !important; /* 确保聚焦时高度足够 */
      }
    }
    
    /* 调整下拉三角形的位置，使其垂直居中 */
    :deep(.q-field__append) {
      height: 36px;
      padding-top: 0;
      padding-bottom: 0;
      align-items: center; /* 确保内容垂直居中 */
      cursor: pointer !important; /* 确保鼠标样式为指针 */
      
      .q-icon {
        margin-top: 15px !important; /* 向下移动15px */
        align-self: center; /* 确保图标自身居中 */
        cursor: pointer !important; /* 确保鼠标样式为指针 */
      }
    }
    
    /* 保证初始高度与聚焦时相同 */
    :deep(.q-field__control) {
      height: 42px !important; /* 与聚焦时相同的高度 */
    }
  }

  /* 添加Name输入框的样式以匹配Type */
  .col-6:nth-child(2) .context-edit-input {
    /* 确保整个区域的鼠标样式都是指针，但输入时恢复文本光标 */
    :deep(.q-field) {
      cursor: pointer !important;
    }
    
    /* 调整清除按钮X的大小 */
    :deep(.q-field__focusable-action) {
      font-size: 14px !important; /* 减小X符号的大小 */
      opacity: 0.7; /* 稍微降低不透明度 */
      margin-right: 4px; /* 提供一些右侧间距 */
      
      i.material-icons, i.q-icon {
        font-size: 18px !important; /* 确保图标大小一致 */
      }
    }
    
    :deep(.q-field__native) {
      caret-color: black; /* 恢复输入时的光标 */
      cursor: text; /* 恢复输入时的文本光标 */
      user-select: text; /* 确保文本可选 */
      font-weight: bold; /* 保持与Type一致的字体粗细 */
    }
    
    /* 设置下拉菜单中的项目字体样式 */
    :deep(.q-item) {
      font-size: inherit;
      font-weight: normal;
    }
    
    :deep(input) {
      cursor: text !important; /* 输入区域使用文本光标 */
      user-select: text; /* 确保文本可选 */
    }
    
    :deep(input:focus) {
      cursor: text !important; /* 聚焦时确保是文本光标 */
    }
    
    /* 确保其他元素的鼠标样式一致 */
    :deep(.q-field__control), 
    :deep(.q-field__marginal),
    :deep(.q-field__control-container),
    :deep(.q-field__label) {
      cursor: pointer !important;
    }
    
    /* 调整聚焦时的蓝色边框 */
    :deep(.q-field--focused) {
      .q-field__control {
        box-shadow: 0 0 0 2px #2196f3; /* 添加更明显的聚焦边框 */
        height: 42px !important; /* 确保聚焦时高度足够 */
      }
    }
    
    /* 调整下拉三角形的位置，使其垂直居中 */
    :deep(.q-field__append) {
      height: 36px;
      padding-top: 0;
      padding-bottom: 0;
      align-items: center; /* 确保内容垂直居中 */
      cursor: pointer !important; /* 确保鼠标样式为指针 */
      
      .q-icon {
        margin-top: 15px !important; /* 向下移动15px */
        align-self: center; /* 确保图标自身居中 */
        cursor: pointer !important; /* 确保鼠标样式为指针 */
      }
    }
    
    /* 保证初始高度与聚焦时相同 */
    :deep(.q-field__control) {
      height: 42px !important; /* 与聚焦时相同的高度 */
    }
  }
  
  /* 专门增加Name输入框的高度 */
  .col-6:nth-child(2) .context-edit-input {
    :deep(.q-field__control) {
      height: 40px; /* 增加Name输入框高度 */
    }
  }
  
  /* 调整左右两个容器垂直对齐 */
  .row.full-width {
    align-items: center;
  }
}

// 移除表格上方的边框
.no-border-top {
  border-top: none !important;
}

// 为整个页面添加一个蓝线移除规则
:deep(.q-card__section + .q-card__section) {
  border-top: 1px solid transparent !important;
}

// Add new container styles
.abstract-container {
  height: auto;
  min-height: 400px;
}

.analysis-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 确保外层容器不滚动 */
}

.analysis-scroll {
  overflow-y: auto;
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  position: relative; /* 添加相对定位 */
  height: calc(100% - 45px); /* 减去新添加容器的高度(45px) */
  margin-top: 0; /* 移除上边距，使元组容器紧贴标题 */

  // Custom scrollbar styles
  &::-webkit-scrollbar {
    width: 8px;
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

  // 添加新的样式来控制按钮组的位置
  .q-table {
    flex: 1;
    margin-bottom: 16px;
    
    // 为表格内容添加足够的底部内边距，确保最后一个元组的编辑区域不被按钮栏遮挡
    tbody {
      padding-bottom: 120px; /* 增加底部内边距，确保展开内容不被按钮遮挡 */
      
      // 为最后一个展开的元组添加额外的底部边距
      tr:last-child .meta-relations {
        margin-bottom: 100px; /* 增加最后一个元组的底部边距 */
      }
    }
  }

  .row.justify-center {
    margin-top: auto;
    padding-top: 8px; /* 减小顶部内边距 */
    padding-bottom: 8px; /* 减小底部内边距 */
    border-top: 1px solid rgba(0, 0, 0, 0.12);
    position: sticky;
    bottom: 10px; /* 下移10px */
    background-color: white;
    z-index: 10; /* 增加z-index确保在内容之上 */
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05); /* 添加上阴影增强视觉分隔 */
    border-bottom-left-radius: 8px; /* 添加底部圆角 */
    border-bottom-right-radius: 8px; /* 添加底部圆角 */
  }
}

.analysis-table {
  height: 100%;
}

// 编辑状态下的表格样式
.editing-table {
  overflow-y: auto !important;
  
  // 在编辑状态下，为展开的元组添加更多底部空间
  .meta-relations {
    padding-bottom: 30px;
  }
  
  // 确保最后一行有足够空间
  tbody tr:last-child {
    margin-bottom: 120px;
  }
}

// 非编辑状态下的表格样式，确保滚动行为与编辑状态类似
.analysis-table {
  overflow-y: auto !important;
}

.meta-relation-row {
  position: relative;
  z-index: 1;
  
  // 添加样式确保展开内容完全显示
  .meta-relations {
    position: relative;
    z-index: 2;
    background-color: rgba(0, 0, 0, 0.02);
    border-radius: 4px;
    transition: all 0.3s ease;
    padding: 16px;
    margin: 8px 0;
    
    // 移除max-height限制
    // max-height: 400px;
    height: auto;
    overflow: visible;
    
    // 确保内容不被截断
    .q-markup-table {
      margin-bottom: 16px;
      
      // 调整表格内容样式
      td, th {
        padding: 8px;
        white-space: normal;
        word-break: break-word;
      }
    }
  }
}

// 修改滚动容器样式
.analysis-scroll {
  overflow-y: auto;
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  position: relative;
  height: calc(100% - 45px);
  margin-top: 0;

  // 确保展开内容可见
  .q-table {
    overflow: visible !important;
    
    // 调整表格容器样式
    tbody {
      tr {
        position: relative;
        
        // 确保展开行正确显示
        &.meta-relation-row {
          td {
            position: relative;
            background: white;
          }
        }
      }
    }
  }
}

// 添加展开动画
.meta-relations {
  transform-origin: top;
  animation: expand 0.3s ease;
}

@keyframes expand {
  from {
    opacity: 0;
    transform: scaleY(0);
  }
  to {
    opacity: 1;
    transform: scaleY(1);
  }
}

.abstract {
  line-height: 1.8;
  text-align: justify;
  white-space: pre-line;

  :deep(.highlighted) {
    background-color: rgba(255, 152, 0, 0.7);
    transition: background-color 0.3s ease;
    position: relative;
    z-index: 2;
  }

  :deep(.hover-highlighted) {
    background-color: rgba(255, 152, 0, 0.2);
    transition: background-color 0.3s ease;
    position: relative;
    z-index: 2;
  }
}

.full-height {
  height: 100%;
}

.q-table td {
  padding: 0 !important;
}

.q-input {
  padding: 8px;
  width: 100%;
}

.q-tr {
  transition: background-color 0.3s ease;
}

.visualization-container {
  width: 100%;
  height: 600px;
  border-radius: 8px;
}

.visualization-frame {
  width: 100%;
  height: 100%;
  border: none;
  border-radius: 8px;
}

// 确保标题在最上层
.text-h6 {
  background-color: transparent;
}

.q-table {
  td {
    text-align: center !important;
  }

  th {
    text-align: center !important;
  }

  .expandable-row {
    cursor: pointer;
  }

  .meta-relations {
    background-color: rgba(0, 0, 0, 0.03);
    padding: 8px;
  }
}

.meta-relations {
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
  transition: all 0.3s ease;
  // 当在编辑模式时为meta-relations添加更多的底部边距
  padding-bottom: 16px;

  .meta-relation-item {
    padding: 8px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);

    &:last-child {
      border-bottom: none;
    }

    .text-weight-medium {
      font-weight: 500;
    }
  }
}

// 编辑状态下的元组展开区域
.isEditing .meta-relations {
  margin-bottom: 40px; /* 编辑状态下增加底部间距 */
}

.cursor-pointer {
  cursor: pointer;
}

.expand-button {
  opacity: 0.7;
  &:hover {
    opacity: 1;
  }
}

.meta-relations {
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
  transition: all 0.3s ease;
  // 当在编辑模式时为meta-relations添加更多的底部边距
  padding-bottom: 16px;

  .meta-relation-item {
    padding: 8px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);

    &:last-child {
      border-bottom: none;
    }

    .text-weight-medium {
      font-weight: 500;
    }
  }
}

.q-input {
  .q-field__native {
    text-align: center;
  }
}

.relation-add-btn,
.meta-add-btn {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  background-color: var(--q-primary) !important;
  color: white !important;
  border: none;
  transition: all 0.3s ease;

  &:hover:not(.disabled-btn) {
    transform: scale(1.05);
    opacity: 0.9;
  }
  
  &:active:not(.disabled-btn) {
    transform: translateY(0); /* 点击时回到原位 */
  }
}

.meta-add-btn {
  vertical-align: middle;
}

// Add styles for the table footer
.q-table tbody td,
.q-table tbody th {
  padding: 4px;
}

tfoot td {
  border-top: 1px solid rgba(0, 0, 0, 0.12);
  padding: 4px !important;
}

// 增加底部区域的上边距
.q-mt-xxl {
  margin-top: 72px !important;
}

.text-input {
  .q-field {
    background: white;
  }
}

.supporting-text-container {
  width: 100%;
  position: relative;
}

.supporting-text-input {
  :deep(.q-field__control) {
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
    
    textarea {
      height: 100% !important;
      overflow: auto !important;
      overflow-y: visible !important;
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

.supporting-text-display {
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 4px;
  padding: 10px;
  max-height: 100px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: break-word;
  
  /* 自定义滚动条样式 */
  &::-webkit-scrollbar {
    width: 8px;
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

.text-display {
  background: rgba(0, 0, 0, 0.02);
  padding: 8px;
  border-radius: 4px;
}

.q-icon {
  font-size: 28px !important;
  opacity: 0.7;
  transition: all 0.3s ease;

  :deep(.q-tooltip.q-tooltip--style) {
    font-size: 20px !important;
    * {
      font-size: 20px !important;
    }
  }

  &:hover {
    color: var(--q-primary);
    opacity: 1;
  }
}

// 添加更高优先级的 tooltip 样式
:deep(.q-tooltip.q-tooltip--style) {
  font-size: 14px !important;
  background-color: #707070 !important;
  padding: 8px 12px !important;
}

// 固定显示的菜单样式
:deep(.q-menu.note-popup) {
  background: #f5f5f5 !important; // 改为浅灰色背景
  font-size: 18px !important; // 增大字体
  max-width: 300px !important;
  padding: 16px !important;
  white-space: pre-wrap;
  color: #333 !important; // 深色文字，提高可读性
  min-width: 250px;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);

  .note-content {
    position: relative;
    padding-top: 12px; // 从24px减半为12px
  }

  .note-header {
    position: absolute;
    top: -12px;
    right: -12px;
    z-index: 1;
    text-align: right;
    width: 100%;
    display: flex;
    justify-content: flex-end;

    .q-btn {
      color: #333 !important;
      opacity: 0.7;
      padding: 4px;
      min-height: 24px;
      min-width: 24px;
      font-size: 15px;
      margin-left: auto;

      &:hover {
        opacity: 1;
      }
    }
  }
}

// 将 note-body 样式提取出来，并增加选择器优先级
:deep(.q-menu.note-popup .note-body) {
  font-size: 24px !important;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  color: white !important;
  background-color: rgba(0, 0, 0, 0.8) !important;
  padding: 0 15px;
  border-radius: 4px;
  margin-top: 4px; // 从8px减半为4px
  max-height: 100px; // 设置为与Supporting Text相同的高度
  overflow-y: auto; // 添加垂直滚动功能
  padding-bottom: 15px; // 增加底部内边距
}

/* 表格展开区域的Note区域样式统一 */
.text-input textarea, .text-input .q-field__native {
  background-color: rgba(0, 0, 0, 0.03) !important;
  border-radius: 4px !important;
  padding: 10px !important;
  min-height: 100px !important;
  max-height: 100px !important;
  overflow-y: auto !important;
  white-space: pre-wrap !important;
  word-wrap: break-word !important;
  word-break: break-word !important;
}

/* 确保note-textarea的高度和样式一致 */
.note-textarea {
  :deep(.q-field__control) {
    height: 100px !important;
    min-height: 100px !important;
    max-height: 100px !important;
    background-color: rgba(0, 0, 0, 0.03) !important;
  }
  
  :deep(.q-field__native) {
    height: 100px !important;
    min-height: 100px !important;
    resize: none !important;
  }
}

/* 标题样式统一 */
.text-subtitle2 {
  font-size: 16px !important;
  font-weight: 500 !important;
  margin-bottom: 8px !important;
  color: rgba(0, 0, 0, 0.8) !important;
}

/* Supporting Text和Note区域的容器统一样式 */
.supporting-text-display, .note-display {
  background-color: rgba(0, 0, 0, 0.03) !important;
  border-radius: 4px !important;
  padding: 10px !important;
  min-height: 100px !important;
  max-height: 100px !important;
  overflow-y: auto !important;
  white-space: pre-wrap !important;
  word-wrap: break-word !important;
  word-break: break-word !important;
  display: block !important;
  box-sizing: border-box !important;
}

.url-input {
  :deep(.q-field__label) {
    font-size: v-bind(urlInputSize + 'px');
  }
  :deep(.q-field__native) {
    font-size: v-bind(urlInputSize + 'px');
  }
  :deep(.q-field__marginal) {
    font-size: v-bind(urlInputSize + 'px');
  }
}

// 修改高亮样式的实现
:deep(.q-table) {
  tbody {
    tr.bg-yellow-2 {
      background-color: rgba(255, 193, 7, 0.05) !important; // 提高不透明度到 5%
    }
  }
}

.back-btn {
  :deep(.custom-tooltip) {
    font-size: 18px !important;
    background-color: #707070 !important;
    padding: 8px 12px !important;
  }
}

.disabled-btn {
  opacity: 0.6;
  cursor: not-allowed !important;
  
  &:hover {
    transform: none !important;
    box-shadow: none !important;
  }
}

:deep(.text-size-18) {
  font-size: 18px !important;
}

.view-switch-btn {
  font-size: 14px;
  line-height: 1;
  height: 32px;
  padding: 0 12px;
  
  :deep(.q-btn__content) {
    text-transform: none; /* 避免自动大写 */
    display: flex;
    align-items: center;
    font-size: 14px !important;
  }
  
  .q-icon {
    font-size: 14px !important; /* 添加!important确保样式优先应用 */
  }
}

.view-graph-btn {
  :deep(.q-btn__content) {
    font-size: 14px !important;
  }
  .q-icon {
    font-size: 14px !important;
  }
}

.view-response-btn {
  :deep(.q-btn__content) {
    font-size: 14px !important;
  }
  .q-icon {
    font-size: 14px !important;
  }
}

.response-view {
  background-color: white;
  color: black;
  font-size: 14px;
  line-height: 1.6;
  height: 100%;
  overflow-y: auto;
}

.no-overflow {
  overflow: visible !important;
}

/* 添加按钮样式 */
.q-btn.q-mx-sm {
  height: 34px; /* 减小按钮高度 */
  min-width: 100px; /* 减小按钮宽度 */
  font-size: 14px; /* 减小字体大小 */
  font-weight: 500; /* 稍微加粗字体 */
  margin: 0 8px !important; /* 减小按钮之间的间距 */
  transition: transform 0.2s ease, box-shadow 0.2s ease; /* 添加过渡效果 */
  border-radius: 6px; /* 调整圆角 */
  
  &:hover:not(.disabled-btn) {
    transform: translateY(-2px); /* 悬停时轻微上浮 */
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1); /* 悬停时添加阴影 */
  }
  
  &:active:not(.disabled-btn) {
    transform: translateY(0); /* 点击时回到原位 */
  }
}

/* 为不同类型的按钮添加特定样式 */
.complete-btn {
  font-weight: 600 !important; /* 完成按钮文字更粗 */
}

/* 添加禁用输入框的样式 */
.disabled-input {
  opacity: 0.8;
  cursor: not-allowed !important;
  
  :deep(.q-field__native) {
    color: #707070 !important;
  }
  
  :deep(.q-field__control) {
    background-color: #f0f0f0 !important;
  }

  :deep(textarea) {
    cursor: not-allowed !important;
  }
}

/* 为非编辑状态下的字段添加边框样式 */
.context-display-field {
  font-size: 18px;
  border: 1px solid #2196f3;
  border-radius: 4px;
  padding: 8px 12px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: white;
  font-weight: bold;
}

/* 统一的显示容器，一个框包含Type和Name */
.unified-context-display {
  font-size: 18px;
  border: 1px solid #9e9e9e; /* 灰色边框 */
  border-radius: 4px;
  padding: 8px 12px;
  min-height: 42px;
  display: flex;
  align-items: center;
  background-color: white;
  font-weight: bold;
  width: 100%;
  margin-top: 16px; /* 增加上边距 */
}

.unified-context-display .field-text {
  font-size: 18px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

/* 编辑状态下的输入容器 */
.edit-inputs-container {
  margin-top: 16px; /* 与非编辑状态保持一致的上边距 */
  width: 100%;
}

.wide-tooltip {
  max-width: 500px !important;
}

/* 添加全局选择器以强制设置宽tooltip样式 */
:deep(.wide-tooltip) {
  min-width: 300px !important;
  max-width: 500px !important;
}

/* 为tooltip添加更高优先级的CSS规则 */
:global(.body--light .wide-tooltip) {
  min-width: 300px !important;
  max-width: 500px !important;
}

/* 直接针对Quasar的tooltip组件设置样式 */
:deep(.q-tooltip.wide-tooltip) {
  min-width: 300px !important;
  max-width: 500px !important;
}

/* 使用非常高优先级的选择器 */
body .q-tooltip.wide-tooltip,
html body .q-tooltip.wide-tooltip,
:deep(html body .q-tooltip.wide-tooltip) {
  min-width: 300px !important;
  max-width: 500px !important;
}

/* 全局覆盖所有的Quasar tooltip样式 */
:root {
  --q-tooltip-min-width: 300px !important;
  --q-tooltip-max-width: 500px !important;
}

.q-tooltip, 
body .q-tooltip,
html .q-tooltip,
#q-app .q-tooltip {
  min-width: 300px !important;
  max-width: 500px !important;
  width: auto !important;
}

/* 添加笔记框的强制样式 */
.note-popup {
  min-width: 300px !important;
  max-width: 500px !important;
}

:deep(.note-popup) {
  min-width: 300px !important;
  max-width: 500px !important;
}

/* 高优先级选择器 */
body .note-popup,
html .note-popup,
#q-app .note-popup {
  min-width: 300px !important;
  max-width: 500px !important;
}

/* 表头样式增强 */
:deep(.q-table thead th) {
  font-size: 16px !important;
  font-weight: bold !important;
  padding-top: 12px !important;
  padding-bottom: 12px !important;
  vertical-align: middle !important;
  text-align: center !important;
}

/* 表头位置微调 - 可以调整下面的像素值来手动控制位置 */
:deep(.q-table thead th:nth-child(2)) { /* Head列 */
  padding-right: 40px !important; /* 向左偏移，增加此值使其更靠左 */
}

:deep(.q-table thead th:nth-child(4)) { /* Tail列 */
  padding-left: 40px !important; /* 向右偏移，增加此值使其更靠右 */
}

/* 隐藏Type输入框的光标 */
.col-6:first-child .context-edit-input {
  /* 确保整个区域的鼠标样式都是指针，但输入时恢复文本光标 */
  :deep(.q-field) {
    cursor: pointer !important;
  }
  
  /* 调整清除按钮X的大小 */
  :deep(.q-field__focusable-action) {
    font-size: 14px !important; /* 减小X符号的大小 */
    opacity: 0.7; /* 稍微降低不透明度 */
    margin-right: 4px; /* 提供一些右侧间距 */
    
    i.material-icons, i.q-icon {
      font-size: 18px !important; /* 确保图标大小一致 */
    }
  }
  
  :deep(.q-field__native) {
    caret-color: black; /* 恢复输入时的光标 */
    cursor: text; /* 恢复输入时的文本光标 */
    user-select: text; /* 确保文本可选 */
    font-weight: bold; /* 保持与Name一致的字体粗细 */
  }
  
  /* 设置下拉菜单中的项目字体样式 */
  :deep(.q-item) {
    font-size: inherit;
    font-weight: normal;
  }
  
  :deep(input) {
    cursor: text !important; /* 输入区域使用文本光标 */
    user-select: text; /* 确保文本可选 */
  }
  
  :deep(input:focus) {
    cursor: text !important; /* 聚焦时确保是文本光标 */
  }
  
  /* 确保其他元素的鼠标样式一致 */
  :deep(.q-field__control), 
  :deep(.q-field__marginal),
  :deep(.q-field__control-container),
  :deep(.q-field__label) {
    cursor: pointer !important;
  }
  
  /* 调整聚焦时的蓝色边框 */
  :deep(.q-field--focused) {
    .q-field__control {
      box-shadow: 0 0 0 2px #2196f3; /* 添加更明显的聚焦边框 */
      height: 42px !important; /* 确保聚焦时高度足够 */
    }
  }
  
  /* 调整下拉三角形的位置，使其垂直居中 */
  :deep(.q-field__append) {
    height: 36px;
    padding-top: 0;
    padding-bottom: 0;
    align-items: center; /* 确保内容垂直居中 */
    cursor: pointer !important; /* 确保鼠标样式为指针 */
    
    .q-icon {
      margin-top: 15px !important; /* 向下移动15px */
      align-self: center; /* 确保图标自身居中 */
      cursor: pointer !important; /* 确保鼠标样式为指针 */
    }
  }
  
  /* 保证初始高度与聚焦时相同 */
  :deep(.q-field__control) {
    height: 42px !important; /* 与聚焦时相同的高度 */
  }
}

/* 添加Name输入框的样式以匹配Type */
.col-6:nth-child(2) .context-edit-input {
  /* 确保整个区域的鼠标样式都是指针，但输入时恢复文本光标 */
  :deep(.q-field) {
    cursor: pointer !important;
  }
  
  /* 调整清除按钮X的大小 */
  :deep(.q-field__focusable-action) {
    font-size: 14px !important; /* 减小X符号的大小 */
    opacity: 0.7; /* 稍微降低不透明度 */
    margin-right: 4px; /* 提供一些右侧间距 */
    
    i.material-icons, i.q-icon {
      font-size: 18px !important; /* 确保图标大小一致 */
    }
  }
  
  :deep(.q-field__native) {
    caret-color: black; /* 恢复输入时的光标 */
    cursor: text; /* 恢复输入时的文本光标 */
    user-select: text; /* 确保文本可选 */
    font-weight: bold; /* 保持与Type一致的字体粗细 */
  }
  
  /* 设置下拉菜单中的项目字体样式 */
  :deep(.q-item) {
    font-size: inherit;
    font-weight: normal;
  }
  
  :deep(input) {
    cursor: text !important; /* 输入区域使用文本光标 */
    user-select: text; /* 确保文本可选 */
  }
  
  :deep(input:focus) {
    cursor: text !important; /* 聚焦时确保是文本光标 */
  }
  
  /* 确保其他元素的鼠标样式一致 */
  :deep(.q-field__control), 
  :deep(.q-field__marginal),
  :deep(.q-field__control-container),
  :deep(.q-field__label) {
    cursor: pointer !important;
  }
  
  /* 调整聚焦时的蓝色边框 */
  :deep(.q-field--focused) {
    .q-field__control {
      box-shadow: 0 0 0 2px #2196f3; /* 添加更明显的聚焦边框 */
      height: 42px !important; /* 确保聚焦时高度足够 */
    }
  }
  
  /* 调整下拉三角形的位置，使其垂直居中 */
  :deep(.q-field__append) {
    height: 36px;
    padding-top: 0;
    padding-bottom: 0;
    align-items: center; /* 确保内容垂直居中 */
    cursor: pointer !important; /* 确保鼠标样式为指针 */
    
    .q-icon {
      margin-top: 15px !important; /* 向下移动15px */
      align-self: center; /* 确保图标自身居中 */
      cursor: pointer !important; /* 确保鼠标样式为指针 */
    }
  }
  
  /* 保证初始高度与聚焦时相同 */
  :deep(.q-field__control) {
    height: 42px !important; /* 与聚焦时相同的高度 */
  }
}

/* 专门增加Name输入框的高度 */
.col-6:nth-child(2) .context-edit-input {
  :deep(.q-field__control) {
    height: 40px; /* 增加Name输入框高度 */
  }
}

/* 调整左右两个容器垂直对齐 */
.row.full-width {
  align-items: center;
}

/* 确保所有笔记区域可滚动且高度一致 */
:deep(textarea) {
  max-height: 100px !important;
  overflow-y: auto !important;
}

/* 添加实体文本的样式 */
.entity-text {
  cursor: help;
  position: relative;
}

.entity-tooltip {
  font-size: 14px !important;
  background-color: #707070 !important;
  padding: 8px 12px !important;
  color: white !important;
  max-width: 250px !important;
  white-space: nowrap !important;
  border-radius: 4px !important;
  z-index: 9999 !important;
  box-shadow: 0 1px 5px rgba(0,0,0,0.2) !important;
}

// 添加编辑状态下的输入框样式限制宽度
:deep(.q-table td .q-select) {
  max-width: 130px; /* 限制编辑框的最大宽度 */
  width: 130px; /* 设置固定宽度 */
  margin: 0 auto; /* 水平居中 */
  
  /* 确保内容居中显示 */
  .q-field__native {
    text-align: center;
  }
  
  /* 调整输入框内部padding */
  .q-field__control {
    padding: 0 6px;
  }
  
  /* 确保下拉图标位置合适 */
  .q-field__append {
    padding-right: 4px;
  }
}

/* 添加撤销/重做按钮区域的样式 */
.history-buttons-container {
  position: absolute;
  right: 16px;
  top: 54px; /* 位于Context编辑框下方 */
  z-index: 10;
  display: flex;
  gap: 8px;
  padding: 4px 8px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 表头中的历史按钮样式 */
.history-buttons-row {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding-right: 8px;
}

/* 标题区域的历史按钮样式 */
.history-buttons-title {
  display: flex;
  gap: 10px;  /* 增加按钮间距 */
  align-items: center;
  justify-content: flex-start;
  padding-left: 8px; /* 增加左侧内边距 */
  
  .q-btn {
    font-size: 16px !important; /* 增大图标大小 */
    background-color: #dbeafe !important; /* 蓝色底色 */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important; /* 更明显的阴影 */
    border-radius: 50% !important; /* 确保是圆形 */
    min-width: 32px !important; /* 最小宽度 */
    min-height: 32px !important; /* 最小高度 */
    width: 32px !important; /* 固定宽度 */
    height: 32px !important; /* 固定高度 */
    padding: 0 !important; /* 移除内边距 */
    transition: all 0.2s ease !important; /* 添加过渡效果 */
    margin-top: -2px !important; /* 稍微上移以对齐 */
    
    &:hover {
      transform: scale(1.05) !important; /* 鼠标悬停时略微放大 */
      box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15) !important; /* 悬停时阴影更明显 */
    }
  }
  
  .q-btn[color="negative"] {
    background-color: #e0f2fe !important; /* Undo按钮的浅蓝色 */
  }
  
  .q-btn[color="positive"] {
    background-color: #dbeafe !important; /* Redo按钮的中蓝色 */
  }
}

.history-btn {
  opacity: 0.8;
  transition: all 0.2s ease;

  &:hover {
    opacity: 1;
    transform: translateY(-2px);
  }

  &:active {
    transform: translateY(0);
  }

  &.q-btn--disabled {
    opacity: 0.4;
    pointer-events: none;
  }
}

/* 撤销/重做按钮的tooltip样式 */
.history-btn .q-tooltip {
  font-size: 14px !important;
  background-color: rgba(0, 0, 0, 0.8) !important;
  color: white;
  padding: 4px 8px !important;
}

.view-graph-btn {
  :deep(.q-btn__content) {
    font-size: 14px !important;
  }
  .q-icon {
    font-size: 14px !important;
  }
}

.view-response-btn {
  :deep(.q-btn__content) {
    font-size: 14px !important;
  }
  .q-icon {
    font-size: 14px !important;
  }
}

// 在 style 部分添加 view-text-btn 的样式
.view-text-btn {
  :deep(.q-btn__content) {
    font-size: 18px !important; /* 增大字体以匹配标题 */
    font-weight: bold;
    text-transform: none; /* 避免自动大写 */
  }
  .q-icon {
    font-size: 18px !important; /* 增大图标以匹配字体 */
  }
  margin: 0 auto; /* 确保按钮居中 */
  padding: 8px 16px; /* 增加内边距 */
}
</style>
