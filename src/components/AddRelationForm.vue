<template>
  <div class="add-relation-dialog" @click.stop>
    <div class="dialog-header">
      <div class="dialog-title">Add New Relation</div>
      <q-btn flat round dense icon="close" @click="$emit('cancel')" />
    </div>
    <div class="dialog-content">
      <div class="form-row">
        <q-select
          v-model="formData.head"
          :options="nodesOptionsList"
          label="Head"
          outlined
          dense
          class="form-field"
          placeholder="Entity that is the source"
          use-input
          input-debounce="0"
          @filter="filterNodesOptions"
          @blur="onNodeBlur($event, 'head')"
          hide-selected
          fill-input
          new-value-mode="add-unique"
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
      <div class="form-row">
        <q-select
          v-model="formData.relation"
          :options="relationsOptionsList"
          label="Relation"
          outlined
          dense
          class="form-field"
          placeholder="Relation type"
          use-input
          input-debounce="0"
          @filter="filterRelationsOptions"
          @blur="onRelationBlur"
          hide-selected
          fill-input
          new-value-mode="add-unique"
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
      <div class="form-row">
        <q-select
          v-model="formData.tail"
          :options="nodesOptionsList"
          label="Tail"
          outlined
          dense
          class="form-field"
          placeholder="Entity that is the target"
          use-input
          input-debounce="0"
          @filter="filterNodesOptions"
          @blur="onNodeBlur($event, 'tail')"
          hide-selected
          fill-input
          new-value-mode="add-unique"
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
      <div class="form-row">
        <q-input
          v-model="formData.text"
          label="Supporting Text"
          type="textarea"
          outlined
          class="form-field"
          placeholder="Enter supporting text"
        />
      </div>
      <div class="form-row">
        <q-input
          v-model="formData.note"
          label="Notes"
          type="textarea"
          outlined
          dense
          class="form-field"
          placeholder="Optional notes about this relation"
        />
      </div>
      
      <!-- Meta Relations Section -->
      <div class="meta-relations-section">
        <h3 class="meta-relations-title">Meta Relations</h3>
        
        <div class="meta-relations-table">
          <div class="meta-table-header">
            <div class="meta-header-cell">Target</div>
            <div class="meta-header-cell">Label</div>
            <div class="meta-header-cell meta-action-header"></div>
          </div>
          
          <div class="meta-table-body">
            <template v-if="formData.metaRelations.length === 0">
              <div class="empty-table-add-button">
                <q-btn
                  round
                  color="primary"
                  icon="add"
                  size="md"
                  @click="addMetaRelation"
                >
                  <q-tooltip>Add meta relation</q-tooltip>
                </q-btn>
              </div>
            </template>
            
            <div 
              v-for="(meta, index) in formData.metaRelations" 
              :key="index"
              class="meta-table-row"
            >
              <div class="meta-table-cell">
                <q-input
                  v-model="meta.target"
                  outlined
                  dense
                  class="meta-field"
                  placeholder="Target"
                  hide-bottom-space
                  align="center"
                />
              </div>
              <div class="meta-table-cell">
                <q-input
                  v-model="meta.label"
                  outlined
                  dense
                  class="meta-field"
                  placeholder="Label"
                  hide-bottom-space
                  align="center"
                />
              </div>
              <div class="meta-table-cell meta-action-cell">
                <q-btn
                  flat
                  round
                  dense
                  color="negative"
                  size="xs"
                  class="delete-button"
                  @click="removeMetaRelation(index)"
                >
                  <q-icon name="delete" style="font-size: 16px;" />
                  <q-tooltip>Remove</q-tooltip>
                </q-btn>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="formData.metaRelations.length > 0" class="meta-add-button-container">
          <q-btn
            round
            color="primary"
            icon="add"
            size="md"
            @click="addMetaRelation"
          >
            <q-tooltip>Add meta relation</q-tooltip>
          </q-btn>
        </div>
      </div>
    </div>
    <div class="dialog-footer">
      <q-btn flat label="Cancel" color="grey-7" @click="$emit('cancel')" />
      <q-btn 
        flat 
        label="Add Relation" 
        color="primary" 
        @click="submitForm"
        :disable="!isFormValid"
      />
    </div>
  </div>
</template>

<script>
// 导入实体和关系数据
// import nodesRelationsData from '../../data/nodes_relations_database.json'

