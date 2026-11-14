<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

function today() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const date = ref(today())
const summary = ref<any>(null)
const advice = ref('')
const refs = ref<any[]>([])
const loading = ref(false)

async function loadSummary() {
  try {
    const res = await api.get('/diet/summary', { params: { record_date: date.value } })
    summary.value = res.data
  } catch {}
}

async function loadAdvice() {
  try {
    const res = await api.get('/advice', { params: { record_date: date.value } })
    advice.value = res.data.advice || ''
    refs.value = res.data.refs || []
  } catch {}
}

async function generate() {
  loading.value = true
  try {
    const res = await api.post('/advice', { record_date: date.value })
    advice.value = res.data.advice
    refs.value = res.data.refs || []
    if (res.data.intake && res.data.targets) {
      summary.value = { totals: res.data.intake, targets: res.data.targets }
    }
  } catch { ElMessage.error('生成失败') } finally { loading.value = false }
}

function onDateChange() {
  loadSummary()
  loadAdvice()
}

onMounted(() => {
  loadSummary()
  loadAdvice()
})
</script>

<template>
  <div>
    <h1 class="page-title">健康建议</h1>
    <p class="page-sub">结合当日摄入与目标，获得个性化指导</p>

    <div class="card controls">
      <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD" @change="onDateChange" />
      <el-button type="primary" :loading="loading" @click="generate">生成建议</el-button>
    </div>

    <div v-if="summary" class="card summary-card">
      <h3 class="card-title">今日摄入概览</h3>
      <div class="metric-grid">
        <div class="metric">
          <span class="m-label">热量</span>
          <div class="m-value"><b>{{ summary.totals.calories }}</b><i>/ {{ summary.targets?.calories }} 千卡</i></div>
        </div>
        <div class="metric">
          <span class="m-label">蛋白质</span>
          <div class="m-value"><b>{{ summary.totals.protein }}</b><i>/ {{ summary.targets?.protein_g }} 克</i></div>
        </div>
        <div class="metric">
          <span class="m-label">脂肪</span>
          <div class="m-value"><b>{{ summary.totals.fat }}</b><i>/ {{ summary.targets?.fat_g }} 克</i></div>
        </div>
        <div class="metric">
          <span class="m-label">碳水</span>
          <div class="m-value"><b>{{ summary.totals.carbs }}</b><i>/ {{ summary.targets?.carbs_g }} 克</i></div>
        </div>
      </div>
    </div>

    <div v-if="advice" class="card advice-card">
      <div class="advice-head">
        <span class="advice-icon">💬</span>
        <h3 class="card-title">给你的建议</h3>
      </div>
      <div class="advice-text">{{ advice }}</div>


    <div v-if="refs.length" class="card refs-card">
      <div class="refs-head">
        <span class="refs-icon">📚</span>
        <h3 class="card-title">本次参考的权威文献</h3>
      </div>
      <div class="ref-list">
        <div v-for="(r, i) in refs" :key="i" class="ref-item">
          <div class="ref-title">{{ r.title }}</div>
          <div class="ref-src">{{ r.source }}</div>
          <div class="ref-content">{{ r.content }}</div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<style scoped>
.controls { display: flex; gap: 12px; margin-bottom: 16px; }
.card-title { font-size: 15px; font-weight: 600; margin: 0 0 14px; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.m-label { font-size: 12px; color: var(--text-faint); }
.m-value { margin-top: 6px; }
.m-value b { font-size: 22px; font-weight: 700; }
.m-value i { font-style: normal; color: var(--text-sub); font-size: 13px; margin-left: 4px; }
.advice-card { margin-top: 16px; }
.advice-head { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.advice-icon { font-size: 18px; }
.advice-head .card-title { margin: 0; }
.advice-text { white-space: pre-wrap; line-height: 2; font-size: 15px; color: var(--text-main); }
.refs-card { margin-top: 16px; }
.refs-head { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.refs-icon { font-size: 18px; }
.refs-head .card-title { margin: 0; }
.ref-list { display: flex; flex-direction: column; gap: 12px; }
.ref-item { padding: 12px 14px; background: #f6fbf8; border: 1px solid #e2f1e8; border-radius: 10px; }
.ref-title { font-size: 14px; font-weight: 700; color: var(--text-main); }
.ref-src { font-size: 12px; color: var(--text-faint); margin-top: 2px; }
.ref-content { font-size: 13px; color: var(--text-sub); line-height: 1.7; margin-top: 8px; }
</style>