<script setup lang="ts">
// @ts-nocheck
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isAuthPage = computed(() => route.path === '/login' || route.path === '/register')

const navs = [
  { path: '/dashboard', label: '营养看板', icon: 'DataLine' },
  { path: '/record', label: '饮食记录', icon: 'Dish' },
  { path: '/profile', label: '体征档案', icon: 'User' },
  { path: '/advice', label: '健康建议', icon: 'ChatDotRound' },
  { path: '/history', label: '历史回溯', icon: 'Calendar' },
  { path: '/foods', label: '食物库', icon: 'Collection' },
  { path: '/guidelines', label: '文献库', icon: 'Reading' },
]

const avatar = computed(() => (auth.displayName || '?').charAt(0))

const pwdVisible = ref(false)
const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')
const pwdLoading = ref(false)

onMounted(async () => {
  if (auth.token && !auth.user) {
    try { await auth.fetchMe() } catch { auth.logout() }
  }
})

async function onCommand(cmd: string) {
  if (cmd === 'logout') {
    await auth.logout()
    router.push('/login')
  } else if (cmd === 'password') {
    oldPwd.value = ''
    newPwd.value = ''
    confirmPwd.value = ''
    pwdVisible.value = true
  }
}

async function submitPassword() {
  if (!oldPwd.value || !newPwd.value) { ElMessage.warning('请填写完整'); return }
  if (newPwd.value.length < 6) { ElMessage.warning('新密码至少6位'); return }
  if (newPwd.value !== confirmPwd.value) { ElMessage.warning('两次密码不一致'); return }
  pwdLoading.value = true
  try {
    await auth.changePassword(oldPwd.value, newPwd.value)
    ElMessage.success('密码已修改，请重新登录')
    pwdVisible.value = false
    await auth.logout()
    router.push('/login')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '修改失败')
  } finally { pwdLoading.value = false }
}
</script>

<template>
  <router-view v-if="isAuthPage" />

  <div v-else class="layout">
    <img class="deco deco-salad" src="/deco/salad.svg" alt="" />
    <img class="deco deco-leaf" src="/deco/leaf.svg" alt="" />
    <img class="deco deco-avocado" src="/deco/avocado.svg" alt="" />
    <img class="deco deco-grapes" src="/deco/grapes.svg" alt="" />

    <aside class="sidebar">
      <div class="brand">
        <span class="brand-logo">🥗</span>
        <span class="brand-name">轻食记</span>
      </div>
      <nav class="nav">
        <router-link v-for="n in navs" :key="n.path" :to="n.path"
          class="nav-item" :class="{ active: route.path === n.path }">
          <el-icon class="nav-icon"><component :is="n.icon" /></el-icon>
          <span class="nav-label">{{ n.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-foot">基于 RAG 的智能营养分析</div>
    </aside>

    <div class="main">
      <header class="topbar">
        <span class="top-slogan">五谷为养，五果为助，五畜为益，五菜为充 ——《黄帝内经》</span>
        <el-dropdown trigger="click" @command="onCommand">
          <div class="user">
            <el-avatar :size="30" class="avatar">{{ avatar }}</el-avatar>
            <span class="uname">{{ auth.displayName }}</span>
            <span class="caret">▾</span>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>

  <el-dialog v-model="pwdVisible" title="修改密码" width="380px">
    <el-input v-model="oldPwd" type="password" placeholder="原密码" show-password style="margin-bottom: 12px" />
    <el-input v-model="newPwd" type="password" placeholder="新密码（至少6位）" show-password style="margin-bottom: 12px" />
    <el-input v-model="confirmPwd" type="password" placeholder="确认新密码" show-password />
    <template #footer>
      <el-button @click="pwdVisible = false">取消</el-button>
      <el-button type="primary" :loading="pwdLoading" @click="submitPassword">确认修改</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.layout { display: flex; min-height: 100vh; }

/* 全局固定角落装饰：挂在视口、位于内容层之下、露在空白处 */
.deco { position: fixed; z-index: 0; pointer-events: none; }
.deco-salad { bottom: 16px; right: 18px; width: 170px; transform: rotate(10deg); opacity: .14; }
.deco-leaf { bottom: 150px; right: 44px; width: 66px; transform: rotate(28deg); opacity: .11; }
.deco-avocado { top: 44%; right: 6px; width: 72px; transform: rotate(-18deg); opacity: .1; }
.deco-grapes { bottom: 40px; right: 36%; width: 56px; opacity: .08; }

.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #f0fdf4 0%, #e0f5e9 100%);
  border-right: 1px solid #d6ede1;
  display: flex;
  flex-direction: column;
  padding: 22px 16px;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 2;
}

.brand { display: flex; align-items: center; gap: 12px; padding: 4px 10px 28px; }
.brand-logo {
  width: 42px; height: 42px;
  border-radius: 13px;
  background: linear-gradient(135deg, #10b981, #34d399);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px;
  box-shadow: 0 6px 14px rgba(16, 185, 129, .28);
}
.brand-name { font-size: 24px; font-weight: 700; letter-spacing: 3px; color: #0a5c43; }

.nav { display: flex; flex-direction: column; gap: 6px; flex: 1; }
.nav-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  text-decoration: none;
  color: #4a7764;
  font-size: 16px; font-weight: 500;
  transition: all .18s ease;
}
.nav-item:hover { background: rgba(16, 185, 129, .1); color: #0a5c43; transform: translateX(2px); }
.nav-item.active {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 6px 14px rgba(16, 185, 129, .32);
}
.nav-icon { font-size: 20px; }
.sidebar-foot { font-size: 12px; color: #7aa894; text-align: center; padding-top: 14px; }

.main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.topbar {
  height: 64px;
  background: rgba(255, 255, 255, .9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: flex-end;
  padding: 0 24px;
  flex-shrink: 0;
  position: sticky; top: 0; z-index: 10;
}
.top-slogan {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font-size: 15px;
  color: #065f46;
  font-weight: 500;
  letter-spacing: 1px;
}
.user { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 6px 10px; border-radius: 10px; }
.user:hover { background: #f0faf5; }
.avatar { background: linear-gradient(135deg, #10b981, #34d399); color: #fff; font-weight: 600; }
.uname { font-size: 14px; color: var(--text-main); }
.caret { color: var(--text-faint); font-size: 12px; }
.content { flex: 1; padding: 28px 32px; position: relative; z-index: 1; }
</style>