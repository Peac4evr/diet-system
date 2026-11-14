<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const gForm = ref({ title: '', content: '', source: '' })
const guidelines = ref<any[]>([])
const gAdding = ref(false)
const loading = ref(false)
const detailVisible = ref(false)
const current = ref<any>(null)

const q = ref('')
const searching = ref(false)
const page = ref(1)
const pageSize = 10

const paged = computed(() => {
  const start = (page.value - 1) * pageSize
  return guidelines.value.slice(start, start + pageSize)
})

const lastPage = computed(() => Math.max(1, Math.ceil(guidelines.value.length / pageSize)))

async function load() {
  loading.value = true
  try {
    const res = await api.get('/guidelines')
    guidelines.value = res.data
    page.value = 1
  } finally { loading.value = false }
}

async function search() {
  if (!q.value.trim()) { await load(); return }
  searching.value = true
  try {
    const res = await api.get('/guidelines', { params: { q: q.value.trim() } })
    guidelines.value = res.data
    page.value = 1
  } finally { searching.value = false }
}

async function add() {
  if (!gForm.value.title.trim() || !gForm.value.content.trim()) { ElMessage.warning('请填写标题和内容'); return }
  gAdding.value = true
  try {
    await api.post('/guidelines', gForm.value)
    ElMessage.success('已导入，将参与健康建议的检索增强')
    gForm.value = { title: '', content: '', source: '' }
    load()
  } catch (e: any) { ElMessage.error('导入失败：' + (e?.response?.data?.detail || e.message)) } finally { gAdding.value = false }
}

function openDetail(g: any) { current.value = g; detailVisible.value = true }

async function remove(g: any) {
  try { await ElMessageBox.confirm(`确定删除文献「${g.title}」吗？删除后将不再参与建议检索。`, '删除确认', { type: 'warning' }) } catch { return }
  try {
    await api.delete(`/guidelines/${g.id}`)
    ElMessage.success('已删除')
    q.value ? search() : load()
  } catch { ElMessage.error('删除失败') }
}

onMounted(load)
</script>

<template>
  <div>
    <h1 class="page-title">文献库</h1>
    <p class="page-sub">管理参与「健康建议」检索增强的膳食指南与科学文献</p>

    <div class="card search-card">
      <el-input v-model="q" placeholder="搜索文献，如：减脂 / 控盐 / 蛋白质" clearable @keyup.enter="search" @clear="load" />
      <el-button type="primary" :loading="searching" @click="search">搜索</el-button>
    </div>

    <div class="card import-card">
      <div class="card-head">
        <h3 class="sub-title">导入文献</h3>
        <p class="sub-hint">录入新的科学饮食文献，导入后自动参与建议生成时的权威召回</p>
      </div>
      <div class="form-grid">
        <div class="field">
          <label>标题</label>
          <el-input v-model="gForm.title" placeholder="如：控糖饮食原则" />
        </div>
        <div class="field">
          <label>来源</label>
          <el-input v-model="gForm.source" placeholder="如：《中国居民膳食指南（2022）》" />
        </div>
      </div>
      <div class="field" style="margin-top: 16px">
        <label>内容</label>
        <el-input v-model="gForm.content" type="textarea" :rows="3" placeholder="录入文献的核心要点…" />
      </div>
      <div class="import-foot">
        <el-button type="primary" size="large" :loading="gAdding" @click="add">导入文献</el-button>
      </div>
    </div>

    <div class="card list-card">
      <div class="card-head">
        <h3 class="sub-title">{{ q.trim() ? '搜索结果' : '已收录文献' }}（{{ guidelines.length }} 篇）</h3>
        <p class="sub-hint">点击任意一篇查看全文，这些内容会被「健康建议」按语义检索引用</p>
      </div>

      <div v-if="paged.length" class="g-list">
        <div v-for="g in paged" :key="g.id" class="g-row" @click="openDetail(g)">
          <span class="g-dot">📄</span>
          <div class="g-main">
            <span class="g-title">{{ g.title }}</span>
            <span class="g-src">{{ g.source }}</span>
          </div>
          <span class="g-preview">{{ g.content }}</span>
          <el-button size="small" type="danger" plain @click.stop="remove(g)">删除</el-button>
        </div>
      </div>
      <div v-else-if="!loading" class="empty">{{ q.trim() ? '没有找到相关文献' : '暂无文献，先导入一篇吧' }}</div>

      <div v-if="guidelines.length > pageSize" class="pager-wrap">
        <el-button :disabled="page <= 1" @click="page = 1" circle>
          <el-icon><DArrowLeft /></el-icon>
        </el-button>
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="guidelines.length"
          layout="prev, pager, next, total"
          background
        />
        <el-button :disabled="page >= lastPage" @click="page = lastPage" circle>
          <el-icon><DArrowRight /></el-icon>
        </el-button>
      </div>
    </div>

    <el-dialog v-model="detailVisible" :title="current?.title" width="600px" top="8vh">
      <div v-if="current">
        <div class="detail-src">📚 来源：{{ current.source }}</div>
        <div class="detail-content">{{ current.content }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.search-card { display: flex; gap: 12px; margin-bottom: 16px; }
.search-card .el-input { flex: 1; }

.card-head { margin-bottom: 18px; }
.sub-title { font-size: 17px; font-weight: 700; margin: 0 0 4px; color: var(--text-main); }
.sub-hint { font-size: 13px; color: var(--text-faint); margin: 0; }

.import-card { margin-bottom: 16px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 13px; color: var(--text-sub); font-weight: 500; }
.import-foot { display: flex; justify-content: flex-end; margin-top: 22px; }

.g-list { display: flex; flex-direction: column; }
.g-row {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 10px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background .15s ease;
  border-radius: 8px;
}
.g-row:last-child { border-bottom: none; }
.g-row:hover { background: #f0faf5; }
.g-dot { font-size: 18px; flex-shrink: 0; }
.g-main { display: flex; flex-direction: column; gap: 3px; width: 200px; flex-shrink: 0; }
.g-title { font-weight: 600; font-size: 15px; color: var(--text-main); }
.g-src { font-size: 12px; color: var(--text-faint); }
.g-preview {
  flex: 1; font-size: 13px; color: var(--text-sub);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.empty { text-align: center; color: var(--text-faint); padding: 30px; }

.pager-wrap { margin-top: 16px; display: flex; justify-content: center; align-items: center; gap: 12px; }

.detail-src { font-size: 13px; color: var(--text-sub); margin-bottom: 14px; }
.detail-content { font-size: 15px; line-height: 1.9; color: var(--text-main); white-space: pre-wrap; }
</style>
