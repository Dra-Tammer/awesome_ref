<script setup>
import { ref, onMounted, computed } from 'vue'
import { useStatsStore } from '../stores/stats.js'
import { useAuthStore } from '../stores/auth.js'
import { useToastStore } from '../stores/toast.js'

const statsStore = useStatsStore()
const auth = useAuthStore()
const toastStore = useToastStore()

onMounted(() => {
  statsStore.loadStats()
})

const showPwdModal = ref(false)
const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')
const pwdError = ref('')
const pwdLoading = ref(false)

function openPwdModal() {
  oldPwd.value = ''
  newPwd.value = ''
  confirmPwd.value = ''
  pwdError.value = ''
  showPwdModal.value = true
}

async function onPwdSubmit() {
  pwdError.value = ''
  pwdLoading.value = true
  try {
    await auth.changePassword(oldPwd.value, newPwd.value, confirmPwd.value)
    showPwdModal.value = false
    auth.logout()
  } catch (e) {
    pwdError.value = e.message
  } finally {
    pwdLoading.value = false
  }
}

const showExportModal = ref(false)

async function doExport(format, ext) {
  showExportModal.value = false
  try {
    const res = await fetch(`/api/export?format=${format}`, { headers: auth.getHeaders() })
    if (!res.ok) throw new Error('导出失败')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    const date = new Date().toISOString().slice(0, 10)
    a.href = url
    a.download = `awesomeref-export-${date}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
    toastStore.showToast('导出成功')
  } catch (e) {
    toastStore.showToast('导出失败: ' + e.message, 'error')
  }
}

const typeLabels = {
  JOUR: '期刊论文', BOOK: '书籍', CHAP: '章节', CONF: '会议论文',
  THES: '学位论文', RPRT: '报告', GEN: '其他', NEWS: '新闻',
  MGZN: '杂志', PAT: '专利', UNPB: '未发表',
}

function typeName(key) {
  return typeLabels[key] || key || '其他'
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`
}

function formatShortDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const maxTypeCount = computed(() => {
  if (!statsStore.stats) return 1
  const vals = Object.values(statsStore.stats.type_distribution)
  return Math.max(...vals, 1)
})

function barPercent(count) {
  return (count / maxTypeCount.value) * 100
}

const maxYearCount = computed(() => {
  if (!statsStore.stats) return 1
  const vals = Object.values(statsStore.stats.year_distribution)
  return Math.max(...vals, 1)
})

function yearBarHeight(count) {
  return (count / maxYearCount.value) * 160
}

const maxMonthlyCount = computed(() => {
  if (!statsStore.stats?.monthly_trend) return 1
  return Math.max(...statsStore.stats.monthly_trend.map(m => m.count), 1)
})

function monthlyBarHeight(count) {
  return (count / maxMonthlyCount.value) * 120
}

function shortMonth(ym) {
  if (!ym) return ''
  const parts = ym.split('-')
  return parts[1] + '月'
}

const hasData = computed(() => statsStore.stats && statsStore.stats.total_references > 0)

const topKeywordCount = computed(() => {
  if (!statsStore.stats?.top_keywords?.length) return 1
  return Math.max(...statsStore.stats.top_keywords.map(k => k.count), 1)
})

function keywordSize(count) {
  const ratio = count / topKeywordCount.value
  return 0.75 + ratio * 0.75 // 0.75rem ~ 1.5rem
}

const topJournalCount = computed(() => {
  if (!statsStore.stats?.top_journals?.length) return 1
  return statsStore.stats.top_journals[0]?.count || 1
})

function journalBarPercent(count) {
  return (count / topJournalCount.value) * 100
}

const topAuthorCount = computed(() => {
  if (!statsStore.stats?.top_authors?.length) return 1
  return statsStore.stats.top_authors[0]?.count || 1
})

function authorBarPercent(count) {
  return (count / topAuthorCount.value) * 100
}
</script>

<template>
  <div class="profile-page">
    <div v-if="statsStore.loading" class="profile-loading">
      <div class="loading-spinner">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        <p>加载统计数据...</p>
      </div>
    </div>

    <div v-else-if="statsStore.stats" class="profile-content">
      <!-- User Hero -->
      <section class="profile-hero">
        <div class="profile-avatar">{{ (statsStore.stats.username || '?')[0].toUpperCase() }}</div>
        <h2 class="profile-username">{{ statsStore.stats.username }}</h2>
        <p class="profile-since">注册于 {{ formatDate(statsStore.stats.registration_date) }}</p>
        <div class="profile-hero-actions">
          <button class="profile-action-btn" @click="openPwdModal" title="修改密码">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            修改密码
          </button>
          <button class="profile-action-btn" @click="showExportModal = true" title="导出数据">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            导出数据
          </button>
        </div>
      </section>

      <!-- Overview Cards -->
      <section class="profile-overview">
        <div class="stat-card">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <div class="stat-number">{{ statsStore.stats.total_references }}</div>
          <div class="stat-label">文献总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
            </svg>
          </div>
          <div class="stat-number">{{ statsStore.stats.total_standalone_notes + statsStore.stats.total_ref_notes }}</div>
          <div class="stat-label">笔记总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="stat-number">{{ statsStore.stats.total_groups }}</div>
          <div class="stat-label">分组数</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <path d="M12 18v-6"/><path d="M9 15l3 3 3-3"/>
            </svg>
          </div>
          <div class="stat-number">{{ statsStore.stats.pdf_attachment_rate }}%</div>
          <div class="stat-label">PDF 附件率</div>
        </div>
      </section>

      <!-- Quick Stats Row -->
      <section class="profile-quick-stats" v-if="hasData">
        <div class="quick-stat">
          <span class="quick-stat-value">{{ statsStore.stats.refs_this_week }}</span>
          <span class="quick-stat-label">本周新增文献</span>
        </div>
        <div class="quick-stat-divider"></div>
        <div class="quick-stat">
          <span class="quick-stat-value">{{ statsStore.stats.refs_this_month }}</span>
          <span class="quick-stat-label">本月新增文献</span>
        </div>
        <div class="quick-stat-divider"></div>
        <div class="quick-stat">
          <span class="quick-stat-value">{{ statsStore.stats.notes_this_week }}</span>
          <span class="quick-stat-label">本周新增笔记</span>
        </div>
        <div class="quick-stat-divider"></div>
        <div class="quick-stat">
          <span class="quick-stat-value">{{ statsStore.stats.note_coverage }}%</span>
          <span class="quick-stat-label">文献笔记覆盖率</span>
        </div>
      </section>

      <template v-if="hasData">
        <!-- Monthly Trend -->
        <section class="profile-section" v-if="statsStore.stats.monthly_trend && statsStore.stats.monthly_trend.some(m => m.count > 0)">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            近 12 个月添加趋势
          </div>
          <div class="year-chart-wrapper">
            <div class="year-chart">
              <div v-for="item in statsStore.stats.monthly_trend" :key="item.month" class="year-bar-wrapper">
                <div class="year-bar-group">
                  <span v-if="item.count > 0" class="year-bar-value">{{ item.count }}</span>
                  <div class="year-bar" :style="{ height: monthlyBarHeight(item.count) + 'px' }"></div>
                </div>
                <span class="year-label">{{ shortMonth(item.month) }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Type Distribution -->
        <section class="profile-section" v-if="Object.keys(statsStore.stats.type_distribution).length > 0">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            文献类型分布
          </div>
          <div class="bar-chart">
            <div v-for="(count, type) in statsStore.stats.type_distribution" :key="type" class="bar-row">
              <span class="bar-label">{{ typeName(type) }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barPercent(count) + '%' }"></div>
              </div>
              <span class="bar-value">{{ count }}</span>
            </div>
          </div>
        </section>

        <!-- Year Distribution -->
        <section class="profile-section" v-if="Object.keys(statsStore.stats.year_distribution).length > 0">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            年份分布
            <span v-if="statsStore.stats.year_span" class="profile-section-badge">{{ statsStore.stats.year_span }} · {{ statsStore.stats.unique_years }} 个年份</span>
          </div>
          <div class="year-chart-wrapper">
            <div class="year-chart">
              <div v-for="(count, year) in statsStore.stats.year_distribution" :key="year" class="year-bar-wrapper">
                <div class="year-bar-group">
                  <span v-if="count > 0" class="year-bar-value">{{ count }}</span>
                  <div class="year-bar" :style="{ height: yearBarHeight(count) + 'px' }"></div>
                </div>
                <span class="year-label">{{ year }}</span>
              </div>
            </div>
          </div>
        </section>

        <div class="profile-two-col">
          <!-- Top Journals -->
          <section class="profile-section" v-if="statsStore.stats.top_journals.length > 0">
            <div class="profile-section-header">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
              期刊 Top 10
            </div>
            <div class="ranking-list">
              <div v-for="(item, i) in statsStore.stats.top_journals" :key="i" class="ranking-item ranking-item-bar">
                <span class="ranking-rank">{{ i + 1 }}</span>
                <div class="ranking-info">
                  <span class="ranking-name" :title="item.name">{{ item.name }}</span>
                  <div class="ranking-bar-track">
                    <div class="ranking-bar-fill" :style="{ width: journalBarPercent(item.count) + '%' }"></div>
                  </div>
                </div>
                <span class="ranking-count">{{ item.count }}</span>
              </div>
            </div>
          </section>

          <!-- Top Authors -->
          <section class="profile-section" v-if="statsStore.stats.top_authors.length > 0">
            <div class="profile-section-header">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              作者 Top 10
            </div>
            <div class="ranking-list">
              <div v-for="(item, i) in statsStore.stats.top_authors" :key="i" class="ranking-item ranking-item-bar">
                <span class="ranking-rank">{{ i + 1 }}</span>
                <div class="ranking-info">
                  <span class="ranking-name" :title="item.name">{{ item.name }}</span>
                  <div class="ranking-bar-track">
                    <div class="ranking-bar-fill" :style="{ width: authorBarPercent(item.count) + '%' }"></div>
                  </div>
                </div>
                <span class="ranking-count">{{ item.count }}</span>
              </div>
            </div>
          </section>
        </div>

        <!-- Keywords -->
        <section class="profile-section" v-if="statsStore.stats.top_keywords.length > 0">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
              <line x1="7" y1="7" x2="7.01" y2="7"/>
            </svg>
            关键词
          </div>
          <div class="keyword-cloud">
            <span v-for="item in statsStore.stats.top_keywords" :key="item.keyword" class="keyword-cloud-tag"
              :style="{ fontSize: keywordSize(item.count) + 'rem' }">
              {{ item.keyword }}
              <span class="keyword-count">({{ item.count }})</span>
            </span>
          </div>
        </section>

        <!-- Most Annotated References -->
        <section class="profile-section" v-if="statsStore.stats.most_annotated && statsStore.stats.most_annotated.length > 0">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
            笔记最多的文献
          </div>
          <div class="ranking-list">
            <div v-for="(item, i) in statsStore.stats.most_annotated" :key="i" class="ranking-item">
              <span class="ranking-rank">{{ i + 1 }}</span>
              <span class="ranking-name" :title="item.title">{{ item.title }}</span>
              <span class="ranking-count">{{ item.count }} 条</span>
            </div>
          </div>
        </section>

        <!-- Deep Insights -->
        <section class="profile-section">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
            </svg>
            深入洞察
          </div>
          <div class="insight-grid">
            <div class="insight-card">
              <span class="insight-card-value">{{ statsStore.stats.avg_authors }}</span>
              <span class="insight-card-label">平均作者数 / 篇</span>
            </div>
            <div class="insight-card">
              <span class="insight-card-value">{{ statsStore.stats.refs_with_abstract }}</span>
              <span class="insight-card-label">有摘要的文献</span>
            </div>
            <div class="insight-card">
              <span class="insight-card-value">{{ statsStore.stats.refs_with_doi }}</span>
              <span class="insight-card-label">有 DOI 的文献</span>
            </div>
            <div class="insight-card">
              <span class="insight-card-value">{{ statsStore.stats.pdf_size_mb }} MB</span>
              <span class="insight-card-label">PDF 存储占用</span>
            </div>
            <div class="insight-card">
              <span class="insight-card-value">{{ statsStore.stats.note_files }}</span>
              <span class="insight-card-label">笔记文件数</span>
            </div>
            <div class="insight-card">
              <span class="insight-card-value">{{ statsStore.stats.img_count }}</span>
              <span class="insight-card-label">上传图片数</span>
            </div>
            <div class="insight-card" v-if="statsStore.stats.trash_count > 0">
              <span class="insight-card-value">{{ statsStore.stats.trash_count }}</span>
              <span class="insight-card-label">回收站文献</span>
            </div>
            <div class="insight-card" v-if="statsStore.stats.year_span">
              <span class="insight-card-value">{{ statsStore.stats.year_span }}</span>
              <span class="insight-card-label">文献年份跨度</span>
            </div>
          </div>
        </section>
      </template>

      <div v-else class="profile-section">
        <div class="profile-empty">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" stroke-width="1.5" opacity="0.4">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
          </svg>
          <p>还没有文献数据，添加一些文献后这里会展示有趣的统计信息</p>
        </div>
      </div>

      <!-- Recent Activity -->
      <section class="profile-section" v-if="statsStore.stats.recent_activity.length > 0">
        <div class="profile-section-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          最近活动
        </div>
        <div class="timeline">
          <div v-for="(item, i) in statsStore.stats.recent_activity" :key="i" class="timeline-item">
            <div class="timeline-dot" :class="{ 'note-dot': item.type === 'note' }"></div>
            <div class="timeline-date">{{ formatShortDate(item.date) }}</div>
            <div class="timeline-desc">
              <span class="timeline-type" :class="{ 'note-type': item.type === 'note' }">
                {{ item.type === 'note' ? '笔记' : '文献' }}
              </span>
              {{ item.title }}
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>

  <!-- 修改密码弹框 -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showPwdModal" class="pwd-modal-overlay" @click.self="showPwdModal = false">
        <div class="pwd-modal">
          <div class="pwd-modal-header">
            <span>修改密码</span>
            <button class="pwd-modal-close" @click="showPwdModal = false">&times;</button>
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
      <div v-if="showExportModal" class="pwd-modal-overlay" @click.self="showExportModal = false">
        <div class="pwd-modal import-modal">
          <div class="pwd-modal-header">
            <span>选择导出格式</span>
            <button class="pwd-modal-close" @click="showExportModal = false">&times;</button>
          </div>
          <div class="import-modal-body">
            <button class="import-option" @click="doExport('json', 'json')">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><path d="M9 15v-2h2a1 1 0 1 0 0-2H9"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">JSON</span>
                <span class="import-option-desc">导出完整备份，可用于数据恢复或迁移</span>
              </div>
            </button>
            <button class="import-option" @click="doExport('md', 'md')">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><polyline points="12 11 16 13 12 15"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">Markdown</span>
                <span class="import-option-desc">可读性强，支持版本管理，方便在编辑器中查看</span>
              </div>
            </button>
            <button class="import-option" @click="doExport('pdf', 'pdf')">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <div class="import-option-text">
                <span class="import-option-title">PDF</span>
                <span class="import-option-desc">排版固定，适合打印和分享</span>
              </div>
            </button>
            <button class="import-option" @click="doExport('docx', 'docx')">
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
</template>
