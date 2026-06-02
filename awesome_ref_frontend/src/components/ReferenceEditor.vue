<script setup>
import { ref, onMounted } from 'vue'
import { useReferencesStore } from '../stores/references.js'
import { useToastStore } from '../stores/toast.js'
import { parseBibTeX } from '../utils/bibtexParser.js'

const emit = defineEmits(['close'])

const refsStore = useReferencesStore()
const toastStore = useToastStore()

const visible = ref(false)
const saving = ref(false)

onMounted(() => {
  requestAnimationFrame(() => { visible.value = true })
})
const bibtexText = ref('')
const bibtexError = ref('')
const parsedRefs = ref([])
const parsedActiveIndex = ref(0)

const REF_TYPES = [
  { value: 'JOUR', label: '期刊文章' },
  { value: 'BOOK', label: '图书' },
  { value: 'CHAP', label: '书章节' },
  { value: 'CONF', label: '会议论文' },
  { value: 'THES', label: '学位论文' },
  { value: 'RPRT', label: '报告' },
  { value: 'PAT', label: '专利' },
  { value: 'STD', label: '标准' },
  { value: 'WEB', label: '网页' },
  { value: 'GEN', label: '通用' },
]

const form = ref({
  type: 'JOUR',
  title: '',
  authors: '',
  year: '',
  journal: '',
  volume: '',
  issue: '',
  pages: '',
  doi: '',
  abstract: '',
  keywords: '',
})

function resetForm() {
  form.value = {
    type: 'JOUR',
    title: '',
    authors: '',
    year: '',
    journal: '',
    volume: '',
    issue: '',
    pages: '',
    doi: '',
    abstract: '',
    keywords: '',
  }
}

function fillForm(refData) {
  form.value.type = refData.type || 'JOUR'
  form.value.title = refData.title || ''
  form.value.authors = (refData.authors || []).join('; ')
  form.value.year = refData.year || ''
  form.value.journal = refData.journal || ''
  form.value.volume = refData.volume || ''
  form.value.issue = refData.issue || ''
  form.value.pages = refData.pages || ''
  form.value.doi = refData.doi || ''
  form.value.abstract = refData.abstract || ''
  form.value.keywords = (refData.keywords || []).join('; ')
}

function parseAuthors(text) {
  if (!text.trim()) return []
  return text.split(/[,;\n]/).map(a => a.trim()).filter(Boolean)
}

function parseKeywords(text) {
  if (!text.trim()) return []
  return text.split(/[,;\n]/).map(k => k.trim()).filter(Boolean)
}

function onBibtexParse() {
  bibtexError.value = ''
  parsedRefs.value = []
  parsedActiveIndex.value = 0

  if (!bibtexText.value.trim()) {
    bibtexError.value = '请先粘贴 BibTeX 内容。'
    return
  }

  const results = parseBibTeX(bibtexText.value)
  if (results.length === 0) {
    bibtexError.value = '未检测到有效的 BibTeX 条目，请检查格式。'
    return
  }

  parsedRefs.value = results
  fillForm(results[0])
}

function selectParsedRef(index) {
  parsedActiveIndex.value = index
  fillForm(parsedRefs.value[index])
}

