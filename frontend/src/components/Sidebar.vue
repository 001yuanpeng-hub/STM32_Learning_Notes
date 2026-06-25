<template>
  <aside class="sidebar" :class="{ open: isOpen }">
    <div class="sidebar-header">
      <button class="new-chat-btn" @click="$emit('new-chat')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>新建对话</span>
      </button>
      <button class="close-btn" @click="$emit('close')" title="收起侧边栏">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="11 17 6 12 11 7"/>
          <polyline points="18 17 13 12 18 7"/>
        </svg>
      </button>
    </div>

    <div class="sidebar-content">
      <div class="section">
        <button class="section-title" @click="recentExpanded = !recentExpanded">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            :style="{ transform: recentExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
          <span>Recent</span>
        </button>

        <div v-if="recentExpanded" class="conversation-list">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="conversation-item"
            :class="{ active: activeId === conv.id }"
            @click="$emit('select', conv.id)"
          >
            <!-- 编辑状态 -->
            <input
              v-if="editingId === conv.id"
              v-model="editingTitle"
              class="edit-input"
              @blur="saveTitle(conv.id)"
              @keyup.enter="saveTitle(conv.id)"
              @keyup.escape="cancelEdit"
              @click.stop
              ref="editInput"
            />
            <!-- 显示状态 -->
            <span v-else class="conv-title">{{ conv.title }}</span>

            <div class="item-actions">
              <button class="action-btn" @click.stop="startEdit(conv)" title="重命名">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button class="action-btn delete" @click.stop="$emit('delete', conv.id)" title="删除">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>
          <div v-if="conversations.length === 0" class="empty-hint">暂无对话</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import axios from 'axios'

defineProps({
  isOpen: Boolean,
  conversations: Array,
  activeId: Number
})

const emit = defineEmits(['new-chat', 'select', 'delete', 'close', 'renamed'])

const recentExpanded = ref(true)
const editingId = ref(null)
const editingTitle = ref('')
const editInput = ref(null)

function startEdit(conv) {
  editingId.value = conv.id
  editingTitle.value = conv.title
  nextTick(() => {
    if (editInput.value) {
      editInput.value.focus()
      editInput.value.select()
    }
  })
}

function cancelEdit() {
  editingId.value = null
  editingTitle.value = ''
}

async function saveTitle(convId) {
  const title = editingTitle.value.trim()
  if (!title) {
    cancelEdit()
    return
  }
  try {
    await axios.patch(`/api/conversations/${convId}`, { title })
    emit('renamed')
  } catch (err) {
    console.error('重命名失败:', err)
  }
  cancelEdit()
}
</script>

<style scoped>
.sidebar {
  width: 0;
  overflow: hidden;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  flex-shrink: 0;
  position: relative;
  z-index: 200;
}

.sidebar.open {
  width: 260px;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  padding: 10px 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  color: #374151;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.new-chat-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.close-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  border-radius: 6px;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.section {
  margin-bottom: 4px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px;
  background: none;
  border: none;
  color: #6b7280;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}

.section-title:hover {
  background: #f3f4f6;
}

.section-title svg {
  transition: transform 0.15s;
  flex-shrink: 0;
}

.conversation-list {
  margin-top: 2px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.conversation-item:hover {
  background: #f3f4f6;
}

.conversation-item.active {
  background: #e5e7eb;
}

.conv-title {
  flex: 1;
  font-size: 0.8125rem;
  color: #374151;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.edit-input {
  flex: 1;
  min-width: 0;
  padding: 2px 6px;
  border: 1px solid #6366f1;
  border-radius: 4px;
  font-size: 0.8125rem;
  color: #111827;
  outline: none;
  background: #ffffff;
}

.item-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}

.conversation-item:hover .item-actions {
  opacity: 1;
}

.action-btn {
  width: 24px;
  height: 24px;
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.15s;
}

.action-btn:hover {
  color: #374151;
  background: #e5e7eb;
}

.action-btn.delete:hover {
  color: #ef4444;
  background: #fef2f2;
}

.empty-hint {
  padding: 12px 10px;
  font-size: 0.75rem;
  color: #9ca3af;
  text-align: center;
}

.sidebar-content::-webkit-scrollbar {
  width: 4px;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

@media (max-width: 840px) {
  .sidebar.open {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 200;
    box-shadow: 4px 0 16px rgba(0, 0, 0, 0.1);
  }
}
</style>
