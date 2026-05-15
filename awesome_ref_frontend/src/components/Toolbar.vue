<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useAuth } from '../composables/useAuth.js'
import { useTheme } from '../composables/useTheme.js'
import { useToast } from '../composables/useToast.js'
import { useReferences } from '../composables/useReferences.js'
import { useGroups } from '../composables/useGroups.js'
import { useNotes } from '../composables/useNotes.js'
import ReferenceEditor from './ReferenceEditor.vue'
import GlobalSearch from './GlobalSearch.vue'

const { logout, username, changePassword, getHeaders } = useAuth()
const { theme, toggle: toggleTheme } = useTheme()
const { toast, showToast } = useToast()
const { addReferences, loadReferences, loadTrash } = useReferences()
const { loadGroups } = useGroups()
const { loadNotes } = useNotes()

const props = defineProps({
  viewMode: { type: String, default: 'references' },
})
const emit = defineEmits(['update:viewMode', 'navigate'])

const showSearch = ref(false)

const showMenu = ref(false)
const menuRef = ref(null)

const showPwdModal = ref(false)
const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')
const pwdError = ref('')
const pwdLoading = ref(false)

const showExportModal = ref(false)

const showNewRefModal = ref(false)
const showImportModal = ref(false)

function onLogout() {
  showMenu.value = false
  logout()
}

function toggleMenu() {
  showMenu.value = !showMenu.value
}

function onClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    showMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onBeforeUnmount(() => document.removeEventListener('click', onClickOutside))

function onNewRef() {
  showMenu.value = false
  showNewRefModal.value = true
}

function onImportRIS() {
  showImportModal.value = false
  showMenu.value = false
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.ris,.txt'
  input.multiple = true
  input.onchange = async (e) => {
    const files = Array.from(e.target.files)
    const { parseRIS } = await import('../utils/risParser.js')
    const risFiles = files.filter(f => f.name.endsWith('.ris') || f.name.endsWith('.txt'))
    if (risFiles.length === 0) return
    const allRefs = []
    for (const file of risFiles) {
      const text = await file.text()
      allRefs.push(...parseRIS(text))
    }
    if (allRefs.length > 0) {
      await addReferences(allRefs)
      showToast(`成功导入 ${allRefs.length} 条文献`)
    } else {
      showToast('未找到可导入的文献数据', 'error')
    }
  }
  input.click()
}

function onImportJSON() {
  showImportModal.value = false
  showMenu.value = false
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      if (!data.export_version) {
        showToast('无效的备份文件格式', 'error')
        return
      }
      const res = await fetch('/api/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getHeaders() },
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '导入失败')
      }
      await Promise.all([loadReferences(), loadGroups(), loadNotes(), loadTrash()])
      showToast('导入成功')
    } catch (e) {
      showToast('导入失败: ' + e.message, 'error')
    }
  }
  input.click()
}

function openPwdModal() {
  showMenu.value = false
  oldPwd.value = ''
  newPwd.value = ''
  confirmPwd.value = ''
  pwdError.value = ''
  showPwdModal.value = true
}

function closePwdModal() {
  showPwdModal.value = false
}

async function onPwdSubmit() {
  pwdError.value = ''
  pwdLoading.value = true
  try {
    await changePassword(oldPwd.value, newPwd.value, confirmPwd.value)
    showPwdModal.value = false
    logout()
  } catch (e) {
    pwdError.value = e.message
  } finally {
    pwdLoading.value = false
  }
}

function openExportModal() {
  showMenu.value = false
  showExportModal.value = true
}

function closeExportModal() {
  showExportModal.value = false
}

