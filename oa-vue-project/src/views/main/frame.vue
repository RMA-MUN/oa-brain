<template>
  <el-container class="container">
    <transition name="slide">
      <el-aside class="aside" :width="asideWidth">
        <router-link to="/" class="brand">企翼<span v-show="!isCollapse">管理系统</span>
        </router-link>

        <el-menu active-text-color="#ffd04b" background-color="#3e4248" class="el-menu-vertical-demo" default-active="1"
          text-color="#fff" :collapse="isCollapse" :router="true">

          <el-menu-item index="1" route="/">
            <el-icon>
              <House />
            </el-icon>
            <span>首页</span>
          </el-menu-item>

          <el-sub-menu index="2" route="/attendance">
            <template #title>
              <el-icon>
                <Checked />
              </el-icon>
              <span>考勤</span>
            </template>

            <el-menu-item-group>
              <el-menu-item index="1-1" route="/attendance/emp" v-if="authStore.user.is_superuser">
                <el-icon>
                  <User />
                </el-icon>
                <span>员工考勤</span>
              </el-menu-item>

              <el-menu-item index="1-2" route="/attendance/my">
                <el-icon>
                  <UserFilled />
                </el-icon>
                <span>个人考勤</span>
              </el-menu-item>
            </el-menu-item-group>
          </el-sub-menu>

          <el-sub-menu index="3">
            <template #title>
              <el-icon>
                <BellFilled />
              </el-icon>
              <span>通知</span>
            </template>

            <el-menu-item-group>
              <el-menu-item index="2-1" route="/inform/public" v-if="authStore.user.is_superuser">
                <el-icon>
                  <Plus />
                </el-icon>
                <span>发布通知</span>
              </el-menu-item>

              <el-menu-item index="2-2" route="/inform/list">
                <el-icon>
                  <MessageBox />
                </el-icon>
                <span>查看通知</span>
              </el-menu-item>
            </el-menu-item-group>>
          </el-sub-menu>

          <el-sub-menu index="4" v-if="authStore.user && (authStore.user.is_superuser || authStore.user.is_leader)">
            <template #title>
              <el-icon>
                <Checked />
              </el-icon>
              <span>员工</span>
            </template>

            <el-menu-item-group>
              <el-menu-item index="4-1" route="/staff/add">
                <el-icon>
                  <CirclePlusFilled />
                </el-icon>
                <span>添加员工</span>
              </el-menu-item>

              <el-menu-item index="4-2" route="/staff/list">
                <el-icon>
                  <List />
                </el-icon>
                <span>员工列表</span>
              </el-menu-item>
            </el-menu-item-group>>
          </el-sub-menu>

          <el-menu-item index="5" route="/ai/chat">
            <el-icon>
              <ChatDotRound />
            </el-icon>
            <span>AI助手</span>
          </el-menu-item>

        </el-menu>
      </el-aside>
    </transition>
    <el-container>
      <el-header class="header">

        <div class="left-header">
          <div class="CollapseBtn">
            <el-button v-show="!isCollapse" circle @click="changeCollapse">
              <el-icon>
                <Fold />
              </el-icon>
            </el-button>
            <el-button v-show="isCollapse" circle @click="changeCollapse">
              <el-icon>
                <Expand />
              </el-icon>
            </el-button>
          </div>
        </div>

        <el-dropdown>

          <span class="el-dropdown-link">
            <el-avatar src="src/assets/img/dog.png" />
            <div class="UsernameInfo">
              <span>{{ username }}</span>
            </div>
            <el-icon class="el-icon--right">
              <arrow-down />
            </el-icon>
          </span>

          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="showProfileBox">个人信息</el-dropdown-item>
              <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>

        </el-dropdown>

      </el-header>

      <el-main class="main">
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>

  <el-dialog v-model="profileVisible" title="个人信息" width="600px" center>
    <div class="profile-content">
      <!-- 基本信息卡片 -->
      <el-card class="profile-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        <div class="card-content">
          <div class="info-row">
            <div class="info-col">
              <el-form label-width="100px" :inline="true">
                <el-form-item label="用户名">
                  <span class="info-text primary">{{ username }}</span>
                </el-form-item>
                <el-form-item label="用户UUID">
                  <span class="info-text">
                    <el-tooltip :content="authStore.user?.uuid || '-'" placement="top">
                      <span>{{ (authStore.user?.uuid || '').substring(0, 10) + '...' }}</span>
                    </el-tooltip>
                  </span>
                </el-form-item>
              </el-form>
            </div>
            <div class="info-col">
              <el-form label-width="100px" :inline="true">
                <el-form-item label="邮箱">
                  <span class="info-text">{{ authStore.user?.email || '-' }}</span>
                </el-form-item>
                <el-form-item label="电话">
                  <span class="info-text">{{ authStore.user?.telephone || '-' }}</span>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 部门信息卡片 -->
      <el-card class="profile-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>部门信息</span>
          </div>
        </template>
        <div class="card-content">
          <div class="info-row">
            <div class="info-col">
              <el-form label-width="100px" :inline="true">
                <el-form-item label="所属部门">
                  <span class="info-text">{{ authStore.user?.department?.name || '-' }}</span>
                </el-form-item>
              </el-form>
            </div>
            <div class="info-col">
              <el-form label-width="100px" :inline="true">
                <el-form-item label="部门领导">
                  <span class="info-text">{{ authStore.user?.department?.leader_name || '-' }}</span>
                </el-form-item>
              </el-form>
            </div>
          </div>
          <div class="info-row">
            <div class="info-col">
              <el-form label-width="100px" :inline="true">
                <el-form-item label="直接上级">
                  <span class="info-text">{{ authStore.user?.department?.manager_name || '-' }}</span>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 状态信息卡片 -->
      <el-card class="profile-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>状态信息</span>
          </div>
        </template>
        <div class="card-content">
          <div class="info-row">
            <div class="info-col">
              <el-form label-width="100px" :inline="true">
                <el-form-item label="用户状态">
                  <el-tag :type="authStore.user?.is_active ? 'success' : 'danger'">{{ authStore.user?.is_active ? '在职' :
                    '离职' }}</el-tag>
                </el-form-item>
                <el-form-item label="权限级别">
                  <el-tag
                    :type="authStore.user?.is_superuser ? 'warning' : authStore.user?.is_staff ? 'primary' : 'info'">{{
                      authStore.user?.is_superuser ? '超级管理员' : authStore.user?.is_staff ? '管理员' : '普通用户' }}</el-tag>
                </el-form-item>
              </el-form>
            </div>
          </div>
          <div class="info-row">
            <div class="info-col">
              <el-form label-width="100px" :inline="true">
                <el-form-item label="最后登录">
                  <span class="info-text">{{ formatDate(authStore.user?.last_login) || '-' }}</span>
                </el-form-item>
              </el-form>
            </div>
            <div class="info-col">
              <el-form label-width="100px" :inline="true">
                <el-form-item label="入职时间">
                  <span class="info-text">{{ formatDate(authStore.user?.date_joined) || '-' }}</span>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
      </el-card>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="profileVisible = false">关闭</el-button>
        <el-button type="primary" @click="showChangePasswordDialog">修改密码</el-button>
      </div>
    </template>
  </el-dialog>

  <el-dialog v-model="dialogVisible" title="个人信息" width="500">
    <el-form :model="reSetPassword" :rules="rules" ref="reSetPasswordForm" :label-width="formLabelWidth">
      <el-form-item label="旧密码" :label-width="formLabelWidth" prop="oldPassword">
        <el-input v-model="reSetPassword.oldPassword" style="width: 240px" type="password" autocomplete="off"
          show-password />
      </el-form-item>
      <el-form-item label="新密码" :label-width="formLabelWidth" prop="newPassword">
        <el-input v-model="reSetPassword.newPassword" style="width: 240px" type="password" autocomplete="off"
          show-password />
      </el-form-item>
      <el-form-item label="确认新密码" :label-width="formLabelWidth" prop="confirmPassword">
        <el-input v-model="reSetPassword.confirmPassword" style="width: 240px" type="password" autocomplete="off"
          show-password @keyup.enter="handleSubmit" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">
          确认
        </el-button>
      </div>
    </template>
  </el-dialog>

</template>

<script setup name="Frame">
// 导入外部JS逻辑
import useFrameComposable from '@/assets/js/frame.js'
import { ChatDotRound } from '@element-plus/icons-vue'

// 解构获取所有状态和方法
const {
  isCollapse,
  authStore,
  profileVisible,
  dialogVisible,
  reSetPassword,
  rules,
  formLabelWidth,
  asideWidth,
  username,
  logout,
  showChangePasswordDialog,
  showProfileBox,
  formatDate,
  handleSubmit,
  changeCollapse
} = useFrameComposable()
</script>

<!-- 导入外部CSS样式 -->
<style scoped>
@import url('@/assets/css/frame.css');
</style>
