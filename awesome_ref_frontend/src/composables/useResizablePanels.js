import { ref } from 'vue'

export function useResizablePanels(options = {}) {
  const {
    leftDefault = 240,
    leftMin = 180,
    leftMax = 400,
    rightDefault = 780,
    rightMin = 320,
    rightMax = 800,
  } = options

  const leftWidth = ref(leftDefault)
  const leftCollapsed = ref(false)
  const leftPrevWidth = ref(leftDefault)

  const rightWidth = ref(rightDefault)
  const rightCollapsed = ref(false)
  const rightPrevWidth = ref(rightDefault)

  const resizingLeft = ref(false)
  const resizingRight = ref(false)
  let leftRaf = null
  let rightRaf = null

  function onLeftHandleDown(e) {
    e.preventDefault()
    if (leftCollapsed.value) {
      toggleLeftPanel()
      return
    }
    const startX = e.clientX
    const startW = leftWidth.value
    let moved = false

    function onMove(ev) {
      if (!moved && Math.abs(ev.clientX - startX) > 3) moved = true
      if (!moved) return
      resizingLeft.value = true
      if (leftRaf) cancelAnimationFrame(leftRaf)
      leftRaf = requestAnimationFrame(() => {
        leftWidth.value = Math.max(leftMin, Math.min(leftMax, startW + ev.clientX - startX))
      })
    }

    function onUp() {
      resizingLeft.value = false
      if (leftRaf) cancelAnimationFrame(leftRaf)
      leftRaf = null
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
      if (!moved) toggleLeftPanel()
    }

    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  function onRightHandleDown(e) {
    e.preventDefault()
    if (rightCollapsed.value) {
      toggleRightPanel()
      return
    }
    const startX = e.clientX
    const startW = rightWidth.value
    let moved = false

    function onMove(ev) {
      if (!moved && Math.abs(ev.clientX - startX) > 3) moved = true
      if (!moved) return
      resizingRight.value = true
      if (rightRaf) cancelAnimationFrame(rightRaf)
      rightRaf = requestAnimationFrame(() => {
        rightWidth.value = Math.max(rightMin, Math.min(rightMax, startW + startX - ev.clientX))
      })
    }

    function onUp() {
      resizingRight.value = false
      if (rightRaf) cancelAnimationFrame(rightRaf)
      rightRaf = null
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
      if (!moved) toggleRightPanel()
    }

    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  function toggleLeftPanel() {
    if (leftCollapsed.value) {
      leftCollapsed.value = false
      leftWidth.value = leftPrevWidth.value
    } else {
      leftPrevWidth.value = leftWidth.value
      leftCollapsed.value = true
      leftWidth.value = 0
    }
  }

  function toggleRightPanel() {
    if (rightCollapsed.value) {
      rightCollapsed.value = false
      rightWidth.value = rightPrevWidth.value
    } else {
      rightPrevWidth.value = rightWidth.value
      rightCollapsed.value = true
      rightWidth.value = 0
    }
  }

  return {
    leftWidth, leftCollapsed, resizingLeft, onLeftHandleDown, toggleLeftPanel,
    rightWidth, rightCollapsed, resizingRight, onRightHandleDown, toggleRightPanel,
  }
}
