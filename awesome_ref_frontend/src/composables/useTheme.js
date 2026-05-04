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
    getComputedStyle(el)
    theme.value = next

    setTimeout(() => {
      el.classList.remove('theme-transitioning')
      transitioning = false
    }, 350)
  }

  watch(theme, (val) => {
    document.documentElement.setAttribute('data-theme', val)
    localStorage.setItem('theme', val)
  }, { immediate: true })

  return { theme, toggle }
}
