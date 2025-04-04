<template>
  <div v-if="show" 
       class="context-menu" 
       :style="{ left: position.x + 'px', top: position.y + 'px' }"
       @click.stop
       @contextmenu.prevent.stop>
    <!-- Node menu -->
    <div v-if="type === 'node'" class="menu-items">
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('rename')">
        <span>Rename Node</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('delete')">
        <span>Delete Node</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('add-connection')">
        <span>Add Connection</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
    </div>
    <!-- Edge menu -->
    <div v-if="type === 'edge'" class="menu-items">
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('edit-label')">
        <span>Edit Label</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('add-meta-relation')">
        <span>Add Meta-Relation</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('delete')">
        <span>Delete Relation</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
    </div>
    <!-- Meta Edge menu (same options as Edge) -->
    <div v-if="type === 'meta-edge'" class="menu-items">
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('edit-label')">
        <span>Edit Label</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('edit-target')">
        <span>Edit Target</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
      <div class="menu-item" :class="{ 'disabled': !canEdit }" @click.stop="canEdit && emitAction('delete')">
        <span>Delete Relation</span>
        <q-tooltip v-if="!canEdit">{{ disabledMessage }}</q-tooltip>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ContextMenu',
  props: {
    show: {
      type: Boolean,
      required: true
    },
    position: {
      type: Object,
      required: true,
      default: () => ({ x: 0, y: 0 })
    },
    type: {
      type: String,
      required: true,
      validator: value => ['node', 'edge', 'meta-edge'].includes(value)
    },
    canEdit: {
      type: Boolean,
      default: true
    },
    isAdmin: {
      type: Boolean,
      default: false
    },
    paperOwner: {
      type: String,
      default: ''
    },
    currentUser: {
      type: String,
      default: ''
    }
  },
  computed: {
    disabledMessage() {
      if (this.isAdmin) {
        return 'View mode, cannot edit';
      } else {
        return 'Only the owner user can edit';
      }
    }
  },
  mounted() {
    // Add event listeners
    document.addEventListener('click', this.handleClickOutside);
    document.addEventListener('contextmenu', this.handleContextMenuOutside);
    document.addEventListener('keydown', this.handleEscapeKey);
    
    // Log when mounted
    console.log('Context menu mounted, type:', this.type, 'canEdit:', this.canEdit);
  },
  beforeUnmount() {
    // Remove event listeners
    document.removeEventListener('click', this.handleClickOutside);
    document.removeEventListener('contextmenu', this.handleContextMenuOutside);
    document.removeEventListener('keydown', this.handleEscapeKey);
  },
  methods: {
    emitAction(action) {
      console.log('Menu action clicked:', action);
      this.$emit(action);
      this.$emit('close');
    },
    handleClickOutside(event) {
      // Don't close if clicking inside the menu
      if (this.$el && this.$el.contains(event.target)) {
        return;
      }
      
      // If we get here, the click was outside the menu - close it
      console.log('Click outside context menu detected, closing menu');
      this.$emit('close');
    },
    handleContextMenuOutside(event) {
      // Always close on new context menu
      if (!this.$el || !this.$el.contains(event.target)) {
        this.$emit('close');
      }
    },
    handleEscapeKey(event) {
      // Close on escape key
      if (event.key === 'Escape') {
        this.$emit('close');
      }
    }
  },
  watch: {
    // Log when show changes
    show(newVal) {
      console.log('Context menu visibility changed:', newVal, 'type:', this.type, 'canEdit:', this.canEdit);
    }
  }
}
</script>

<style scoped>
.context-menu {
  position: fixed;
  background: white;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 150px;
  user-select: none;
  overflow: visible;
}

.menu-items {
  padding: 4px 0;
}

.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
  white-space: nowrap;
  position: relative;
}

.menu-item:hover:not(.disabled) {
  background-color: #f5f5f5;
}

.menu-item span {
  font-size: 14px;
  color: #333;
}

/* Add hover effects */
.menu-item:hover:not(.disabled) span {
  color: #000;
}

/* Disabled item styles */
.menu-item.disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.menu-item.disabled:before {
  content: "";
  position: absolute;
  right: 10px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #e74c3c;
  display: inline-block;
}

.menu-item.disabled:after {
  content: "";
  position: absolute;
  right: 10px;
  width: 14px;
  height: 2px;
  background-color: #e74c3c;
  transform: rotate(-45deg);
  top: calc(50% - 1px);
}

.menu-item.disabled span {
  color: #999;
}

/* Add subtle dividers */
.menu-item:not(:last-child) {
  border-bottom: 1px solid #f0f0f0;
}
</style> 