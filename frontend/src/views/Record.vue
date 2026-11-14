<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api'

function today() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const route = useRoute()
const router = useRouter()

const text = ref('')
const mealType = ref('lunch')
const parsing = ref(false)
const saving = ref(false)
const result = ref<any>(null)
const editingId = ref<number | null>(null)

const addVisible = ref(false)
const addName = ref('')
const adding = ref(false)

const mealTypes = [
  { value: 'breakfast', label: '早餐' },
  { value: 'lunch', label: '午餐' },
  { value: 'dinner', label: '晚餐' },
  { value: 'snack', label: '加餐' },
]

const examples = [
  '一碗加了肥牛卷和宽粉的麻辣烫',
  '两个鸡蛋加一杯牛奶',
  '一份鸡胸肉蔬菜沙拉',
  '半碗米饭配番茄炒蛋',
]

function useExample(e: string) {
  text.value = e
  parse()
}

function toPer100(nutrition: any, weight: number) {
  const k = 100 / (weight || 100)
  const out: any = {}
  for (const [key, v] of Object.entries(nutrition)) out[key] = +((v as number) * k).toFixed(2)
  return out
}

function displayNutr(item: any) {
  if (!item.per100) return null
  const k = (item.weight_g || 0) / 100
  const out: any = {}
  for (const [key, v] of Object.entries(item.per100)) out[key] = +((v as number) * k).toFixed(1)
  return out
}

function normalizeItems(items: any[]) {
  for (const it of items) {
    it.original_weight = it.weight_g
    it.per100 = it.nutrition ? toPer100(it.nutrition, it.weight_g) : null
    it.estimated = false
  }
}

onMounted(async () => {
  const id = route.query.edit
  if (!id) return
  editingId.value = Number(id)
  try {
    const res = await api.get(`/diet/records/${id}`)
    const r = res.data
    text.value = r.raw_text
    mealType.value = r.meal_type
    result.value = { meal_type: r.meal_type, items: r.items, totals: {} }
    for (const it of result.value.items) {
      it.original_weight = it.weight_g
      it.per100 = it.nutrition ? toPer100(it.nutrition, it.weight_g) : null
      it.estimated = !it.matched_name
    }
  } catch { ElMessage.error('加载记录失败') }
})

async function parse() {
  if (!text.value.trim()) { ElMessage.warning('先输入一段饮食描述'); return }
  parsing.value = true
  try {
    const res = await api.post('/diet/parse', { text: text.value.trim() })
    result.value = res.data
    normalizeItems(result.value.items)
    mealType.value = result.value.meal_type || mealType.value
  } catch (e: any) {
    ElMessage.error('解析失败：' + (e?.response?.data?.detail || e.message))
  } finally { parsing.value = false }
}

async function aiWeight(item: any) {
  try {
    const res = await api.post('/diet/estimate-weight', { name: item.name, context: text.value })
    item.weight_g = res.data.weight_g
    item.original_weight = res.data.weight_g
    ElMessage.success(`已按语境估重：${res.data.weight_g} 克`)
  } catch { ElMessage.error('估重失败') }
}

async function aiNutrition(item: any) {
  try {
    const res = await api.post('/diet/estimate-nutrition', { name: item.name, weight_g: item.weight_g, context: text.value })
    item.per100 = toPer100(res.data, item.weight_g)
    item.estimated = true
    ElMessage.success('已用 AI 估计营养')
  } catch { ElMessage.error('估计失败') }
}

function removeItem(i: number) {
  result.value.items.splice(i, 1)
}

function ensureResult() {
  if (!result.value) result.value = { meal_type: mealType.value, items: [], totals: {} }
}

async function confirmAdd() {
  const name = addName.value.trim()
  if (!name) { ElMessage.warning('输入食物名'); return }
  adding.value = true
  try {
    const res = await api.post('/foods/match', { name })
    const m = res.data
    ensureResult()
    if (m.matched_name) {
      result.value.items.push({ name, matched_name: m.matched_name, weight_g: 100, confidence: 1, original_weight: 100, per100: m.per100 || null, estimated: false })
    } else {
      result.value.items.push({ name, matched_name: null, weight_g: 100, confidence: 0, original_weight: 100, per100: null, estimated: false })
    }
    addVisible.value = false
    addName.value = ''
  } catch (e: any) {
    ElMessage.error('匹配失败：' + (e?.response?.data?.detail || e.message))
  } finally { adding.value = false }
}

