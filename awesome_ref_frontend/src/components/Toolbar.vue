<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useAuth } from '../composables/useAuth.js'
import { useTheme } from '../composables/useTheme.js'
import { useToast } from '../composables/useToast.js'
import GlobalSearch from './GlobalSearch.vue'

const { logout, username } = useAuth()
const { theme, toggle: toggleTheme } = useTheme()
const { toast, showToast } = useToast()

const props = defineProps({
  viewMode: { type: String, default: 'references' },
})
const emit = defineEmits(['update:viewMode', 'navigate'])

const showSearch = ref(false)

const showMenu = ref(false)
const menuRef = ref(null)

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
      <span class="view-mode-indicator" :class="{ middle: viewMode === 'notes', right: viewMode === 'profile' }"></span>
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
      <button
        class="btn-view-mode"
        :class="{ active: viewMode === 'profile' }"
        @click="emit('update:viewMode', 'profile')"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        我的
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
</template>
