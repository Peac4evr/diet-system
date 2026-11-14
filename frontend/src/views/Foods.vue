<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const q = ref('')
const searching = ref(false)
const isSearch = ref(false)

// ---- 全部食物（服务端分页） ----
const allItems = ref<any[]>([])
const allTotal = ref(0)
const allPage = ref(1)
const allPageSize = 20
const loadingAll = ref(false)

const lastAllPage = computed(() => Math.max(1, Math.ceil(allTotal.value / allPageSize)))

// ---- 搜索结果（客户端分页） ----
const results = ref<any[]>([])
const resultPage = ref(1)
const resultPageSize = 10
const lastResultPage = computed(() => Math.max(1, Math.ceil(results.value.length / resultPageSize)))
const pagedResults = computed(() => {
  const s = (resultPage.value - 1) * resultPageSize
  return results.value.slice(s, s + resultPageSize)
})

const addForm = ref({ name: '', category: '自定义', calories: 0, protein: 0, fat: 0, carbs: 0, sodium: 0 })
const adding = ref(false)

async function loadAll() {
  loadingAll.value = true
  try {
    const res = await api.get('/foods', { params: { page: allPage.value, page_size: allPageSize } })
    allItems.value = res.data.items
    allTotal.value = res.data.total
  } finally { loadingAll.value = false }
}

function gotoAllPage(p: number) {
  allPage.value = p
  loadAll()
}

async function search() {
  if (!q.value.trim()) { ElMessage.warning('输入关键词'); return }
  searching.value = true
  try {
    const res = await api.get('/foods/search', { params: { q: q.value.trim() } })
    results.value = res.data
    resultPage.value = 1
    isSearch.value = true
  } finally { searching.value = false }
}

function resetToAll() {
  isSearch.value = false
  q.value = ''
  resultPage.value = 1
}

async function add() {
  if (!addForm.value.name.trim()) { ElMessage.warning('请输入食物名称'); return }
  adding.value = true
  try {
    await api.post('/foods', addForm.value)
    ElMessage.success('已添加')
    addForm.value = { name: '', category: '自定义', calories: 0, protein: 0, fat: 0, carbs: 0, sodium: 0 }
    loadAll()
  } catch { ElMessage.error('添加失败') } finally { adding.value = false }
}

onMounted(loadAll)
</script>

<template>
  <div>
    <h1 class="page-title">食物库</h1>
    <p class="page-sub">浏览全部食物，或搜索、手动录入冷门食材</p>

    <div class="card search-card">
      <el-input v-model="q" placeholder="搜索食物，如：牛肉" clearable @keyup.enter="search" @clear="resetToAll" />
      <el-button type="primary" :loading="searching" @click="search">搜索</el-button>
    </div>
