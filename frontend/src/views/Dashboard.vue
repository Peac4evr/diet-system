<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '../api'

function today() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const date = ref(today())
const summary = ref<any>(null)
const loading = ref(false)

const ringRef = ref<HTMLElement>()
const pieRef = ref<HTMLElement>()
let ringChart: echarts.ECharts | null = null
let pieChart: echarts.ECharts | null = null

const stats = [
  { key: 'calories', label: '热量', unit: '千卡', color: '#f59e0b', targetKey: 'calories' },
  { key: 'protein', label: '蛋白质', unit: '克', color: '#3b82f6', targetKey: 'protein_g' },
  { key: 'fat', label: '脂肪', unit: '克', color: '#fbbf24', targetKey: 'fat_g' },
  { key: 'carbs', label: '碳水', unit: '克', color: '#22c55e', targetKey: 'carbs_g' },
]

const statIntake = (s: any) => summary.value?.totals?.[s.key] ?? 0
const statTarget = (s: any) => summary.value?.targets?.[s.targetKey] ?? 0
const statPct = (s: any) => {
  const t = statTarget(s)
  return t ? Math.min(100, Math.round((statIntake(s) / t) * 100)) : 0
}

const macroCompare = computed(() => {
  const t = summary.value?.totals
  const rec: any = { protein: 20, fat: 25, carbs: 55 }
  const defs = [
    { name: '蛋白质', key: 'protein', color: '#3b82f6' },
    { name: '脂肪', key: 'fat', color: '#fbbf24' },
    { name: '碳水', key: 'carbs', color: '#22c55e' },
  ]
  if (!t) return defs.map((d: any) => ({ ...d, actual: 0, recommended: rec[d.key], diff: -rec[d.key] }))
  const kcal: any = { protein: t.protein * 4, fat: t.fat * 9, carbs: t.carbs * 4 }
  const total = kcal.protein + kcal.fat + kcal.carbs
  return defs.map((d: any) => {
    const actual = total ? Math.round((kcal[d.key] / total) * 100) : 0
    return { ...d, actual, recommended: rec[d.key], diff: actual - rec[d.key] }
  })
})

async function load() {
  loading.value = true
  try {
    const res = await api.get('/diet/summary', { params: { record_date: date.value } })
    summary.value = res.data
    await nextTick()
    renderRing()
    renderPie()
  } finally {
    loading.value = false
  }
}

function renderRing() {
  if (!ringRef.value || !summary.value) return
  ringChart?.dispose()
  ringChart = echarts.init(ringRef.value)
  const total = summary.value.totals.calories || 0
  const goal = summary.value.targets?.calories || 0
  const percent = goal ? Math.min(100, Math.round((total / goal) * 100)) : 0
  const over = goal > 0 && total > goal
  const color = over ? '#ef4444' : '#10b981'
  ringChart.setOption({
    series: [{
      type: 'pie', radius: ['70%', '86%'], silent: true,
      label: { show: false }, labelLine: { show: false },
      data: [
        { value: Math.min(total, goal || total), itemStyle: { color } },
        { value: Math.max(goal - total, 0), itemStyle: { color: '#ecefee' } },
      ],
    }],
    title: {
      text: goal ? `${percent}%` : '—',
      subtext: over ? '已超标' : '热量进度',
      left: 'center', top: '36%',
      textStyle: { fontSize: 26, fontWeight: 700, color: over ? '#ef4444' : '#1f2937' },
      subtextStyle: { fontSize: 12, color: '#9ca3af' },
    },
  })
}

function renderPie() {
  if (!pieRef.value || !summary.value) return
  pieChart?.dispose()
  pieChart = echarts.init(pieRef.value)
  const t = summary.value.totals
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} kcal（{d}%）' },
    legend: { bottom: 0, icon: 'circle' },
    series: [{
      type: 'pie', radius: ['42%', '68%'], center: ['50%', '44%'],
      label: { formatter: '{b} {d}%', color: '#6b7280' },
      data: [
        { name: '蛋白质', value: +(t.protein * 4).toFixed(1), itemStyle: { color: '#3b82f6' } },
        { name: '脂肪', value: +(t.fat * 9).toFixed(1), itemStyle: { color: '#fbbf24' } },
        { name: '碳水', value: +(t.carbs * 4).toFixed(1), itemStyle: { color: '#22c55e' } },
      ],
    }],
  })
}

onMounted(load)
onBeforeUnmount(() => { ringChart?.dispose(); pieChart?.dispose() })
</script>

