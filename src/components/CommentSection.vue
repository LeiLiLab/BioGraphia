<template>
  <div class="comment-section q-mt-lg">
    <div class="text-h5 q-mb-md text-center">Comments</div>

    <!-- Comments list -->
    <div class="comments-list q-mb-lg">
      <template v-if="comments.length">
        <div v-for="comment in comments" :key="comment.id" class="comment-item q-mb-md">
          <!-- Main comment -->
          <div class="comment-content q-pa-md">
            <div class="row items-center justify-between q-mb-sm">
              <div class="text-weight-bold">{{ comment.username }}</div>
              <div class="text-caption text-grey timestamp">
                {{ formatDate(comment.timestamp) }}
              </div>
            </div>
            <div class="comment-text q-mb-sm" :class="{ 'deleted-comment': comment.is_deleted }">
              {{ comment.is_deleted ? 'This comment has been deleted' : comment.content }}
            </div>
            <div class="row items-center" v-if="!comment.is_deleted">
              <q-btn
                flat
                dense
                color="primary"
                label="Reply"
                @click="startReply(comment)"
                :disable="!currentUser"
                class="action-btn"
              />
              <template v-if="canDelete(comment)">
                <q-btn
                  flat
                  dense
                  color="info"
                  label="Edit"
                  class="action-btn q-ml-sm"
                  @click="startEdit(comment)"
                  v-if="!comment.isEditing"
                />
                <div v-if="comment.isEditing" class="row items-center">
                  <q-btn
                    flat
                    dense
                    color="orange-8"
                    label="Cancel"
                    class="action-btn"
                    @click="cancelEdit(comment)"
                  />
                  <q-btn
                    flat
                    dense
                    color="positive"
                    label="Save"
                    class="action-btn q-ml-sm"
                    @click="saveEdit(comment)"
                  />
                </div>
                <q-btn
                  flat
                  dense
                  color="negative"
                  label="Delete"
                  class="action-btn q-ml-sm"
                  @click="confirmDelete(comment)"
                />
              </template>
            </div>

            <!-- Edit input -->
            <div v-if="comment.isEditing" class="edit-input q-mt-md">
              <q-input
                v-model="comment.editContent"
                type="textarea"
                outlined
                dense
                class="q-mb-sm comment-input-field"
              />
            </div>

            <!-- Reply input for main comment -->
            <div v-if="replyingTo === comment.id && !replyingToReply" class="reply-input q-mt-md">
              <q-input
                v-model="replyContent"
                type="textarea"
                outlined
                dense
                placeholder="Add a reply..."
                class="q-mb-sm"
              />
              <div class="row justify-end">
                <q-btn
                  flat
                  label="Cancel"
                  color="grey"
                  class="action-btn q-mr-sm"
                  @click="cancelReply"
                />
                <q-btn
                  :disable="!replyContent.trim()"
                  color="primary"
                  label="Reply"
                  class="action-btn"
                  @click="submitReply(comment.id)"
                />
              </div>
            </div>

            <!-- Replies -->
            <div v-if="comment.replies && comment.replies.length" class="replies q-mt-md q-ml-lg">
              <div
                v-for="reply in comment.replies"
                :key="reply.id"
                :id="reply.id"
                class="reply-item q-mb-md q-pa-md"
                :class="{ 'highlight-reply': highlightedReplyId === reply.id }"
              >
                <div class="row items-center justify-between q-mb-sm">
                  <div class="text-weight-bold">{{ reply.username }}</div>
                  <div class="text-caption text-grey">
                    {{ formatDate(reply.timestamp) }}
                  </div>
                </div>
                <div class="reply-text" :class="{ 'deleted-comment': reply.is_deleted }">
                  <template v-if="!reply.is_deleted">
                    <div
                      v-if="reply.quoted_username && reply.quoted_content"
                      class="quoted-content q-mb-sm"
                      @click="highlightQuotedReply(reply)"
                    >
                      <span class="quoted-username">{{ reply.quoted_username }}:</span>
                      <span class="quoted-text">{{ reply.quoted_content }}</span>
                    </div>
                    {{ reply.content }}
                  </template>
                  <template v-else> This comment has been deleted </template>
                </div>
                <div class="row items-center q-mt-sm" v-if="!reply.is_deleted">
                  <q-btn
                    flat
                    dense
                    color="primary"
                    label="Reply"
                    @click="startReply(comment, reply)"
                    :disable="!currentUser"
                    class="action-btn"
                  />
                  <template v-if="canDelete(reply)">
                    <q-btn
                      flat
                      dense
                      color="info"
                      label="Edit"
                      @click="startEdit(reply)"
                      v-if="!reply.isEditing"
                      class="action-btn q-ml-sm"
                    />
                    <div v-if="reply.isEditing" class="row items-center">
                      <q-btn
                        flat
                        dense
                        color="orange-8"
                        label="Cancel"
                        class="action-btn"
                        @click="cancelEdit(reply)"
                      />
                      <q-btn
                        flat
                        dense
                        color="positive"
                        label="Save"
                        class="action-btn q-ml-sm"
                        @click="saveEdit(reply)"
                      />
                    </div>
                    <q-btn
                      flat
                      dense
                      color="negative"
                      label="Delete"
                      class="action-btn q-ml-sm"
                      @click="confirmDelete(reply)"
                    />
                  </template>
                </div>

                <!-- Reply input for replies -->
                <div
                  v-if="replyingTo === comment.id && replyingToReply === reply.id"
                  class="reply-input q-mt-md"
                >
                  <q-input
                    v-model="replyContent"
                    type="textarea"
                    outlined
                    dense
                    placeholder="Add a reply..."
                    class="q-mb-sm"
                  />
                  <div class="row justify-end">
                    <q-btn
                      flat
                      label="Cancel"
                      color="grey"
                      class="action-btn q-mr-sm"
                      @click="cancelReply"
                    />
                    <q-btn
                      :disable="!replyContent.trim()"
                      color="primary"
                      label="Reply"
                      class="action-btn"
                      @click="submitReply(comment.id)"
                    />
                  </div>
                </div>

                <!-- Edit input for replies -->
                <div v-if="reply.isEditing" class="edit-input q-mt-md">
                  <q-input
                    v-model="reply.editContent"
                    type="textarea"
                    outlined
                    dense
                    class="q-mb-sm comment-input-field"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="text-center text-grey q-pa-xl empty-state">
        No comments yet. Be the first to comment!
      </div>
    </div>

    <!-- Add comment input -->
    <div class="comment-input">
      <q-separator class="q-mb-md" />
      <q-input
        v-model="newComment"
        type="textarea"
        outlined
        placeholder="Add a comment..."
        :disable="!currentUser"
        @keyup.enter="addComment"
        class="q-mb-sm comment-input-field"
      />
      <div class="row justify-end">
        <q-btn
          :disable="!newComment.trim() || !currentUser"
          color="primary"
          label="Comment"
          @click="addComment"
          class="action-btn"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useQuasar } from 'quasar'