async function doExport(format, ext, mime) {
  showExportModal.value = false
  try {
    const res = await fetch(`/api/export?format=${format}`, { headers: getHeaders() })
    if (!res.ok) throw new Error('导出失败')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const date = new Date().toISOString().slice(0, 10)
    a.href = url
    a.download = `awesomeref-export-${date}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
    showToast('导出成功')
  } catch (e) {
    showToast('导出失败: ' + e.message, 'error')
  }
}

function onExportJSON() { doExport('json', 'json', 'application/json') }
function onExportMD()   { doExport('md', 'md', 'text/markdown') }
function onExportPDF()  { doExport('pdf', 'pdf', 'application/pdf') }
function onExportDOCX() { doExport('docx', 'docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') }
</script>

<template>
  <header class="toolbar">
    <div class="toolbar-left">
      <h1 class="logo">
        <span class="logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
        </span>
        AwesomeRef
      </h1>
    </div>
    <div class="toolbar-center">
      <span class="view-mode-indicator" :class="{ right: viewMode === 'notes' }"></span>
      <button
        class="btn-view-mode"
        :class="{ active: viewMode === 'references' }"
        @click="emit('update:viewMode', 'references')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
        文献
      </button>
      <button
        class="btn-view-mode"
        :class="{ active: viewMode === 'notes' }"
        @click="emit('update:viewMode', 'notes')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        笔记
      </button>
    </div>
    <div class="toolbar-right">
      <button class="btn-theme-toggle" @click="toggleTheme" :title="theme === 'light' ? '切换暗黑模式' : '切换亮色模式'">
        <svg v-if="theme === 'light'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
      </button>
      <button class="btn-theme-toggle" @click="showSearch = true" title="全局搜索">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </button>
      <div class="menu-wrapper" ref="menuRef">
        <button class="btn-menu" @click="toggleMenu" title="菜单">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/>
          </svg>
        </button>
        <Transition name="dropdown">
          <div v-if="showMenu" class="dropdown-menu">
            <button class="dropdown-item" @click="onNewRef">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              新建文献
            </button>
            <button class="dropdown-item" @click="showImportModal = true; showMenu = false">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              导入文献
            </button>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item" @click="openExportModal">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              导出数据
            </button>
            <button class="dropdown-item" @click="openPwdModal">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              修改密码
            </button>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item danger" @click="onLogout">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              退出登录
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </header>

  <!-- 修改密码弹框 -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showPwdModal" class="pwd-modal-overlay" @click.self="closePwdModal">
        <div class="pwd-modal">
          <div class="pwd-modal-header">
            <span>修改密码</span>
            <button class="pwd-modal-close" @click="closePwdModal">&times;</button>
          </div>
          <form class="pwd-modal-form" @submit.prevent="onPwdSubmit">
            <div class="form-field">
              <label>原密码</label>
              <input type="password" v-model="oldPwd" placeholder="请输入原密码" />
            </div>
            <div class="form-field">
              <label>新密码</label>
              <input type="password" v-model="newPwd" placeholder="请输入新密码" />
            </div>
            <div class="form-field">
              <label>确认新密码</label>
              <input type="password" v-model="confirmPwd" placeholder="请再次输入新密码" />
            </div>
            <div v-if="pwdError" class="login-error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              {{ pwdError }}
            </div>
            <button type="submit" class="btn-login" :disabled="pwdLoading">
              {{ pwdLoading ? '提交中...' : '确认修改' }}
            </button>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 导出格式选择弹框 -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showExportModal" class="pwd-modal-overlay" @click.self="closeExportModal">
        <div class="pwd-modal import-modal">
          <div class="pwd-modal-header">
            <span>选择导出格式</span>
            <button class="pwd-modal-close" @click="closeExportModal">&times;</button>
          </div>
          <div class="import-modal-body">
            <button class="import-option" @click="onExportJSON">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15v-2h2a1 1 0 1 0 0-2H9"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">JSON</span>
                <span class="import-option-desc">导出完整备份，可用于数据恢复或迁移</span>
              </div>
            </button>
            <button class="import-option" @click="onExportMD">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><polyline points="12 11 16 13 12 15"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">Markdown</span>
                <span class="import-option-desc">可读性强，支持版本管理，方便在编辑器中查看</span>
              </div>
            </button>
            <button class="import-option" @click="onExportPDF">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">PDF</span>
                <span class="import-option-desc">排版固定，适合打印和分享</span>
              </div>
            </button>
            <button class="import-option" @click="onExportDOCX">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><rect x="8" y="12" width="8" height="6" rx="1"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">Word (DOCX)</span>
                <span class="import-option-desc">可编辑文档，适合进一步排版和批注</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- 导入格式选择弹框 -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showImportModal" class="pwd-modal-overlay" @click.self="showImportModal = false">
        <div class="pwd-modal import-modal">
          <div class="pwd-modal-header">
            <span>选择导入格式</span>
            <button class="pwd-modal-close" @click="showImportModal = false">&times;</button>
          </div>
          <div class="import-modal-body">
            <button class="import-option" @click="onImportRIS">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">RIS 文件</span>
                <span class="import-option-desc">导入 .ris 或 .txt 格式的文献数据</span>
              </div>
            </button>
            <button class="import-option" @click="onImportJSON">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15v-2h2a1 1 0 1 0 0-2H9"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">JSON 备份文件</span>
                <span class="import-option-desc">导入包含分组、文献和笔记的完整备份</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Toast 提示 -->
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="toast.visible" class="toast" :class="`toast-${toast.type}`">
        <svg v-if="toast.type === 'success'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        {{ toast.message }}
      </div>
    </Transition>
  </Teleport>

  <GlobalSearch
    :visible="showSearch"
    @close="showSearch = false"
    @navigate="(item) => emit('navigate', item)"
  />

  <ReferenceEditor v-if="showNewRefModal" @close="showNewRefModal = false" />
</template>
