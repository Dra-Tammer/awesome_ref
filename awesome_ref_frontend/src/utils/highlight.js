export function highlightText(text, query) {
  if (!query || !text) return escapeHtml(text || '')
  const q = query.trim().toLowerCase()
  if (!q) return escapeHtml(text)

  const words = q.split(/\s+/).filter(Boolean)
  if (words.length === 0) return escapeHtml(text)

  const pattern = new RegExp(`(${words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')

  return escapeHtml(text).replace(pattern, '<mark class="search-highlight">$1</mark>')
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}