async function onBibtexImportAll() {
  saving.value = true
  try {
    await refsStore.addReferences(parsedRefs.value)
    toastStore.showToast(`成功创建 ${parsedRefs.value.length} 条文献`)
    bibtexText.value = ''
    parsedRefs.value = []
    close()
  } catch (e) {
    toastStore.showToast('创建失败: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

async function onSubmit() {
  if (!form.value.title.trim()) {
    toastStore.showToast('请输入文献标题', 'error')
    return
  }
  saving.value = true
  try {
    await refsStore.addReferences([{
      type: form.value.type,
      title: form.value.title.trim(),
      authors: parseAuthors(form.value.authors),
      year: form.value.year.trim(),
      journal: form.value.journal.trim(),
      volume: form.value.volume.trim(),
      issue: form.value.issue.trim(),
      pages: form.value.pages.trim(),
      doi: form.value.doi.trim(),
      abstract: form.value.abstract.trim(),
      keywords: parseKeywords(form.value.keywords),
    }])
    toastStore.showToast('文献创建成功')
    resetForm()
    bibtexText.value = ''
    parsedRefs.value = []
    close()
  } catch (e) {
    toastStore.showToast('创建失败: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

function close() {
  visible.value = false
}

function onAfterLeave() {
  resetForm()
  bibtexText.value = ''
  parsedRefs.value = []
  bibtexError.value = ''
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal" @after-leave="onAfterLeave">
      <div v-if="visible" class="ref-editor-overlay" @click.self="close">
        <div class="ref-editor">
          <div class="ref-editor-header">
            <span>新建文献</span>
            <button class="pwd-modal-close" @click="close">&times;</button>
          </div>

          <div class="ref-editor-body">
            <!-- BibTeX 一键解析区 -->
            <div class="bibtex-collapse">
              <div class="bibtex-collapse-header" @click="bibtexText = bibtexText || ''">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
                </svg>
                <span>BibTeX 一键解析</span>
                <svg v-if="!bibtexText && parsedRefs.length === 0" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="bibtex-chevron">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
              <div class="bibtex-collapse-body">
                <textarea
                  v-model="bibtexText"
                  class="bibtex-textarea"
                  rows="6"
                  placeholder='@article{example,
  author = {Smith, John and Doe, Jane},
  title = {An Example Article},
  journal = {Journal of Examples},
  year = {2024},
  volume = {10},
  pages = {100-200}
}'
                ></textarea>
                <div class="bibtex-actions">
                  <button class="btn-save-note" style="font-size:13px;padding:6px 14px" @click="onBibtexParse">解析并填充表单</button>
                  <button
                    v-if="parsedRefs.length > 1"
                    class="btn-cancel-note"
                    style="font-size:13px;padding:6px 14px"
                    :disabled="saving"
                    @click="onBibtexImportAll"
                  >全部导入 ({{ parsedRefs.length }} 条)</button>
                </div>
                <div v-if="bibtexError" class="bibtex-error">{{ bibtexError }}</div>

                <!-- 多条目切换 -->
                <div v-if="parsedRefs.length > 1" class="bibtex-entry-tabs">
                  <span class="bibtex-entry-label">解析出 {{ parsedRefs.length }} 条文献，点击切换填充：</span>
                  <div class="bibtex-entry-list">
                    <button
                      v-for="(ref, idx) in parsedRefs"
                      :key="idx"
                      class="bibtex-entry-chip"
                      :class="{ active: parsedActiveIndex === idx }"
                      @click="selectParsedRef(idx)"
                    >{{ ref.title }}</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 表单 -->
            <div class="ref-editor-form">
              <div class="form-field">
                <label>标题 *</label>
                <input type="text" v-model="form.title" placeholder="请输入文献标题" />
              </div>
              <div class="form-row form-row-2">
                <div class="form-field">
                  <label>类型</label>
                  <select v-model="form.type">
                    <option v-for="t in REF_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
                  </select>
                </div>
                <div class="form-field">
                  <label>年份</label>
                  <input type="text" v-model="form.year" placeholder="如 2024" />
                </div>
              </div>
              <div class="form-field">
                <label>作者</label>
                <input type="text" v-model="form.authors" placeholder="多个作者以逗号或分号分隔" />
              </div>
              <div class="form-field">
                <label>期刊 / 出版物</label>
                <input type="text" v-model="form.journal" placeholder="请输入期刊或出版物名称" />
              </div>
              <div class="form-row form-row-3">
                <div class="form-field">
                  <label>卷</label>
                  <input type="text" v-model="form.volume" placeholder="卷" />
                </div>
                <div class="form-field">
                  <label>期</label>
                  <input type="text" v-model="form.issue" placeholder="期" />
                </div>
                <div class="form-field">
                  <label>页码</label>
                  <input type="text" v-model="form.pages" placeholder="如 100-200" />
                </div>
              </div>
              <div class="form-field">
                <label>DOI</label>
                <input type="text" v-model="form.doi" placeholder="如 10.1234/example" />
              </div>
              <div class="form-field">
                <label>摘要</label>
                <textarea v-model="form.abstract" rows="4" placeholder="请输入摘要"></textarea>
              </div>
              <div class="form-field">
                <label>关键词</label>
                <input type="text" v-model="form.keywords" placeholder="多个关键词以逗号或分号分隔" />
              </div>
            </div>

            <div class="ref-editor-actions">
              <button class="btn-cancel-note" @click="close">取消</button>
              <button class="btn-save-note" :disabled="saving" @click="onSubmit">
                {{ saving ? '保存中...' : '创建文献' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