function previewTotals() {
  if (!result.value) return null
  const t: any = { calories: 0, protein: 0, fat: 0, carbs: 0, sodium: 0 }
  for (const it of result.value.items) {
    const n = displayNutr(it)
    if (n) { t.calories += n.calories; t.protein += n.protein; t.fat += n.fat; t.carbs += n.carbs; t.sodium += n.sodium }
  }
  return { calories: +t.calories.toFixed(1), protein: +t.protein.toFixed(1), fat: +t.fat.toFixed(1), carbs: +t.carbs.toFixed(1), sodium: +t.sodium.toFixed(1) }
}

async function save() {
  if (!result.value) return
  const items = result.value.items.map((it: any) => ({
    name: it.name,
    matched_name: it.matched_name || null,
    weight_g: it.weight_g,
    confidence: it.confidence ?? 0,
    nutrition: (!it.matched_name && it.per100) ? displayNutr(it) : null,
  }))
  saving.value = true
  try {
    if (editingId.value) {
      try { await api.delete(`/diet/records/${editingId.value}`) } catch {}
    }
    const res = await api.post('/diet/records', {
      record_date: today(), meal_type: mealType.value, raw_text: text.value.trim(), items,
    })
    ElMessage.success(`已保存，本餐 ${res.data.totals.calories} 千卡`)
    result.value = null
    text.value = ''
    editingId.value = null
    router.replace('/record')
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e?.response?.data?.detail || e.message))
  } finally { saving.value = false }
}
</script>

