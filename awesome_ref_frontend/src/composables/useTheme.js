import { ref, watch } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'light')
let transitioning = false

export function useTheme() {
  function toggle() {
    if (transitioning) return
    transitioning = true
    const next = theme.value === 'light' ? 'dark' : 'light'
    const el = document.documentElement
    el.classList.add('theme-transitioning')
    // Force synchronous style recalculation so the browser computes
    // transition properties before CSS variables change. Without this,
    // batched style invalidation can skip the transition entirely.
    void el.offsetHeight
    theme.value = next
    setTimeout(() => {
      el.classList.remove('theme-transitioning')
      transitioning = false
    }, 550)
  }

  watch(theme, (val) => {
    document.documentElement.setAttribute('data-theme', val)
    localStorage.setItem('theme', val)
  }, { immediate: true })

  return { theme, toggle }
}
