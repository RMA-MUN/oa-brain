# DjangoOfficeProject - 智能OA系统后端服务

提供用户认证、考勤管理、员工管理、文件管理和通知管理等核心业务API。

## 环境要求

- Python 3.8+
- MySQL 5.7+
- Redis 6.0+

## 技术栈

| 技术 | 说明 |
|------|------|
| Django 5.2.6 | Web框架 |
| Django REST Framework | RESTful API |
| Celery | 异步任务 |
| Redis | 缓存/消息队列 |
| MySQL | 业务数据库 |
| JWT | 认证机制 |

## 项目结构

```
DjangoOfficeProject/
├── DjangoOfficeProject/      # 项目配置
│   ├── settings.py          # 主配置文件
│   ├── celery.py            # Celery配置
│   └── urls.py              # 路由配置
├── apps/                     # 业务模块
│   ├── officeAuth/          # 用户认证
│   ├── officeAttendance/    # 考勤管理
│   ├── staff/              # 员工管理
│   ├── file/               # 文件管理
│   ├── inform/             # 通知系统
│   └── home/               # 首页功能
├── media/                    # 媒体文件
├── templates/                # HTML模板
└── manage.py                 # 管理脚本
```

## 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/RMA-MUN/oa-brain
cd DjangoOfficeProject
```

### 2. 创建虚拟环境

```bash
pip install uv
uv sync
```

### 3. 配置数据库

在 `settings.py` 中配置MySQL连接：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_oa',
        'USER': 'root',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### 4. 配置邮件服务（可选）

用于用户注册激活功能：

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@qq.com'
EMAIL_HOST_PASSWORD = 'your_email_password'
```

### 5. 初始化数据库

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. 启动Redis

```bash
redis-server.exe
```

### 7. 启动Celery Worker

```bash
celery -A DjangoOfficeProject worker -l INFO -P gevent -Q celery,email
```

### 8. 启动Django服务

```bash
python manage.py runserver
```

服务运行于：http://127.0.0.1:8000

## API接口

| 模块 | 端点 | 说明 |
|------|------|------|
| officeAuth | `/officeAuth/` | 用户注册、登录、认证 |
| officeAttendance | `/Attendance/` | 请假申请、审批、考勤记录 |
| staff | `/staff/` | 员工信息管理、邮件通知 |
| file | `/file/` | 文件上传下载 |
| inform | `/inform/` | 通知发布、阅读跟踪 |
| home | `/home/` | 首页数据统计 |

## 模块说明

| 模块 | 核心文件 | 主要功能 |
|------|----------|----------|
| officeAuth | views.py | JWT认证、用户管理、部门管理 |
| officeAttendance | views.py | 请假申请、审批流程 |
| staff | views.py/tasks.py | 员工CRUD、异步邮件 |
| file | views.py | 文件存储、分类管理 |
| inform | views.py | 通知发布、可见性控制 |
| home | views.py | 数据聚合展示 |

## 开发说明

### 异步任务

邮件发送等耗时操作通过Celery异步执行：

```python
# apps/staff/tasks.py
@shared_task
def send_welcome_email(user_id):
    # 异步发送欢迎邮件
    pass
```

### 认证机制

所有需认证API请求需在Header中携带JWT令牌：

```
Authorization: Bearer <token>
```

### 跨域配置

已配置CORS，允许前端3000端口访问。

## 常见问题

**Q: 邮件发送失败？**
- 检查SMTP配置是否正确
- 确认邮箱已开启SMTP服务
- 查看logs.log错误日志

**Q: Celery任务不执行？**
- 确认Redis服务运行正常
- 检查Celery Worker是否启动
- 查看Worker日志错误信息

**Q: 图片无法访问？**
- 检查media目录权限
- 确认MEDIA_URL和MEDIA_ROOT配置正确
