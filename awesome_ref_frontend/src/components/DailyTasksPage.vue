<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useDailyTasksStore } from '../stores/dailyTasks.js'

const dailyTasksStore = useDailyTasksStore()

const newTitle = ref('')
const openNote = ref(null)
const noteVal = ref('')
const adding = ref(false)
const editId = ref(null)
const editVal = ref('')

const quotes = [
  '千里之行，始于足下', '不积跬步，无以至千里', '今日事，今日毕',
  '把大问题拆成小问题，逐个击破', '完成比完美更重要', '每一个小任务都是一次胜利',
  '坚持就是胜利，一步一步来', '专注于当下，别想太多', '行动是治愈焦虑的良药', '你比你想象的更强大',
]

const todayStr = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})
const curDate = computed(() => dailyTasksStore.viewingDate || todayStr.value)
const curDateFmt = computed(() => {
  const p = curDate.value.split('-')
  return `${p[0]} 年 ${parseInt(p[1])} 月 ${parseInt(p[2])} 日`
})
const curWeekday = computed(() => {
  const p = curDate.value.split('-')
  return ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'][new Date(+p[0], +p[1] - 1, +p[2]).getDay()]
})
const isToday = computed(() => curDate.value === todayStr.value)
const hasPlan = computed(() => !!dailyTasksStore.viewingPlan)
const quote = computed(() => quotes[new Date().getDate() % quotes.length])
const tasks = computed(() => dailyTasksStore.viewingPlan?.tasks || [])
const total = computed(() => tasks.value.length)
const done = computed(() => tasks.value.filter(t => t.status === 'done').length)
const partial = computed(() => tasks.value.filter(t => t.status === 'partial').length)
const rate = computed(() => total.value === 0 ? 0 : Math.round(((done.value + partial.value * 0.5) / total.value) * 100))

const rR = 18, rC = 2 * Math.PI * rR
const rOff = computed(() => rC * (1 - rate.value / 100))