<template>
  <div class="page">
    <h1 class="page-title">饮食记录</h1>
    <p class="page-sub">{{ editingId ? '正在修改这一餐' : '用一句话描述你吃了什么，剩下的交给系统' }}</p>

    <div class="card input-card">
      <div class="input-row">
        <el-select v-model="mealType" style="width: 120px">
          <el-option v-for="m in mealTypes" :key="m.value" :label="m.label" :value="m.value" />
        </el-select>
        <el-input v-model="text" type="textarea" :rows="2" placeholder="例如：一碗加了肥牛卷和宽粉和鸡胸的麻辣烫" />
        <el-button type="primary" :loading="parsing" @click="parse">解析</el-button>
      </div>
    </div>

    <div v-if="!result" class="guide-area">
      <div class="card guide-card">
        <h3 class="guide-title">不知道怎么描述？点一个示例试试 👇</h3>
        <div class="example-chips">
          <button v-for="e in examples" :key="e" class="example-chip" @click="useExample(e)">{{ e }}</button>
        </div>
      </div>

      <div class="features">
        <div class="card feature">
          <span class="feat-icon">🧠</span>
          <div class="feat-body">
            <div class="feat-title">智能解析</div>
            <div class="feat-desc">一句话拆出食材和克重</div>
          </div>
        </div>
        <div class="card feature">
          <span class="feat-icon">⚖️</span>
          <div class="feat-body">
            <div class="feat-title">AI 估重</div>
            <div class="feat-desc">拿不准克重，AI 帮你估</div>
          </div>
        </div>
        <div class="card feature">
          <span class="feat-icon">➕</span>
          <div class="feat-body">
            <div class="feat-title">自由增删</div>
            <div class="feat-desc">漏了添加、多了删除</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="result" class="card confirm-card">
      <div class="confirm-head">
        <h3 class="confirm-title">确认这一餐，可微调</h3>
        <el-button size="small" @click="addVisible = true">＋ 添加食物</el-button>
      </div>

      <div v-for="(it, i) in result.items" :key="i" class="item-row">
        <div class="item-main">
          <div class="item-name">
            <span class="name">{{ it.name }}</span>
            <el-tag v-if="it.matched_name" size="small" type="success" effect="light">{{ it.matched_name }}</el-tag>
            <el-tag v-else-if="it.estimated" size="small" type="warning" effect="light">AI 估计</el-tag>
            <el-tag v-else size="small" type="danger" effect="light">未识别</el-tag>
          </div>
          <div v-if="displayNutr(it)" class="item-nutr">
            <span>热量 <b>{{ displayNutr(it).calories }}</b> 千卡</span>
            <span>蛋白 <b>{{ displayNutr(it).protein }}</b> 克</span>
            <span>脂肪 <b>{{ displayNutr(it).fat }}</b> 克</span>
            <span>碳水 <b>{{ displayNutr(it).carbs }}</b> 克</span>
          </div>
        </div>

        <div class="item-actions">
          <el-input-number v-model="it.weight_g" :min="1" :max="2000" size="small" style="width: 100px" />
          <span class="unit">克</span>
          <el-button size="small" @click="aiWeight(it)">AI 估重</el-button>
          <el-button v-if="!it.matched_name && !it.per100" size="small" type="warning" @click="aiNutrition(it)">AI 估计营养</el-button>
          <el-button size="small" type="danger" plain @click="removeItem(i)">删除</el-button>
        </div>
      </div>

      <div v-if="result.items.length === 0" class="empty">这一餐还没有食物，点右上角「添加食物」或重新解析</div>

      <div class="confirm-foot">
        <div class="totals" v-if="previewTotals()">
          合计：<b>{{ previewTotals().calories }}</b> 千卡 · 蛋白 {{ previewTotals().protein }}g · 脂肪 {{ previewTotals().fat }}g · 碳水 {{ previewTotals().carbs }}g
        </div>
        <el-button type="primary" size="large" :loading="saving" @click="save">{{ editingId ? '保存修改' : '保存这一餐' }}</el-button>
      </div>
    </div>

    <el-dialog v-model="addVisible" title="添加食物" width="380px">
      <el-input v-model="addName" placeholder="输入食物名，如：土豆" @keyup.enter="confirmAdd" />
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="confirmAdd">匹配并添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.input-card { margin-bottom: 16px; }
.input-row { display: flex; gap: 12px; align-items: stretch; }
.input-row .el-input { flex: 1; }
.confirm-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.confirm-title { font-size: 15px; font-weight: 600; margin: 0; }
.item-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 0; border-bottom: 1px solid var(--border); }
.item-row:last-of-type { border-bottom: none; }
.item-main { flex: 1; min-width: 0; }
.item-name { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.item-name .name { font-weight: 600; }
.item-nutr { display: flex; flex-wrap: wrap; gap: 4px 16px; color: var(--text-sub); font-size: 13px; }
.item-nutr b { color: var(--text-main); }
.item-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.unit { color: var(--text-sub); font-size: 13px; }
.empty { text-align: center; color: var(--text-faint); padding: 20px 0; }
.confirm-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; }
.totals { color: var(--text-sub); font-size: 14px; }
.totals b { color: var(--text-main); font-size: 18px; }
.guide-card { text-align: left; padding: 32px 24px; }
.guide-title { font-size: 16px; font-weight: 600; margin: 0 0 16px; color: var(--text-sub); }
.example-chips { display: flex; flex-wrap: wrap; justify-content: flex-start; gap: 10px; }
.example-chip {
  border: 1px solid #c7e9da;
  background: linear-gradient(180deg, #ffffff, #f3faf6);
  color: #0a5c43;
  padding: 10px 16px;
  border-radius: 999px;
  font-size: 14px;
  cursor: pointer;
  transition: all .18s ease;
}
.example-chip:hover {
  background: var(--brand-soft);
  border-color: var(--brand);
  box-shadow: 0 4px 12px rgba(16, 185, 129, .18);
  transform: translateY(-1px);
}
.features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px; }
.feature { display: flex; align-items: flex-start; gap: 12px; padding: 18px 20px; }
.feat-icon { font-size: 26px; line-height: 1; }
.feat-title { font-weight: 600; font-size: 15px; }
.feat-desc { font-size: 13px; color: var(--text-sub); margin-top: 2px; }
.page { display: flex; flex-direction: column; min-height: calc(100vh - 120px); }
.guide-area { margin-top: auto; padding-top: 16px; }
</style>