<script setup lang="ts">
// @ts-nocheck
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const form = ref({ name: '', gender: 'male', age: 22, height_cm: 175, weight_kg: 70, activity_level: 'moderate', goal: 'lose_fat' })
const profile = ref(null)
const saving = ref(false)

const activityOptions = [
  { value: 'sedentary', label: '久坐（很少运动）' },
  { value: 'light', label: '轻度活动（每周1-3次）' },
  { value: 'moderate', label: '中度活动（每周3-5次）' },
  { value: 'active', label: '高度活动（每周6-7次）' },
  { value: 'very_active', label: '极高活动（体力劳动）' },
]
const goalOptions = [
  { value: 'lose_fat', label: '减脂' },
  { value: 'build_muscle', label: '增肌' },
  { value: 'maintain', label: '保持健康' },
]

async function load() {
  try {
    const res = await api.get('/profile')
    if (res.data) { profile.value = res.data; Object.assign(form.value, res.data) }
  } catch {}
}

async function save() {
  saving.value = true
  try {
    const res = await api.post('/profile', form.value)
    profile.value = res.data
    ElMessage.success('已保存并计算')
  } catch { ElMessage.error('保存失败') } finally { saving.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <h1 class="page-title">体征档案</h1>
    <p class="page-sub">录入身体数据，自动计算代谢目标</p>

    <div class="grid">
      <div class="card">
        <el-form label-width="90px">
          <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="性别">
            <el-radio-group v-model="form.gender">
              <el-radio value="male">男</el-radio>
              <el-radio value="female">女</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="年龄"><el-input-number v-model="form.age" :min="1" :max="120" /></el-form-item>
          <el-form-item label="身高(cm)"><el-input-number v-model="form.height_cm" :min="50" :max="250" /></el-form-item>
          <el-form-item label="体重(kg)"><el-input-number v-model="form.weight_kg" :min="20" :max="300" /></el-form-item>
          <el-form-item label="活动水平">
            <el-select v-model="form.activity_level">
              <el-option v-for="a in activityOptions" :key="a.value" :label="a.label" :value="a.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标">
            <el-select v-model="form.goal">
              <el-option v-for="g in goalOptions" :key="g.value" :label="g.label" :value="g.value" />
            </el-select>
          </el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存并计算</el-button>
        </el-form>
      </div>

      <div v-if="profile" class="card">
        <h3 class="sub-title">代谢目标</h3>
        <div class="metric-list">
          <div class="metric"><span>基础代谢 BMR</span><b>{{ profile.bmr }}</b><i>千卡/天</i></div>
          <div class="metric"><span>每日消耗 TDEE</span><b>{{ profile.tdee }}</b><i>千卡/天</i></div>
          <div class="metric"><span>目标热量</span><b>{{ profile.target_calories }}</b><i>千卡/天</i></div>
          <div class="metric"><span>蛋白质</span><b>{{ profile.target_protein_g }}</b><i>克/天</i></div>
          <div class="metric"><span>脂肪</span><b>{{ profile.target_fat_g }}</b><i>克/天</i></div>
          <div class="metric"><span>碳水</span><b>{{ profile.target_carbs_g }}</b><i>克/天</i></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.sub-title { font-size: 15px; font-weight: 600; margin: 0 0 14px; }
.metric-list { display: flex; flex-direction: column; gap: 14px; }
.metric { display: flex; align-items: baseline; gap: 8px; }
.metric span { color: var(--text-sub); font-size: 13px; flex: 1; }
.metric b { font-size: 20px; font-weight: 700; }
.metric i { color: var(--text-faint); font-size: 12px; font-style: normal; }
</style>