<template>
  <div class="page">
    <div class="head">
      <div>
        <h1 class="page-title">营养看板</h1>
        <p class="page-sub">今日摄入与目标的实时对比</p>
      </div>
      <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD" @change="load" />
    </div>

    <div v-if="summary" class="stats">
      <div v-for="s in stats" :key="s.key" class="card stat">
        <span class="stat-label">{{ s.label }}</span>
        <div class="stat-num">
          <span class="big-number" :style="{ color: s.color }">{{ statIntake(s) }}</span>
          <span class="stat-unit">/ {{ statTarget(s) }} {{ s.unit }}</span>
        </div>
        <div class="bar"><div class="bar-inner" :style="{ width: statPct(s) + '%', background: s.color }" /></div>
      </div>
    </div>
    <div v-if="summary?.warnings?.length" class="warnings">
      <div v-for="w in summary.warnings" :key="w.type" class="warn" :class="'warn-' + w.level">
        <span class="warn-icon">{{ w.level === 'high' ? '🚨' : '⚠️' }}</span>
        <div class="warn-body">
          <b>{{ w.title }}</b>
          <p>{{ w.detail }}</p>
        </div>
      </div>
    </div>


    <div v-if="summary" class="charts">
      <div class="card chart-card">
        <h3 class="chart-title">热量进度</h3>
        <div ref="ringRef" class="chart" />
      </div>
      <div class="card chart-card">
        <h3 class="chart-title">供能比</h3>
        <div ref="pieRef" class="chart pie-chart" />
        <div class="ratio-list">
          <div v-for="m in macroCompare" :key="m.key" class="ratio-row">
            <span class="ratio-dot" :style="{ background: m.color }" />
            <span class="ratio-name">{{ m.name }}</span>
            <span class="ratio-val">实际 <b>{{ m.actual }}%</b></span>
            <span class="ratio-arrow" :class="m.diff > 0 ? 'up' : 'down'">{{ m.diff > 0 ? '↑' : '↓' }}</span>
            <span class="ratio-rec">推荐 {{ m.recommended }}%</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!loading" class="card empty">
      还没有记录，去「饮食记录」添加一餐吧 🍽️
    </div>
  </div>
</template>

<style scoped>
.head { display: flex; justify-content: space-between; align-items: flex-start; }

.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; position: relative; z-index: 1; }

.stat {
  border: none;
  color: #fff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 8px 22px rgba(0, 0, 0, .14);
}
.stat:nth-child(1) { background: linear-gradient(135deg, #f59e0b, #fbbf24); }
.stat:nth-child(2) { background: linear-gradient(135deg, #3b82f6, #60a5fa); }
.stat:nth-child(3) { background: linear-gradient(135deg, #f97316, #fb923c); }
.stat:nth-child(4) { background: linear-gradient(135deg, #22c55e, #4ade80); }

.stat-label { font-size: 17px; font-weight: 600; color: rgba(255, 255, 255, .95); }
.stat-num { display: flex; align-items: baseline; gap: 6px; margin: 10px 0 12px; }
.stat-num .big-number { color: #fff !important; font-size: 44px; }
.stat-unit { font-size: 15px; color: rgba(255, 255, 255, .85); }
.bar { height: 7px; border-radius: 4px; background: rgba(255, 255, 255, .28); overflow: hidden; }
.bar-inner { height: 100%; border-radius: 4px; background: #fff !important; transition: width .3s; }

.charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; position: relative; z-index: 1; }
.chart-card { display: flex; flex-direction: column; }
.chart-title { font-size: 15px; font-weight: 600; margin: 0 0 8px; }
.chart { height: 280px; }
.pie-chart { height: 210px; }
.ratio-list { margin-top: 2px; display: flex; flex-direction: column; gap: 8px; }
.ratio-row { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.ratio-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.ratio-name { color: var(--text-sub); min-width: 44px; }
.ratio-val { color: var(--text-sub); }
.ratio-val b { color: var(--text-main); font-weight: 700; }
.ratio-arrow.up { color: #ef4444; }
.ratio-arrow.down { color: #f59e0b; }
.ratio-rec { color: var(--text-faint); margin-left: auto; }
.empty { text-align: center; color: var(--text-sub); padding: 40px; }
.warnings { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; position: relative; z-index: 1; }
.warn { display: flex; align-items: flex-start; gap: 10px; padding: 14px 16px; border-radius: 12px; border: 1px solid; }
.warn-high { background: #fef2f2; border-color: #fecaca; }
.warn-medium { background: #fffbeb; border-color: #fde68a; }
.warn-icon { font-size: 20px; line-height: 1.2; }
.warn-body b { display: block; font-size: 15px; font-weight: 700; color: #b91c1c; }
.warn-medium .warn-body b { color: #b45309; }
.warn-body p { margin: 4px 0 0; font-size: 13px; color: #7f1d1d; line-height: 1.6; }
.warn-medium .warn-body p { color: #78350f; }
</style>