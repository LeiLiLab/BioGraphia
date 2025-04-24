<template>
  <div 
    v-if="show" 
    class="text-selection-prompt" 
    :style="{ top: position.y + 'px', left: position.x + 'px' }"
  >
    <div class="prompt-content">
      <div class="prompt-message">Add as a new relation?</div>
      <div class="prompt-buttons">
        <q-btn 
          flat 
          dense 
          color="positive" 
          icon="check" 
          size="sm" 
          @click="$emit('confirm')"
        >
          <q-tooltip>Yes, add new relation</q-tooltip>
        </q-btn>
        <q-btn 
          flat 
          dense 
          color="negative" 
          icon="close" 
          size="sm" 
          @click="$emit('cancel')"
        >
          <q-tooltip>Cancel</q-tooltip>
        </q-btn>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TextSelectionPrompt',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    position: {
      type: Object,
      default: () => ({ x: 0, y: 0 })
    }
  },
  emits: ['confirm', 'cancel']
}
</script>

<style>
.text-selection-prompt {
  position: absolute;
  z-index: 1000;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  transform: translate(-50%, -100%);
  animation: fadeIn 0.2s ease-out;
  border: 1px solid #e0e0e0;
}

.prompt-content {
  padding: 8px 12px;
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
  from { opacity: 0; transform: translate(-50%, -90%); }
  to { opacity: 1; transform: translate(-50%, -100%); }
}
</style> 