function fmtD(d) { return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}` }
function shiftD(s, n) { const p = s.split('-'); const d = new Date(+p[0], +p[1] - 1, +p[2]); d.setDate(d.getDate() + n); return fmtD(d) }
function isFut(s) { return s > todayStr.value }

async function prev() { await dailyTasksStore.loadPlanByDate(shiftD(curDate.value, -1)) }
async function next() { const n = shiftD(curDate.value, 1); if (!isFut(n)) await dailyTasksStore.loadPlanByDate(n) }

const hm = computed(() => {
  const map = {}
  for (const i of dailyTasksStore.heatmapData) map[i.date] = i

  const today = new Date()
  const endDow = today.getDay()
  const endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const start = new Date(endDate)
  start.setDate(start.getDate() - endDow - 51 * 7)

  const weeks = []
  const months = []
  let lastMonth = -1
  const cur = new Date(start)

  for (let w = 0; w < 52; w++) {
    const week = []
    for (let d = 0; d < 7; d++) {
      const ds = fmtD(cur)
      const month = cur.getMonth()
      if (d === 0 && month !== lastMonth) {
        months.push({ label: (month + 1) + '月', col: w })
        lastMonth = month
      }
      week.push({ date: ds, data: map[ds] || null, isToday: ds === todayStr.value })
      cur.setDate(cur.getDate() + 1)
    }
    weeks.push(week)
  }

  return { weeks, months }
})

function hLevel(i) {
  if (!i?.data || i.data.total === 0) return 0
  const r = (i.data.done + i.data.partial * 0.5) / i.data.total
  return r >= .9 ? 4 : r >= .6 ? 3 : r >= .3 ? 2 : 1
}

function cellCls(d) {
  if (!d) return {}
  const lv = hLevel(d)
  return { l0: lv === 0, l1: lv === 1, l2: lv === 2, l3: lv === 3, l4: lv === 4, today: d.isToday, sel: d.date === curDate.value }
}

const tipD = ref(''), tipI = ref(''), tipOn = ref(false), tipX = ref(0), tipY = ref(0)
function tipShow(e, i) {
  if (!i?.data) { tipOn.value = false; return }
  tipD.value = i.date; tipI.value = `${i.data.total} 个任务 · 完成 ${i.data.done} · 部分 ${i.data.partial}`
  tipOn.value = true
  const r = e.target.getBoundingClientRect(); tipX.value = r.left + r.width / 2; tipY.value = r.top - 8
}
function tipHide() { tipOn.value = false }

const recent = computed(() => dailyTasksStore.heatmapData.slice().sort((a, b) => b.date.localeCompare(a.date)).slice(0, 20))
const hmKey = ref(0)

async function refreshHm() { await dailyTasksStore.loadHeatmap(); hmKey.value++ }

async function doAdd() {
  const t = newTitle.value.trim(); if (!t) return
  adding.value = true; await dailyTasksStore.addTask(t); newTitle.value = ''; adding.value = false
  await nextTick(); const el = document.querySelector('.dt-list'); if (el) el.scrollTop = 0
  await refreshHm()
}
const stOrd = ['pending', 'partial', 'done']
async function cycle(t) { await dailyTasksStore.updateTask(t.id, { status: stOrd[(stOrd.indexOf(t.status) + 1) % 3] }); await refreshHm() }
function togNote(t) { editId.value = null; openNote.value = openNote.value === t.id ? null : (noteVal.value = t.note || '', t.id) }
async function saveN(t) { await dailyTasksStore.updateTask(t.id, { note: noteVal.value }); openNote.value = null }
async function delT(t) { await dailyTasksStore.deleteTask(t.id); await refreshHm() }
function startEd(t) { openNote.value = null; editId.value = t.id; editVal.value = t.title; nextTick(() => { const el = document.querySelector('.dt-ed'); if (el) { el.focus(); el.select() } }) }
async function saveEd(t) { const v = editVal.value.trim(); if (v && v !== t.title) await dailyTasksStore.updateTask(t.id, { title: v }); editId.value = null }
function cancEd() { editId.value = null }

async function handleCreatePlan() {
  await dailyTasksStore.createPlan(curDate.value)
  await refreshHm()
}

const calOpen = ref(false)
const calYear = ref(0)
const calMonth = ref(0)

function openCal() {
  const p = curDate.value.split('-')
  calYear.value = +p[0]
  calMonth.value = +p[1] - 1
  calOpen.value = true
}

function calNav(d) {
  calMonth.value += d
  if (calMonth.value < 0) { calMonth.value = 11; calYear.value-- }
  if (calMonth.value > 11) { calMonth.value = 0; calYear.value++ }
}

const calDays = computed(() => {
  const first = new Date(calYear.value, calMonth.value, 1)
  const last = new Date(calYear.value, calMonth.value + 1, 0)
  const startDow = first.getDay()
  const days = []
  for (let i = 0; i < startDow; i++) days.push(null)
  for (let d = 1; d <= last.getDate(); d++) days.push(d)
  return days
})

function calDateStr(d) {
  return `${calYear.value}-${String(calMonth.value + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

function pickDay(d) {
  const ds = calDateStr(d)
  if (!isFut(ds)) { dailyTasksStore.loadPlanByDate(ds); calOpen.value = false }
}

function onDocClick(e) {
  if (calOpen.value && !e.target.closest('.dt-cal') && !e.target.closest('.dt-dd-btn')) {
    calOpen.value = false
  }
}

onMounted(async () => {
  await Promise.all([dailyTasksStore.loadToday(), dailyTasksStore.loadHeatmap()])
  document.addEventListener('click', onDocClick)
})
</script>

<template>
  <div class="dt-page">
    <div class="dt-card">
      <!-- Date -->
      <div class="dt-hd">
        <button class="dt-nb" @click="prev"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg></button>
        <div class="dt-di">
          <span class="dt-dd dt-dd-btn" @click="openCal" title="点击选择日期">
            {{ curDateFmt }}
          </span>
          <span class="dt-dw">{{ curWeekday }}</span>

          <!-- Calendar dropdown -->
          <Transition name="dt-cal">
            <div v-if="calOpen" class="dt-cal" @click.stop>
              <div class="dt-cal-hd">
                <button class="dt-cal-nav" @click="calNav(-1)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg></button>
                <span class="dt-cal-ym">{{ calYear }} 年 {{ calMonth + 1 }} 月</span>
                <button class="dt-cal-nav" @click="calNav(1)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></button>
              </div>
              <div class="dt-cal-week">
                <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
              </div>
              <div class="dt-cal-grid">
                <span v-for="(d, i) in calDays" :key="i"
                  class="dt-cal-day"
                  :class="{ empty: !d, today: d && calDateStr(d) === todayStr, sel: d && calDateStr(d) === curDate, future: d && isFut(calDateStr(d)) }"
                  @click="d && pickDay(d)">{{ d }}</span>
              </div>
              <div class="dt-cal-ft">
                <button class="dt-cal-today" @click="dailyTasksStore.loadToday(); calOpen = false">今天</button>
              </div>
            </div>
          </Transition>
        </div>
        <button class="dt-nb" @click="next" :disabled="curDate >= todayStr"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></button>
      </div>

      <!-- Stats -->
      <div class="dt-st">
        <div class="dt-rg">
          <svg width="40" height="40" viewBox="0 0 44 44"><circle cx="22" cy="22" :r="rR" fill="none" stroke="var(--border)" stroke-width="3" opacity=".4"/><circle cx="22" cy="22" :r="rR" fill="none" stroke="var(--accent)" stroke-width="3" stroke-linecap="round" :stroke-dasharray="rC" :stroke-dashoffset="rOff" transform="rotate(-90 22 22)" style="transition:stroke-dashoffset .8s cubic-bezier(.22,1,.36,1)"/></svg>
          <span class="dt-rgn">{{ rate }}%</span>
        </div>
        <span class="dt-sp"></span>
        <span class="dt-sv"><b>{{ total }}</b> 任务</span>
        <span class="dt-sp"></span>
        <span class="dt-sv dt-ok"><b>{{ done }}</b> 完成</span>
        <span class="dt-sp"></span>
        <span class="dt-sv dt-wi"><b>{{ total - done }}</b> 未完成</span>
      </div>

      <p v-if="isToday" class="dt-qt">{{ quote }}</p>

      <!-- Input -->
      <Transition name="dt-in">
        <div v-if="hasPlan" class="dt-in">
          <input v-model="newTitle" class="dt-ipt" :placeholder="isToday ? '写下今天要完成的一件小事...' : '为这天添加任务...'" @keydown.enter="doAdd" :disabled="adding" />
          <button class="dt-ia" @click="doAdd" :disabled="adding || !newTitle.trim()"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></button>
        </div>
      </Transition>

      <!-- Tasks / Empty states -->
      <Transition name="dt-view" mode="out-in">
        <div v-if="!hasPlan" :key="curDate + '-noplan'" class="dt-em">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity=".2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          <p>{{ isToday ? '还没有任务，写下一个小目标开始吧' : '这天没有计划记录' }}</p>
          <button v-if="!isToday" class="dt-create-btn" @click="handleCreatePlan">创建计划</button>
        </div>
        <div v-else-if="tasks.length === 0" :key="curDate + '-empty'" class="dt-em">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity=".2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
          <p>还没有任务，添加一个吧</p>
        </div>
        <div v-else :key="curDate + '-list'" class="dt-list">
          <TransitionGroup name="dt-a">
            <div v-for="t in tasks" :key="t.id" class="dt-tk" :class="{ 'is-done': t.status === 'done', 'is-partial': t.status === 'partial' }">
              <button class="dt-ck" :class="'s-' + t.status" @click="cycle(t)">
                <Transition name="dt-check" mode="out-in">
                  <svg v-if="t.status === 'pending'" key="pending" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/></svg>
                  <svg v-else-if="t.status === 'partial'" key="partial" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18" fill="currentColor" opacity=".25"/></svg>
                  <svg v-else key="done" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><polyline points="8 12 11 15 16 9"/></svg>
                </Transition>
              </button>
              <div class="dt-tb">
                <Transition name="dt-edit" mode="out-in">
                  <input v-if="editId === t.id" key="edit" v-model="editVal" class="dt-ed" @keydown.enter="saveEd(t)" @keydown.escape="cancEd" @blur="saveEd(t)" />
                  <span v-else key="view" class="dt-tx" :class="{ done: t.status === 'done' }" @dblclick="startEd(t)">{{ t.title }}</span>
                </Transition>
                <div v-if="t.note && openNote !== t.id" class="dt-np">{{ t.note }}</div>
                <Transition name="dt-ne">
                  <div v-if="openNote === t.id" class="dt-ne-wrap">
                    <textarea v-model="noteVal" class="dt-nta" placeholder="记录完成情况..." rows="2"></textarea>
                    <div class="dt-neb"><button class="dt-nes" @click="saveN(t)">保存</button><button class="dt-nec" @click="openNote = null">取消</button></div>
                  </div>
                </Transition>
              </div>
              <div class="dt-ta">
                <button class="dt-ab" @click="startEd(t)" title="编辑"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
                <button class="dt-ab" @click="togNote(t)" title="备注"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></button>
                <button class="dt-ab dt-x" @click="delT(t)" title="删除"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
              </div>
            </div>
          </TransitionGroup>
        </div>
      </Transition>

      <!-- Heatmap (GitHub style) -->
      <div class="dt-hm-sec" :key="hmKey">
        <h3 class="dt-sec-hd"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>年度记录</h3>
        <div class="gh-graph">
          <!-- Month labels row -->
          <div class="gh-head">
            <span></span><!-- spacer for day-label column -->
            <span v-for="(m, i) in hm.months" :key="i"
              class="gh-head-label"
              :style="{ gridColumn: (m.col + 2) + ' / ' + (i + 1 < hm.months.length ? hm.months[i + 1].col + 2 : 54) }">{{ m.label }}</span>
          </div>
          <!-- Day rows -->
          <div class="gh-body">
            <template v-for="(dayLabel, row) in ['日','一','二','三','四','五','六']" :key="row">
              <span class="gh-day-lbl">{{ dayLabel }}</span>
              <span v-for="(week, col) in hm.weeks" :key="col"
                class="gh-cell"
                :class="cellCls(week[row])"
                @mouseenter="tipShow($event, week[row])" @mouseleave="tipHide"
                @click="!isFut(week[row].date) && dailyTasksStore.loadPlanByDate(week[row].date)"></span>
            </template>
          </div>
          <!-- Legend -->
          <div class="gh-legend">
            <span class="gh-ll">少</span>
            <span class="gh-cell l0"></span>
            <span class="gh-cell l1"></span>
            <span class="gh-cell l2"></span>
            <span class="gh-cell l3"></span>
            <span class="gh-cell l4"></span>
            <span class="gh-ll">多</span>
          </div>
        </div>
      </div>

      <!-- Recent -->
      <div class="dt-rc-sec">
        <h3 class="dt-sec-hd"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>近期计划</h3>
        <div class="dt-rc">
          <div v-for="i in recent" :key="i.date" class="dt-ri" :class="{ active: i.date === curDate }" @click="!isFut(i.date) && dailyTasksStore.loadPlanByDate(i.date)">
            <span class="dt-rd">{{ i.date.slice(5) }}</span>
            <div class="dt-rb"><div class="dt-rf" :style="{ width: i.total ? ((i.done + i.partial * .5) / i.total * 100) + '%' : '0%' }"></div></div>
            <span class="dt-rn">{{ i.done + i.partial }}/{{ i.total }}</span>
          </div>
        </div>
      </div>
    </div>

    <Teleport to="body"><Transition name="dt-tip"><div v-if="tipOn" class="dt-tip" :style="{ left: tipX + 'px', top: tipY + 'px' }"><div class="dt-tip-d">{{ tipD }}</div><div class="dt-tip-i">{{ tipI }}</div></div></Transition></Teleport>
  </div>
</template>
