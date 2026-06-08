export async function importJSONFile(file, authStore, toastStore) {
  const text = await file.text()
  const data = JSON.parse(text)
  if (!data.export_version) {
    toastStore.showToast('无效的备份文件格式', 'error')
    return false
  }
  const res = await fetch('/api/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authStore.getHeaders() },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || '导入失败')
  }
  return true
}
