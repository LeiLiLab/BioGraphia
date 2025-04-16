<template>
  <div 
    v-if="localShow" 
    class="selection-indicator" 
    :style="{ top: adjustedPosition.y + 'px', left: adjustedPosition.x + 'px' }"
    ref="indicatorRef"
  >
    <!-- 添加图标 -->
    <div v-if="!showPrompt" class="add-icon" @click.stop="showPrompt = true">
      <q-icon name="add_circle" size="16px" />
    </div>
    
    <!-- 提示框 -->
    <div v-if="showPrompt" class="prompt-container">
      <div class="prompt-content">
        <div class="prompt-message">Add as a new relation?</div>
        <div class="prompt-buttons">
          <q-btn 
            flat 
            dense 
            color="positive" 
            icon="check" 
            size="sm" 
            @click.stop="onConfirm"
          >
            <q-tooltip>Yes, add new relation</q-tooltip>
          </q-btn>
          <q-btn 
            flat 
            dense 
            color="negative" 
            icon="close" 
            size="sm" 
            @click.stop="onCancel"
          >
            <q-tooltip>Cancel</q-tooltip>
          </q-btn>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SelectionIndicator',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    position: {
      type: Object,
      default: () => ({ 
        x: 0, 
        y: 0,
        directionOffset: { vertical: -20, horizontal: 0 } 
      })
    },
    containerBounds: {
      type: Object,
      default: () => ({ 
        left: 0, 
        top: 0, 
        right: window.innerWidth, 
        bottom: window.innerHeight,
        width: window.innerWidth,
        height: window.innerHeight
      })
    },
    autoHideOnTextDeselect: {
      type: Boolean,
      default: true
    },
    debug: {
      type: Boolean,
      default: false  // 添加调试开关，默认关闭
    }
  },
  emits: ['click', 'confirm', 'cancel', 'hide', 'update:show', 'update:position'],
  data() {
    return {
      localShow: this.show, // 使用内部状态控制组件显示/隐藏
      showPrompt: false,
      documentMouseDownHandler: null,
      selectionChangeHandler: null,
      globalSelectionHandler: null, // 新增全局选择检测处理函数引用
      justActivated: false, // 标记组件是否刚刚被激活
      ignoreNextMouseEvent: false, // 忽略下一个鼠标事件
      lastSelectionTime: 0 // 添加上次选择时间记录到组件数据中
    }
  },
  computed: {
    directionOffset() {
      return this.position.directionOffset || { vertical: -20, horizontal: 0 };
    },
    adjustedPosition() {
      const overflowAllowance = 15;
      
      let x = this.position.x + this.directionOffset.horizontal;
      let y = this.position.y + this.directionOffset.vertical;
      
      const bounds = this.containerBounds;
      
      x = Math.max(bounds.left - overflowAllowance, x);
      x = Math.min(bounds.right + overflowAllowance, x);
      
      y = Math.max(bounds.top - 20, y);
      y = Math.min(bounds.bottom + overflowAllowance, y);
      
      return { x, y };
    }
  },
  mounted() {
    this.setupEventListeners();
    this.setupGlobalSelectionDetection();
  },
  methods: {
    // 添加日志辅助方法
    log(message, level = 'info') {
      // 如果调试模式关闭，只显示错误和重要信息
      if (!this.debug && level === 'debug') {
        return;
      }
      
      // 对于重要事件，始终记录日志
      if (level === 'important') {
        console.log(`%cSelectionIndicator: ${message}`, 'color: #0066cc; font-weight: bold;');
        return;
      }
      
      // 对于普通信息，根据调试模式决定样式
      if (this.debug) {
        console.log(`%cSelectionIndicator: ${message}`, level === 'info' ? 'color: #2196f3' : 'color: #7f7f7f');
      } else {
        // 非调试模式下，只输出info级别的日志
        if (level === 'info') {
          console.log(`SelectionIndicator: ${message}`);
        }
      }
    },
    // 显示组件的方法
    showIndicator() {
      this.log('showIndicator');
      
      // 如果组件已经显示，不重复操作
      if (this.localShow) {
        this.log('组件已经显示，不重复操作', 'debug');
        return;
      }
      
      this.localShow = true;
      
      // 标记组件刚刚被激活，应忽略立即的鼠标事件
      this.justActivated = true;
      this.ignoreNextMouseEvent = true;
      
      // 设置一个短暂的延迟，防止立即隐藏
      setTimeout(() => {
        this.justActivated = false;
      }, 300); // 300ms 的保护时间
      
      // 设置组件内部事件监听器
      this.setupEventListeners();
    },
    onConfirm() {
      this.log('onConfirm');
      this.$emit('confirm');
      this.showPrompt = false;
      // 即使确认添加也应该隐藏指示器
      this.hideIndicator();
    },
    onCancel() {
      this.log('onCancel');
      this.$emit('cancel');
      this.showPrompt = false;
      this.hideIndicator();
    },
    hideIndicator() {
      this.log('hideIndicator');
      // 直接修改内部状态隐藏组件
      this.localShow = false;
      
      // 同时通知父组件（保持单向数据流）
      this.$emit('hide');
      this.$emit('update:show', false);
    },
    onDocumentMouseDown(event) {
      // 如果组件已经隐藏，不处理
      if (!this.localShow) return;
      
      // 如果组件刚刚被激活，忽略此事件
      if (this.justActivated || this.ignoreNextMouseEvent) {
        this.log('忽略刚激活时的鼠标事件');
        this.ignoreNextMouseEvent = false;
        return;
      }
      
      this.log('onDocumentMouseDown', 'debug');
      
      // 如果点击的是指示器内部元素，不处理
      if (this.$refs.indicatorRef && this.$refs.indicatorRef.contains(event.target)) {
        this.log('点击了指示器内部，不处理', 'debug');
        return;
      }
      
      this.log('点击了指示器外部，隐藏组件');
      // 无论文本是否被选中，点击指示器外部都隐藏整个指示器
      this.showPrompt = false;
      this.hideIndicator();
    },
    onSelectionChange() {
      // 如果组件已经隐藏，不处理
      if (!this.localShow) return;
      
      this.log('onSelectionChange', 'debug');
      
      // 检查是否有文本选择
      const selection = window.getSelection();
      const hasSelection = selection && selection.toString().trim().length > 0;
      
      // 如果没有文本选择且启用了自动隐藏，隐藏指示器
      if (this.autoHideOnTextDeselect && !hasSelection && !this.justActivated) {
        this.log('没有文本选择，隐藏组件');
        this.showPrompt = false;
        this.hideIndicator();
      }
    },
    setupEventListeners() {
      this.log('setupEventListeners', 'debug');
      
      // 只移除组件内部事件监听器，保留全局选择监听器
      this.removeComponentListeners();
      
      // 创建新的事件处理函数，并保存引用以便之后移除
      this.documentMouseDownHandler = this.onDocumentMouseDown.bind(this);
      this.selectionChangeHandler = this.onSelectionChange.bind(this);
      
      // 添加事件监听 - 使用mousedown代替click
      setTimeout(() => {
        document.addEventListener('mousedown', this.documentMouseDownHandler);
        document.addEventListener('selectionchange', this.selectionChangeHandler);
        this.log('事件监听器已添加', 'debug');
      }, 50); // 小延迟确保DOM完全更新
    },
    removeComponentListeners() {
      this.log('removeComponentListeners', 'debug');
      
      // 如果存在处理函数，则移除事件监听
      if (this.documentMouseDownHandler) {
        document.removeEventListener('mousedown', this.documentMouseDownHandler);
        this.documentMouseDownHandler = null;
      }
      
      if (this.selectionChangeHandler) {
        document.removeEventListener('selectionchange', this.selectionChangeHandler);
        this.selectionChangeHandler = null;
      }
      
      this.log('组件内部事件监听器已移除', 'debug');
    },
    removeEventListeners() {
      this.log('removeEventListeners', 'debug');
      
      // 先移除组件内部监听器
      this.removeComponentListeners();
      
      // 再移除全局选择监听器
      if (this.globalSelectionHandler) {
        document.removeEventListener('selectionchange', this.globalSelectionHandler);
        this.globalSelectionHandler = null;
        this.log('全局选择监听器已移除', 'debug');
      }
    },
    // 新增的全局文本选择检测方法
    setupGlobalSelectionDetection() {
      this.log('setupGlobalSelectionDetection', 'debug');
      
      // 移除旧的全局监听器(如果有)
      if (this.globalSelectionHandler) {
        document.removeEventListener('selectionchange', this.globalSelectionHandler);
        this.log('移除旧的全局选择监听器', 'debug');
      }
      
      // 创建全局选择检测处理函数
      this.globalSelectionHandler = () => {
        // 显著减少日志输出 - 不再每次触发都输出
        
        // 检查是否有文本选择
        const selection = window.getSelection();
        const hasSelection = selection && selection.toString().trim().length > 0;
        
        // 防抖动：确保两次触发之间至少间隔100ms
        const now = Date.now();
        if (now - this.lastSelectionTime < 100) {
          // 不再输出高频调试信息
          return;
        }
        this.lastSelectionTime = now;
        
        // 如果有文本选择且组件当前未显示，则显示组件
        if (hasSelection && !this.localShow) {
          this.log('检测到新的文本选择，显示组件', 'important');
          
          // 获取当前选区位置
          const range = selection.getRangeAt(0);
          const rect = range.getBoundingClientRect();
          
          // 更新位置信息
          const newPosition = {
            x: rect.left + rect.width / 2,
            y: rect.top,
            directionOffset: this.directionOffset
          };
          
          // 通知父组件更新位置（如果需要）
          this.$emit('update:position', newPosition);
          
          // 显示指示器
          this.showIndicator();
          
          // 通知父组件组件已显示
          this.$emit('update:show', true);
        }
      };
      
      // 添加全局selection事件监听
      document.addEventListener('selectionchange', this.globalSelectionHandler);
      this.log('全局选择监听器已设置', 'debug');
    }
  },
  watch: {
    show(newVal, oldVal) {
      this.log(`show prop 值变化 ${oldVal} -> ${newVal}`, 'debug');
      
      // 同步内部状态与prop
      if (newVal !== this.localShow) {
        this.localShow = newVal;
        
        if (newVal) {
          // 标记组件刚刚被激活，应忽略立即的鼠标事件
          this.justActivated = true;
          this.ignoreNextMouseEvent = true;
          
          // 设置一个短暂的延迟，防止立即隐藏
          setTimeout(() => {
            this.justActivated = false;
          }, 300); // 300ms 的保护时间
          
          // 当组件显示时
          // 重置提示框状态
          this.showPrompt = false;
          
          // 设置事件监听
          this.$nextTick(() => {
            this.setupEventListeners();
            
            // 检查当前是否有文本选择，如果没有则立即隐藏
            const selection = window.getSelection();
            const hasSelection = selection && selection.toString().trim().length > 0;
            if (this.autoHideOnTextDeselect && !hasSelection) {
              this.log('显示时没有文本选择，立即隐藏', 'debug');
              this.hideIndicator();
              return;
            }
            
            // 强制更新组件以确保正确渲染
            const el = this.$el;
            if (el && (el.offsetWidth === 0 || el.offsetHeight === 0)) {
              this.log('组件尺寸为0，强制更新', 'debug');
              this.$forceUpdate();
            }
          });
        }
      }
    },
    localShow(newVal) {
      this.log(`localShow 值变化为 ${newVal}`, 'debug');
    },
    position: {
      handler(newPos) {
        if (!newPos || typeof newPos.x !== 'number' || typeof newPos.y !== 'number') {
          console.warn('SelectionIndicator: Invalid position provided', newPos);
        }
      },
      deep: true
    }
  },
  beforeUnmount() {
    this.log('beforeUnmount', 'debug');
    // 组件销毁前移除所有事件监听
    this.removeEventListeners();
  }
}
</script>

<style>
.selection-indicator {
  position: absolute;
  z-index: 1000;
  pointer-events: auto;
  transform: translate(-50%, -50%);
}

.add-icon {
  cursor: pointer;
  background-color: #2196f3;
  color: white;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  animation: fadeIn 0.2s ease-out;
  transform: translate(0, 0);
}

.add-icon:hover {
  background-color: #1976d2;
  transform: scale(1.1);
}

.prompt-container {
  position: absolute;
  top: 0;
  left: 0;
  transform: translate(-40%, -120%);
  z-index: 1001;
  animation: promptFadeIn 0.2s ease-out;
}

.prompt-content {
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #e0e0e0;
  padding: 8px 12px;
  min-width: 140px;
}

.prompt-message {
  font-size: 14px;
  margin-bottom: 8px;
  text-align: center;
  color: #333;
}

.prompt-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes promptFadeIn {
  from { opacity: 0; transform: translate(-40%, -110%); }
  to { opacity: 1; transform: translate(-40%, -120%); }
}
</style> 