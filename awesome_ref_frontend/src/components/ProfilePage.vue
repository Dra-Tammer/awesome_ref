<script setup>
import { onMounted, computed } from 'vue'
import { useStats } from '../composables/useStats.js'

const { stats, loading, loadStats } = useStats()

onMounted(() => {
  loadStats()
})

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
  if (!stats.value) return 1
  const vals = Object.values(stats.value.type_distribution)
  return Math.max(...vals, 1)
})

function barPercent(count) {
  return (count / maxTypeCount.value) * 100
}

const maxYearCount = computed(() => {
  if (!stats.value) return 1
  const vals = Object.values(stats.value.year_distribution)
  return Math.max(...vals, 1)
})

function yearBarHeight(count) {
  return (count / maxYearCount.value) * 160
}

const hasData = computed(() => stats.value && stats.value.total_references > 0)
</script>

<template>
  <div class="profile-page">
    <div v-if="loading" class="profile-loading">
      <div class="loading-spinner">
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        <p>加载统计数据...</p>
      </div>
    </div>

    <div v-else-if="stats" class="profile-content">
      <!-- User Hero -->
      <section class="profile-hero">
        <div class="profile-avatar">{{ (stats.username || '?')[0].toUpperCase() }}</div>
        <h2 class="profile-username">{{ stats.username }}</h2>
        <p class="profile-since">注册于 {{ formatDate(stats.registration_date) }}</p>
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
          <div class="stat-number">{{ stats.total_references }}</div>
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
          <div class="stat-number">{{ stats.total_standalone_notes }}</div>
          <div class="stat-label">独立笔记</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="stat-number">{{ stats.total_groups }}</div>
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
          <div class="stat-number">{{ stats.pdf_attachment_rate }}%</div>
          <div class="stat-label">PDF 附件率</div>
        </div>
      </section>

      <template v-if="hasData">
        <!-- Type Distribution -->
        <section class="profile-section" v-if="Object.keys(stats.type_distribution).length > 0">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            文献类型分布
          </div>
          <div class="bar-chart">
            <div v-for="(count, type) in stats.type_distribution" :key="type" class="bar-row">
              <span class="bar-label">{{ typeName(type) }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barPercent(count) + '%' }"></div>
              </div>
              <span class="bar-value">{{ count }}</span>
            </div>
          </div>
        </section>

        <!-- Year Distribution -->
        <section class="profile-section" v-if="Object.keys(stats.year_distribution).length > 0">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            年份分布
          </div>
          <div class="year-chart-wrapper">
            <div class="year-chart">
              <div v-for="(count, year) in stats.year_distribution" :key="year" class="year-bar-wrapper">
                <div class="year-bar" :style="{ height: yearBarHeight(count) + 'px' }"></div>
                <span class="year-label">{{ year }}</span>
              </div>
            </div>
          </div>
        </section>

        <div class="profile-two-col">
          <!-- Top Journals -->
          <section class="profile-section" v-if="stats.top_journals.length > 0">
            <div class="profile-section-header">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
              期刊 Top 10
            </div>
            <div class="ranking-list">
              <div v-for="(item, i) in stats.top_journals" :key="i" class="ranking-item">
                <span class="ranking-rank">{{ i + 1 }}</span>
                <span class="ranking-name" :title="item.name">{{ item.name }}</span>
                <span class="ranking-count">{{ item.count }}</span>
              </div>
            </div>
          </section>

          <!-- Top Authors -->
          <section class="profile-section" v-if="stats.top_authors.length > 0">
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
              <div v-for="(item, i) in stats.top_authors" :key="i" class="ranking-item">
                <span class="ranking-rank">{{ i + 1 }}</span>
                <span class="ranking-name" :title="item.name">{{ item.name }}</span>
                <span class="ranking-count">{{ item.count }}</span>
              </div>
            </div>
          </section>
        </div>

        <!-- Keywords -->
        <section class="profile-section" v-if="stats.top_keywords.length > 0">
          <div class="profile-section-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
              <line x1="7" y1="7" x2="7.01" y2="7"/>
            </svg>
            关键词
          </div>
          <div class="keyword-cloud">
            <span v-for="item in stats.top_keywords" :key="item.keyword" class="keyword-cloud-tag">
              {{ item.keyword }}
              <span class="keyword-count">({{ item.count }})</span>
            </span>
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
      <section class="profile-section" v-if="stats.recent_activity.length > 0">
        <div class="profile-section-header">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          最近活动
        </div>
        <div class="timeline">
          <div v-for="(item, i) in stats.recent_activity" :key="i" class="timeline-item">
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
</template>
