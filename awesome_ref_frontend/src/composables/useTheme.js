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

    // Force synchronous style resolution with the transition class active
    // but CSS variables still at their current values. This snaps a "before"
    // snapshot that CSS transitions need as the starting point.
    getComputedStyle(el)

    // rAF defers the variable change until after the next paint, so the
    // browser has definitely rendered the "before" state. At that point
    // changing data-theme triggers a clean transition from old → new.
    requestAnimationFrame(() => {
      theme.value = next
      setTimeout(() => {
        el.classList.remove('theme-transitioning')
        transitioning = false
      }, 350)
    })
  }

  watch(theme, (val) => {
    document.documentElement.setAttribute('data-theme', val)
    localStorage.setItem('theme', val)
  }, { immediate: true })

  return { theme, toggle }
}
