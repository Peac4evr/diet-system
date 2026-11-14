<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import api from '../api'

function fmt(d: Date) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function today() { return fmt(new Date()) }
function daysAgo(n: number) {
  const d = new Date(); d.setDate(d.getDate() + n); return fmt(d)
}

const mealLabel: any = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐' }
const router = useRouter()
const date = ref(today())
const records = ref([])
const summary = ref<any>(null)
const loading = ref(false)

// ---- 摄入趋势 ----
const trendMetric = ref('calories')
const trendMetrics = [
  { value: 'calories', label: '热量', unit: '千卡', targetKey: 'calories', color: '#10b981' },
  { value: 'protein', label: '蛋白质', unit: '克', targetKey: 'protein_g', color: '#3b82f6' },
  { value: 'fat', label: '脂肪', unit: '克', targetKey: 'fat_g', color: '#f59e0b' },
  { value: 'carbs', label: '碳水', unit: '克', targetKey: 'carbs_g', color: '#22c55e' },
]
const trendRange = ref([daysAgo(-6), today()])
const trendRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null

const trendShortcuts = [
  { text: '近7天', value: () => [new Date(Date.now() - 6 * 86400000), new Date()] },
  { text: '近14天', value: () => [new Date(Date.now() - 13 * 86400000), new Date()] },
  { text: '近30天', value: () => [new Date(Date.now() - 29 * 86400000), new Date()] },
]

async function load() {
  loading.value = true
  try {
    const [r, s] = await Promise.all([
      api.get('/diet/records', { params: { record_date: date.value } }),
      api.get('/diet/summary', { params: { record_date: date.value } }),
    ])
    records.value = r.data
    summary.value = s.data
  } finally { loading.value = false }
}

async function loadTrend() {
  if (!trendRange.value || trendRange.value.length !== 2) return
  const [s, e] = trendRange.value
  try {
    const res = await api.get('/diet/trend', { params: { start_date: s, end_date: e } })
    await nextTick()
    renderTrend(res.data)
  } catch {}
}

function renderTrend(data: any) {
  if (!trendRef.value) return
  trendChart?.dispose()
  trendChart = echarts.init(trendRef.value)
  const days = data.days || []
  const targets = data.targets || {}
  const m = trendMetrics.find((x) => x.value === trendMetric.value) || trendMetrics[0]
  const values = days.map((d: any) => +(d[m.value] ?? 0))
  const targetVal = targets[m.targetKey] ?? 0
  const series: any[] = [
    { name: m.label, type: 'line', smooth: true, data: values, itemStyle: { color: m.color }, areaStyle: { opacity: 0.10 }, symbolSize: 6 },
  ]
  if (targetVal > 0) {
    series.push({ name: '目标', type: 'line', data: days.map(() => targetVal), itemStyle: { color: '#f59e0b' }, lineStyle: { type: 'dashed' }, symbol: 'none' })
  }
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, icon: 'circle' },
    grid: { left: 46, right: 20, top: 28, bottom: 44 },
    xAxis: { type: 'category', data: days.map((d: any) => d.date.slice(5)), boundaryGap: false },
    yAxis: { type: 'value', name: m.unit },
    series,
  })
}

function edit(r: any) { router.push(`/record?edit=${r.id}`) }

async function remove(r: any) {
  try { await ElMessageBox.confirm('确定删除这一餐吗？', '删除确认', { type: 'warning' }) } catch { return }
  try {
    await api.delete(`/diet/records/${r.id}`)
    ElMessage.success('已删除')
    load()
  } catch { ElMessage.error('删除失败') }
}

onMounted(() => { load(); loadTrend() })
onBeforeUnmount(() => { trendChart?.dispose() })
</script>

<template>
  <div>
    <h1 class="page-title">历史回溯</h1>
    <p class="page-sub">按周期查看摄入趋势，按日期回溯餐单</p>

    <div class="card trend-card">
      <div class="trend-head">
        <h3 class="chart-title">摄入趋势</h3>
        <div class="trend-controls">
          <el-radio-group v-model="trendMetric" size="small" @change="loadTrend">
            <el-radio-button v-for="m in trendMetrics" :key="m.value" :value="m.value">{{ m.label }}</el-radio-button>
          </el-radio-group>
          <el-date-picker v-model="trendRange" type="daterange" value-format="YYYY-MM-DD" size="small" :shortcuts="trendShortcuts" @change="loadTrend" />
        </div>
      </div>
      <div ref="trendRef" class="trend-chart" />
    </div>

    <div class="card head-card">
      <span class="head-label">单日餐单回溯</span>
      <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD" @change="load" />
    </div>

    <div v-if="summary" class="card summary-card">
      <span>当天摄入</span>
      <b>{{ summary.totals.calories }}</b><i>千卡</i>
      <span class="vs">目标 {{ summary.targets?.calories }} 千卡</span>
      <span class="gap">蛋白 {{ summary.totals.protein }}g · 脂肪 {{ summary.totals.fat }}g · 碳水 {{ summary.totals.carbs }}g</span>
    </div>

    <div v-if="records.length" class="records">
      <div v-for="r in records" :key="r.id" class="card record">
        <div class="record-head">
          <el-tag size="small" type="success" effect="light">{{ mealLabel[r.meal_type] || r.meal_type }}</el-tag>
          <b class="record-cal">{{ r.total_calories }} 千卡</b>
          <div class="record-actions">
            <el-button size="small" @click="edit(r)">修改</el-button>
            <el-button size="small" type="danger" plain @click="remove(r)">删除</el-button>
          </div>
        </div>
        <div class="record-raw">{{ r.raw_text }}</div>
        <div class="record-macro">蛋白 {{ r.total_protein_g }}g · 脂肪 {{ r.total_fat_g }}g · 碳水 {{ r.total_carbs_g }}g</div>
      </div>
    </div>
    <div v-else-if="!loading" class="card empty">这一天没有记录</div>
  </div>
</template>

<style scoped>
.trend-card { margin-bottom: 16px; }
.trend-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.trend-controls { display: flex; align-items: center; gap: 12px; }
.trend-chart { height: 260px; }

.head-card { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.head-label { color: var(--text-sub); font-size: 14px; font-weight: 600; }

.summary-card { display: flex; align-items: baseline; gap: 8px; margin-bottom: 16px; }
.summary-card b { font-size: 22px; font-weight: 700; color: var(--energy); }
.summary-card i { font-style: normal; color: var(--text-faint); font-size: 12px; }
.vs { color: var(--text-sub); font-size: 13px; }
.gap { margin-left: auto; color: var(--text-sub); font-size: 13px; }
.records { display: flex; flex-direction: column; gap: 12px; }
.record-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.record-cal { margin-left: auto; }
.record-actions { display: flex; gap: 8px; }
.record-raw { color: var(--text-main); font-size: 14px; margin-bottom: 4px; }
.record-macro { color: var(--text-sub); font-size: 13px; }
.empty { text-align: center; color: var(--text-faint); padding: 30px; }
</style>
