<script setup lang="ts">
// @ts-nocheck
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function login() {
  if (!username.value || !password.value) { ElMessage.warning('请输入用户名和密码'); return }
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '登录失败')
  } finally { loading.value = false }
}
</script>

<template>
  <div class="auth-page">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>

    <div class="auth-card">
      <div class="logo">🥗</div>
      <h1 class="title">轻食记</h1>
      <p class="sub">欢迎回来，记录今天的每一餐</p>

      <div class="field">
        <label>用户名</label>
        <el-input v-model="username" placeholder="请输入用户名" size="large" @keyup.enter="login" />
      </div>
      <div class="field">
        <label>密码</label>
        <el-input v-model="password" type="password" placeholder="请输入密码" size="large" show-password @keyup.enter="login" />
      </div>

      <el-button type="primary" size="large" class="submit" :loading="loading" @click="login">登录</el-button>

      <div class="foot">还没有账号？<router-link to="/register">立即注册</router-link></div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(150deg, #d1fae5 0%, #ecfdf5 45%, #f0fdf4 100%);
  overflow: hidden;
}

.blob { position: absolute; border-radius: 50%; filter: blur(70px); opacity: .55; }
.blob-1 { width: 420px; height: 420px; background: #6ee7b7; top: -120px; right: -100px; }
.blob-2 { width: 320px; height: 320px; background: #a7f3d0; bottom: -100px; left: -80px; }
.blob-3 { width: 200px; height: 200px; background: #5eead4; top: 42%; left: 14%; opacity: .35; }

.auth-card {
  position: relative;
  z-index: 1;
  width: 380px;
  background: rgba(255, 255, 255, .88);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, .75);
  border-radius: 24px;
  padding: 40px 36px;
  box-shadow: 0 24px 60px rgba(6, 95, 70, .16);
}

.logo {
  width: 56px; height: 56px;
  margin: 0 auto 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, #10b981, #34d399);
  display: flex; align-items: center; justify-content: center;
  font-size: 30px;
  box-shadow: 0 10px 24px rgba(16, 185, 129, .35);
}

.title { text-align: center; font-size: 24px; font-weight: 700; letter-spacing: 3px; color: #0a5c43; margin: 0 0 6px; }
.sub { text-align: center; font-size: 13px; color: #6b7280; margin: 0 0 28px; }

.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; color: #4b5563; margin-bottom: 6px; font-weight: 500; }

.submit { width: 100%; margin-top: 8px; height: 44px; font-size: 15px; }

.foot { margin-top: 20px; text-align: center; font-size: 13px; color: #6b7280; }
.foot a { color: #059669; text-decoration: none; font-weight: 600; }
</style>