<div class="card add-card">
      <div class="add-head">
        <h3 class="sub-title">录入自定义食物</h3>
        <p class="sub-hint">以下数值均按「每 100 克」填写</p>
      </div>

      <div class="basic-grid">
        <div class="field">
          <label>食物名称</label>
          <el-input v-model="addForm.name" placeholder="如：螺蛳粉" />
        </div>
        <div class="field">
          <label>分类</label>
          <el-input v-model="addForm.category" placeholder="如：小吃" />
        </div>
      </div>

      <div class="nutr-label">营养成分</div>
      <div class="nutr-grid">
        <div class="field">
          <label>热量（千卡）</label>
          <el-input-number v-model="addForm.calories" :min="0" style="width: 100%" />
        </div>
        <div class="field">
          <label>蛋白质（克）</label>
          <el-input-number v-model="addForm.protein" :min="0" style="width: 100%" />
        </div>
        <div class="field">
          <label>脂肪（克）</label>
          <el-input-number v-model="addForm.fat" :min="0" style="width: 100%" />
        </div>
        <div class="field">
          <label>碳水（克）</label>
          <el-input-number v-model="addForm.carbs" :min="0" style="width: 100%" />
        </div>
        <div class="field">
          <label>钠（毫克）</label>
          <el-input-number v-model="addForm.sodium" :min="0" style="width: 100%" />
        </div>
      </div>

      <div class="add-foot">
        <el-button type="primary" size="large" :loading="adding" @click="add">添加食物</el-button>
      </div>
    </div>


    <div v-if="isSearch" class="card">
      <div class="card-head">
        <h3 class="sub-title">搜索结果（{{ results.length }} 条）</h3>
        <p class="sub-hint">清空搜索框可返回全部食物</p>
      </div>
      <div v-if="results.length">
        <div v-for="(f, i) in pagedResults" :key="i" class="food-row">
          <div>
            <span class="food-name">{{ f.name }}</span>
            <span class="food-cat">{{ f.category }}</span>
          </div>
          <div class="food-nutr">每100g：热量 {{ f.calories }} 千卡 · 蛋白 {{ f.protein }}g · 脂肪 {{ f.fat }}g · 碳水 {{ f.carbs }}g · 钠 {{ f.sodium }}mg</div>
        </div>
        <div v-if="results.length > resultPageSize" class="pager-wrap">
          <el-button :disabled="resultPage <= 1" @click="resultPage = 1" circle>
            <el-icon><DArrowLeft /></el-icon>
          </el-button>
          <el-pagination v-model:current-page="resultPage" :page-size="resultPageSize" :total="results.length" layout="prev, pager, next, total" background />
          <el-button :disabled="resultPage >= lastResultPage" @click="resultPage = lastResultPage" circle>
            <el-icon><DArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
      <div v-else class="empty">没有找到相关食物</div>
    </div>

    <div v-else class="card">
      <div class="card-head">
        <h3 class="sub-title">全部食物（{{ allTotal }} 种）</h3>
        <p class="sub-hint">按每 100 克的营养成分展示</p>
      </div>
      <div v-loading="loadingAll">
        <div v-for="(f, i) in allItems" :key="i" class="food-row">
          <div>
            <span class="food-name">{{ f.name }}</span>
            <span class="food-cat">{{ f.category }}</span>
          </div>
          <div class="food-nutr">每100g：热量 {{ f.calories }} 千卡 · 蛋白 {{ f.protein }}g · 脂肪 {{ f.fat }}g · 碳水 {{ f.carbs }}g · 钠 {{ f.sodium }}mg</div>
        </div>
      </div>
      <div class="pager-wrap">
        <el-button :disabled="allPage <= 1" @click="gotoAllPage(1)" circle>
          <el-icon><DArrowLeft /></el-icon>
        </el-button>
        <el-pagination v-model:current-page="allPage" :page-size="allPageSize" :total="allTotal" layout="prev, pager, next, total" background @current-change="loadAll" />
        <el-button :disabled="allPage >= lastAllPage" @click="gotoAllPage(lastAllPage)" circle>
          <el-icon><DArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

      </div>
</template>

<style scoped>
.search-card { display: flex; gap: 12px; margin-bottom: 16px; }
.search-card .el-input { flex: 1; }

.card-head { margin-bottom: 14px; }
.sub-title { font-size: 17px; font-weight: 700; margin: 0 0 4px; }
.sub-hint { font-size: 13px; color: var(--text-faint); margin: 0; }

.food-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border); }
.food-row:last-child { border-bottom: none; }
.food-name { font-weight: 600; margin-right: 8px; }
.food-cat { color: var(--text-faint); font-size: 12px; }
.food-nutr { color: var(--text-sub); font-size: 13px; }

.pager-wrap { margin-top: 16px; display: flex; justify-content: center; align-items: center; gap: 12px; }
.empty { text-align: center; color: var(--text-faint); padding: 30px; }

.add-card { margin-top: 16px; }
.add-head { margin-bottom: 18px; }
.basic-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-bottom: 20px; }

.nutr-label { font-size: 13px; color: var(--text-sub); font-weight: 500; margin-bottom: 12px; }

.nutr-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 13px; color: var(--text-sub); }

.add-foot { display: flex; justify-content: flex-end; margin-top: 22px; }
</style>