export default {
  name: 'AddRelationForm',
  props: {
    supportingText: {
      type: String,
      default: ''
    },
    masterNodes: {
      type: Array,
      default: () => []
    },
    masterRelations: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      formData: {
        head: '',
        relation: '',
        tail: '',
        text: this.supportingText,
        note: '',
        metaRelations: []
      },
      // 选项列表
      nodesOptionsList: [...this.masterNodes],
      relationsOptionsList: [...this.masterRelations]
    }
  },
  watch: {
    masterNodes(newVal) {
      this.nodesOptionsList = [...newVal];
      // If current formData.head is a custom value not in newVal,
      // and q-select is not currently focused/filtering,
      // we might need to ensure it's still in nodesOptionsList.
      // However, q-select with add-unique should handle showing the current value.
      // For filtering purposes, resetting to newVal is correct.
      if (this.formData.head && !newVal.includes(this.formData.head) && !this.nodesOptionsList.includes(this.formData.head)) {
        // Add it back if it was a custom entry and got wiped by master list update.
        // This is a simple way, might need more robust handling if complex interactions occur.
         if (this.$refs.headSelect && this.$refs.headSelect.isBuffering) {
          // do nothing if select is active
         } else {
            this.nodesOptionsList.push(this.formData.head)
         }
      }
    },
    masterRelations(newVal) {
      this.relationsOptionsList = [...newVal];
      if (this.formData.relation && !newVal.includes(this.formData.relation) && !this.relationsOptionsList.includes(this.formData.relation)) {
        if (this.$refs.relationSelect && this.$refs.relationSelect.isBuffering) {
            // do nothing
        } else {
            this.relationsOptionsList.push(this.formData.relation)
        }
      }
    },
    supportingText(newVal) {
      // Update formData.text when the prop changes
      this.formData.text = newVal;
    }
  },
  computed: {
    isFormValid() {
      return this.formData.head.trim() !== '' &&
             this.formData.relation.trim() !== '' &&
             this.formData.tail.trim() !== '';
    }
  },
  methods: {
    // 实体选项过滤方法
    filterNodesOptions(val, update) {
      if (val === '') {
        update(() => {
          this.nodesOptionsList = [...this.masterNodes];
        });
        return;
      }

      update(() => {
        const needle = val.toLowerCase();
        this.nodesOptionsList = this.masterNodes.filter(
          v => v.toLowerCase().indexOf(needle) > -1
        );
      });
    },
    
    // 关系选项过滤方法
    filterRelationsOptions(val, update) {
      if (val === '') {
        update(() => {
          this.relationsOptionsList = [...this.masterRelations];
        });
        return;
      }

      update(() => {
        const needle = val.toLowerCase();
        this.relationsOptionsList = this.masterRelations.filter(
          v => v.toLowerCase().indexOf(needle) > -1
        );
      });
    },
    
    // 处理实体字段失焦事件
    onNodeBlur(event, field) {
      const target = event.target;
      if (target && target.value) {
        // 如果输入的值不在选项列表中，将其添加到选项列表
        if (!this.nodesOptionsList.includes(target.value)) {
          this.nodesOptionsList.push(target.value);
        }
        // 将输入的值设置为当前选中值
        this.formData[field] = target.value;
      }
    },
    
    // 处理关系字段失焦事件
    onRelationBlur(event) {
      const target = event.target;
      if (target && target.value) {
        // 如果输入的值不在选项列表中，将其添加到选项列表
        if (!this.relationsOptionsList.includes(target.value)) {
          this.relationsOptionsList.push(target.value);
        }
        // 将输入的值设置为当前选中值
        this.formData.relation = target.value;
      }
    },
    
    addMetaRelation() {
      this.formData.metaRelations.push({
        target: '',
        label: ''
      });
    },
    removeMetaRelation(index) {
      this.formData.metaRelations.splice(index, 1);
    },
    submitForm() {
      if (this.isFormValid) {
        this.$emit('submit', { ...this.formData });
      }
    }
  },
  emits: ['cancel', 'submit']
}
</script>

<style>
.add-relation-dialog {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 1000px;
  max-width: 95vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.dialog-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.dialog-content {
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.form-row {
  margin-bottom: 16px;
}

.form-field {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid #e0e0e0;
}

.meta-relations-section {
  margin-top: 16px;
  border-top: 1px solid #e0e0e0;
  padding-top: 16px;
}

.meta-relations-title {
  text-align: center;
  font-size: 18px;
  font-weight: 500;
  color: #333;
  margin-bottom: 16px;
}

.meta-relations-table {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 16px;
  border-collapse: collapse;
  table-layout: fixed;
}

.meta-table-header {
  display: flex;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  padding: 12px 16px;
  font-weight: bold;
  width: 100%;
  box-sizing: border-box;
}

.meta-header-cell {
  flex: 1;
  padding: 0 8px;
  font-size: 16px;
  text-align: center;
  border-right: 1px solid #e0e0e0;
  box-sizing: border-box;
}

.meta-header-cell:last-child {
  border-right: none;
}

.meta-action-header {
  flex: 0 0 18px;
  max-width: 18px;
  min-width: 18px;
  padding: 0;
}

.meta-table-body {
  padding: 8px 16px;
  width: 100%;
  box-sizing: border-box;
}

.meta-table-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 8px;
  width: 100%;
}

.meta-table-row:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.meta-table-cell {
  flex: 1;
  padding: 4px 8px;
  text-align: center;
  border-right: 1px solid #e0e0e0;
  box-sizing: border-box;
}

.meta-table-cell:last-child {
  border-right: none;
}

.meta-action-cell {
  flex: 0 0 18px;
  max-width: 18px;
  min-width: 18px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-right: none;
  padding: 0;
  position: relative;
}

.delete-button {
  width: 18px;
  height: 18px;
  min-width: 18px;
  min-height: 18px;
  padding: 0;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  position: relative;
}

.delete-button :deep(.q-icon) {
  position: absolute;
  top: 50%;
  left: calc(50% + 5px);
  transform: translate(-50%, -50%);
}

.delete-button:hover {
  color: #f50057;
}

.delete-button .material-icons {
  transform: scale(1.5);
  transform-origin: center;
}

.meta-add-button-container {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.empty-table-add-button {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px 0;
  width: 100%;
  min-height: 80px;
}

/* 设置input内文本居中 */
.meta-field :deep(.q-field__native) {
  text-align: center;
}
</style> 