import { BACKEND_URL } from '../config/api'

interface Comment {
  id: string
  username: string
  content: string
  timestamp: string
  parent_id?: string
  quoted_content?: string
  quoted_username?: string
  quoted_id?: string
  replies: Comment[]
  isEditing?: boolean
  editContent?: string | null
  is_deleted: boolean
}

interface ReplyData {
  url: string
  username: string
  content: string
  parent_id: string
  quoted_username?: string
  quoted_content?: string
  quoted_id?: string
}

export default defineComponent({
  name: 'CommentSection',

  props: {
    paperUrl: {
      type: String,
      required: true,
    },
    currentUser: {
      type: Object,
      default: null,
    },
  },

  setup(props) {
    const $q = useQuasar()
    const comments = ref<Comment[]>([])
    const newComment = ref('')
    const replyingTo = ref<string | null>(null)
    const replyContent = ref('')
    const quotedReply = ref<Comment | null>(null)
    const replyingToReply = ref<string | null>(null)
    const highlightedReplyId = ref<string | null>(null)

    // Load comments
    const loadComments = async () => {
      try {
        const response = await axios.get(`${BACKEND_URL}/api/comments`, {
          params: {
            url: props.paperUrl,
          },
        })
        // Ensure each reply has the correct quoted content
        const processedComments = response.data.comments.map((comment: Comment) => {
          if (comment.replies) {
            comment.replies = comment.replies.map((reply: Comment) => {
              if (reply.quoted_content && reply.quoted_username) {
                reply.quoted_content = truncateText(reply.quoted_content, 100)
              }
              return reply
            })
          }
          return comment
        })
        comments.value = processedComments
      } catch (error) {
        console.error('Error loading comments:', error)
      }
    }

    // Add comment
    const addComment = async () => {
      if (!newComment.value.trim() || !props.currentUser) return

      try {
        await axios.post(`${BACKEND_URL}/api/comments`, {
          url: props.paperUrl,
          username: props.currentUser.username,
          content: newComment.value,
          is_main_comment: true,
        })
        newComment.value = ''
        await loadComments()
        $q.notify({
          type: 'positive',
          message: 'Comment added successfully',
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      } catch (error) {
        console.error('Error adding comment:', error)
        $q.notify({
          type: 'negative',
          message: 'Error adding comment',
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      }
    }

    // Start reply
    const startReply = (comment: Comment, reply?: Comment) => {
      replyingTo.value = comment.id
      replyContent.value = ''
      quotedReply.value = reply || null
      replyingToReply.value = reply ? reply.id : null
    }

    // Cancel reply
    const cancelReply = () => {
      replyingTo.value = null
      replyContent.value = ''
      quotedReply.value = null
      replyingToReply.value = null
    }

    // Submit reply
    const submitReply = async (parentId: string) => {
      if (!replyContent.value.trim() || !props.currentUser) return

      try {
        const replyData: ReplyData = {
          url: props.paperUrl,
          username: props.currentUser.username,
          content: replyContent.value,
          parent_id: parentId,
        }

        if (quotedReply.value && quotedReply.value.id.startsWith('r')) {
          replyData.quoted_username = quotedReply.value.username
          replyData.quoted_content = truncateText(quotedReply.value.content, 100)
          replyData.quoted_id = quotedReply.value.id
        }

        await axios.post(`${BACKEND_URL}/api/comments`, replyData)
        cancelReply()
        await loadComments()
        $q.notify({
          type: 'positive',
          message: 'Reply added successfully',
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      } catch (error) {
        console.error('Error adding reply:', error)
        $q.notify({
          type: 'negative',
          message: 'Error adding reply',
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      }
    }

    // Format date to specified format
    const formatDate = (timestamp: string) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('en-US', {
        month: 'long',
        day: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: 'UTC',
        timeZoneName: 'short',
      })
    }

    // Computed property: comments list sorted by time in ascending order
    const sortedComments = computed(() => {
      return [...comments.value].sort((a, b) => {
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      })
    })

    // Start editing comment
    const startEdit = (comment: Comment) => {
      comment.isEditing = true
      comment.editContent = comment.content
    }

    // Cancel edit
    const cancelEdit = (comment: Comment) => {
      comment.isEditing = false
      comment.editContent = null
    }

    // Save edit
    const saveEdit = async (comment: Comment) => {
      if (!comment.editContent?.trim()) return

      try {
        await axios.put(`${BACKEND_URL}/api/comments/${comment.id}`, {
          url: props.paperUrl,
          username: props.currentUser?.username,
          content: comment.editContent,
        })
        await loadComments()
        $q.notify({
          type: 'positive',
          message: 'Comment updated successfully',
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      } catch (error) {
        console.error('Error updating comment:', error)
        $q.notify({
          type: 'negative',
          message: 'Error updating comment',
          position: 'top',
          timeout: 2000,
          html: true,
          classes: 'text-h6',
        })
      }
    }

    // Confirm delete
    const confirmDelete = (comment: Comment) => {
      let message = 'Are you sure you want to delete this comment?'
      if (comment.replies && comment.replies.length > 0) {
        const activeReplies = comment.replies.filter((reply) => !reply.is_deleted)
        if (activeReplies.length > 0) {
          message =
            'This comment has replies. The comment will be marked as deleted but will remain visible.'
        } else {
          message = 'This comment and all its deleted replies will be permanently removed.'
        }
      }

      $q.dialog({
        title: 'Delete Comment',
        message: `<div style="font-size: 20px;">${message}</div>`,
        class: 'custom-dialog',
        style: {
          width: '500px',
        },
        html: true,
        cancel: {
          label: 'Cancel',
          flat: true,
          color: 'grey',
          class: 'custom-dialog-btn',
        },
        ok: {
          label: 'Delete',
          color: 'negative',
          unelevated: true,
          class: 'custom-dialog-btn',
        },
        persistent: true,
      }).onOk(async () => {
        try {
          const response = await axios.delete(`${BACKEND_URL}/api/comments/${comment.id}`, {
            params: {
              url: props.paperUrl,
              username: props.currentUser?.username,
              has_active_replies:
                comment.replies && comment.replies.some((reply) => !reply.is_deleted),
            },
          })

          if (response.data.success) {
            $q.notify({
              type: 'positive',
              message: response.data.message || 'Comment deleted successfully',
              position: 'top',
              timeout: 2000,
              html: true,
              classes: 'text-h6',
            })
            await loadComments()
          } else {
            $q.notify({
              type: 'negative',
              message: response.data.message || 'Failed to delete comment',
              position: 'top',
              timeout: 2000,
              html: true,
              classes: 'text-h6',
            })
          }
        } catch (error) {
          console.error('Error deleting comment:', error)
          $q.notify({
            type: 'negative',
            message: 'Error deleting comment',
            position: 'top',
            timeout: 2000,
            html: true,
            classes: 'text-h6',
          })
        }
      })
    }

    // Check if comment can be deleted
    const canDelete = (comment: Comment) => {
      return props.currentUser && comment.username === props.currentUser.username
    }

    // Truncate text
    const truncateText = (text: string, maxLength: number) => {
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength - 3) + '...'
    }

    // Highlight quoted reply
    const highlightQuotedReply = (reply: Comment) => {
      console.log('Highlighting reply:', reply.quoted_id)
      if (reply.quoted_id) {
        highlightedReplyId.value = reply.quoted_id
        // Scroll to the quoted reply
        const quotedElement = document.getElementById(reply.quoted_id)
        console.log('Found element:', quotedElement)
        if (quotedElement) {
          quotedElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
        // Remove highlight after 1 second
        setTimeout(() => {
          highlightedReplyId.value = null
        }, 1000)
      }
    }

    // Initial load of comments
    onMounted(() => {
      loadComments()
    })

    return {
      comments: sortedComments,
      newComment,
      replyingTo,
      replyContent,
      quotedReply,
      replyingToReply,
      addComment,
      startReply,
      cancelReply,
      submitReply,
      canDelete,
      formatDate,
      startEdit,
      cancelEdit,
      saveEdit,
      confirmDelete,
      truncateText,
      highlightedReplyId,
      highlightQuotedReply,
    }
  },
})
</script>

<style lang="scss" scoped>
.comment-section {
  width: 100%;
  margin: 0 auto;

  :deep(.q-btn) {
    .q-btn__content {
      font-size: 18px;
      padding: 0;
      margin: 0;
    }

    .q-btn__wrapper {
      padding: 0;
      min-height: 32px;
    }
  }
}

.comment-input-field {
  :deep(.q-field__native),
  :deep(.q-field__input) {
    font-size: 20px !important;
  }

  :deep(.q-field__label) {
    font-size: 20px !important;
  }
}

.comment-btn {
  font-size: 18px;
}

.comment-content {
  background: #f5f5f5;
  border-radius: 8px;

  .text-weight-bold {
    font-size: 24px;
  }

  .comment-text {
    font-size: 24px;
  }

  .text-caption.text-grey {
    font-size: 24px !important;
  }
}

.reply-item {
  background: #ffffff;
  border-radius: 8px;
  border-left: 3px solid #1976d2;
  transition: all 0.3s ease;

  &.highlight-reply {
    background-color: rgba(255, 235, 59, 0.3);
    box-shadow: 0 0 8px rgba(255, 235, 59, 0.5);
    border-left: 3px solid #ffd700;
  }

  .text-weight-bold {
    font-size: 24px;
  }

  .reply-text {
    font-size: 24px;
  }

  .text-caption.text-grey {
    font-size: 24px !important;
  }
}

.comment-text,
.reply-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.replies {
  border-left: 2px solid #e0e0e0;
}

.empty-state {
  font-size: 24px;
  font-weight: 500;
  color: #666;
  padding: 48px 0;
}

.edit-input {
  :deep(.q-field__native),
  :deep(.q-field__input) {
    font-size: 18px !important;
  }
}

.timestamp {
  font-size: 20px !important;
  color: #666;
}

:deep(.custom-dialog) {
  .q-card__section--vert {
    &.q-dialog__title {
      font-size: 28px !important;
      font-weight: 600;
      color: #000;
      padding: 24px 24px 0;
    }

    &.q-dialog__message {
      font-size: 30px !important;
      padding: 24px;
      color: #666;
    }
  }

  .q-card__actions {
    padding: 12px 24px 24px;

    .q-btn {
      .q-btn__content {
        font-size: 18px;
        font-weight: 500;
      }

      &.custom-dialog-btn {
        padding: 8px 32px;
      }
    }
  }

  .q-card {
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
}

.reply-input {
  :deep(.q-field__native),
  :deep(.q-field__input) {
    font-size: 20px !important;
  }

  :deep(.q-field__label) {
    font-size: 20px !important;
  }
}

.deleted-comment {
  color: #999;
  font-style: italic;
}

.quoted-content {
  background: #f0f0f0;
  padding: 8px 12px;
  border-left: 3px solid #1976d2;
  border-radius: 4px;
  font-size: 20px;
  color: #666;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: #e0e0e0;
  }
}

.quoted-username {
  font-weight: 600;
  color: #1976d2;
  margin-right: 4px;
}

.quoted-preview {
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;

  .text-caption {
    color: #666;
    font-size: 14px;
    margin-bottom: 4px;
  }
}

.quoted-reference {
  font-size: 20px;
  color: #666;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  margin-bottom: 8px;

  .quoted-username {
    font-weight: 600;
    color: #1976d2;
    margin-right: 4px;
  }

  .quoted-text {
    font-style: italic;
  }
}

.action-btn {
  min-width: 80px;
  justify-content: center;
  padding: 0 8px;
  font-size: 18px !important;
  height: 32px;

  :deep(.q-btn__content) {
    font-size: 18px !important;
    margin: 0;
    padding: 0;
  }

  :deep(.q-btn__wrapper) {
    padding: 0;
    min-height: 32px;
  }
}
</style>
