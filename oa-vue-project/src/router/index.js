import { createRouter, createWebHistory } from 'vue-router'
import login from '@/views/login/login.vue'
import frame from '@/views/main/frame.vue'
import empAttendance from '@/views/attendance/empAttendance.vue'
import myAttendance from '@/views/attendance/myAttendance.vue'
import informPublic from '@/views/inform/public.vue'
import informList from '@/views/inform/list.vue'
import informDetail from '@/views/inform/detail.vue'
import home from '@/views/home/home.vue'
import aiChat from '@/views/ai/chat.vue'
import { useAuthStore } from '@/stores/auth.js'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'frame',
      component: frame,
      children: [
        {
          path: '/attendance/emp',
          name: 'empAttendance',
          component: empAttendance,
        },
        {
          path: '/attendance/my',
          name: 'myAttendance',
          component: myAttendance,
        },
        {
          path: '/inform/public',
          name: 'informPublic',
          component: informPublic,
        },
        {
          path: '/inform/list',
          name: 'informList',
          component: informList,
        },
        {
          path: '/inform/detail/:id',
          name: 'informDetail',
          component: informDetail,
        },
        {
          path: '/staff/list',
          name: 'staffList',
          component: () => import('@/views/staff/list.vue'),
          meta: { requiresPermission: true, permissionType: 'staff' },
        },
        {
          path: '/staff/add',
          name: 'staffAdd',
          component: () => import('@/views/staff/add.vue'),
          meta: { requiresPermission: true, permissionType: 'staff' },
        },
        {
          path: '/',
          name: 'home',
          component: home,
        },
        {
          path: '/ai/chat/:session_id?',
          name: 'aiChat',
          component: aiChat,
        },
      ],
    },
    {
      path: '/login',
      name: 'login',
      component: login,
    },
  ],
})

// 检查用户是否有权限访问员工模块
function hasStaffPermission() {
  const authStore = useAuthStore()
  const user = authStore.user

  // 检查用户是否存在
  if (!user || typeof user !== 'object') {
    return false
  }

  // 检查是否为superuser
  if (user.is_superuser === true || user.is_superuser === 'true') {
    return true
  }

  // 检查是否为部门领导
  if (user.is_leader === true || user.is_leader === 'true') {
    return true
  }

  // 检查是否有其他可能表示领导权限的字段
  // 这里可以根据实际后端返回的用户数据结构进行调整
  if (user.role === 'leader' || user.position === 'department_leader') {
    return true
  }

  return false
}

router.beforeEach((to, from, next) => {
  // 用户是否登录的路由守卫
  const authStore = useAuthStore()
  const token = authStore.token

  if (!token && to.name !== 'login') {
    // 用户未登录, 则跳转到登录页
    next({ name: 'login' })
  } else {
    // 如果用户已登录，检查是否需要特定权限
    if (to.meta.requiresPermission && to.meta.permissionType === 'staff') {
      // 检查是否有访问员工模块的权限
      if (!hasStaffPermission()) {
        ElMessage.warning('您没有权限访问员工管理模块')
        // 重定向到首页或其他合适的页面
        next({ path: '/' })
        return
      }
    }
    // 继续导航
    next()
  }
})

export default router
