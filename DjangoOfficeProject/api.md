# API文档

## 1. 认证相关API

### 1.1 登录接口
- **URL**: `/officeAuth/login/`
- **方法**: POST
- **请求参数**:
  - `username`: 用户名 (必填)
  - `password`: 密码 (必填)
- **返回数据**:
  - 成功: `{"message": "用户名 登录成功", "user": {...}, "token": "JWT令牌"}`
  - 失败: `{"detail": {"username": ["用户名或密码错误"], "password": ["用户名或密码错误"]}}`
- **示例请求**:
  ```json
  {
    "username": "admin",
    "password": "password123"
  }
  ```
- **示例返回**:
  ```json
  {
    "message": "admin 登录成功",
    "user": {
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "username": "admin",
      "email": "admin@example.com",
      "department": "技术部"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### 1.2 重置密码接口
- **URL**: `/officeAuth/reset-password/`
- **方法**: POST
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
  - `old_password`: 旧密码 (必填)
  - `new_password`: 新密码 (必填)
  - `confirm_password`: 确认新密码 (必填)
- **返回数据**:
  - 成功: `{"message": "密码重置成功"}`
  - 失败: `{"detail": {"old_password": ["原密码错误"], "confirm_password": ["两次输入的密码不一致"]}}`
- **示例请求**:
  ```json
  {
    "old_password": "old123",
    "new_password": "new123",
    "confirm_password": "new123"
  }
  ```
- **示例返回**:
  ```json
  {
    "message": "密码重置成功"
  }
  ```

### 1.3 刷新Token接口
- **URL**: `/officeAuth/refresh-token/`
- **方法**: POST
- **请求参数**:
  - `token`: 旧Token (必填)
- **返回数据**:
  - 成功: `{"message": "Token刷新成功", "token": "新JWT令牌", "expire_time": 1234567890}`
  - 失败: `{"detail": "Token刷新失败"}`
- **示例请求**:
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **示例返回**:
  ```json
  {
    "message": "Token刷新成功",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expire_time": 1712345678
  }
  ```

### 1.4 获取用户详情接口
- **URL**: `/officeAuth/user/detail/`
- **方法**: GET
- **请求头**: `Authorization: Bearer <token>`
- **返回数据**:
  - 成功: `{"message": "获取用户详情成功", "user": {...}}`
- **示例返回**:
  ```json
  {
    "message": "获取用户详情成功",
    "user": {
      "uuid": "123e4567-e89b-12d3-a456-426614174000",
      "username": "admin",
      "email": "admin@example.com",
      "department": "技术部"
    }
  }
  ```

### 1.5 更新部门领导接口
- **URL**: `/officeAuth/department/update-leader/`
- **方法**: POST
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
  - `department_id`: 部门ID (必填)
  - `new_leader_id`: 新领导ID (必填)
- **返回数据**:
  - 成功: `{"message": "部门领导变更成功", "department": "技术部", "old_leader": "张三", "new_leader": "李四"}`
  - 失败: `{"error_message": "您没有权限变更部门领导"}`
- **示例请求**:
  ```json
  {
    "department_id": 1,
    "new_leader_id": "123e4567-e89b-12d3-a456-426614174000"
  }
  ```
- **示例返回**:
  ```json
  {
    "message": "部门领导变更成功",
    "department": "技术部",
    "old_leader": "张三",
    "new_leader": "李四"
  }
  ```

## 2. 考勤相关API

### 2.1 考勤记录接口
- **URL**: `/Attendance/attendance/`
- **方法**: GET, POST, PUT
- **请求头**: `Authorization: Bearer <token>`
- **GET请求参数**:
  - `who`: 查询范围 (可选，值为'requester', 'responser', 'leader', 'manager')
- **POST请求参数**:
  - `type`: 考勤类型ID (必填)
  - `start_time`: 开始时间 (必填)
  - `end_time`: 结束时间 (必填)
  - `reason`: 请假原因 (必填)
  - `responser`: 审批人ID (必填)
- **PUT请求参数**:
  - `status`: 审批状态 (必填，值为'approved', 'rejected')
  - `comment`: 审批意见 (可选)
- **返回数据**:
  - GET: 考勤记录列表
  - POST: 新创建的考勤记录
  - PUT: 更新后的考勤记录
- **示例GET请求**:
  ```
  GET /Attendance/attendance/?who=leader
  ```
- **示例POST请求**:
  ```json
  {
    "type": 1,
    "start_time": "2024-01-01 09:00:00",
    "end_time": "2024-01-02 18:00:00",
    "reason": "家中有事",
    "responser": "123e4567-e89b-12d3-a456-426614174000"
  }
  ```

### 2.2 考勤类型接口
- **URL**: `/Attendance/attendance-type/`
- **方法**: GET
- **返回数据**: 考勤类型列表
- **示例返回**:
  ```json
  [
    {"id": 1, "name": "事假"},
    {"id": 2, "name": "病假"},
    {"id": 3, "name": "年假"}
  ]
  ```

### 2.3 考勤审批人接口
- **URL**: `/Attendance/attendance-responser/`
- **方法**: GET
- **请求头**: `Authorization: Bearer <token>`
- **返回数据**: 当前用户的考勤审批人信息
- **示例返回**:
  ```json
  {
    "uuid": "123e4567-e89b-12d3-a456-426614174000",
    "username": "李四",
    "email": "lisi@example.com"
  }
  ```

## 3. 员工管理相关API

### 3.1 部门列表接口
- **URL**: `/staff/department/`
- **方法**: GET
- **请求头**: `Authorization: Bearer <token>`
- **返回数据**: 部门列表
- **示例返回**:
  ```json
  [
    {
      "id": 1,
      "name": "技术部",
      "leader": "张三",
      "members": ["张三", "李四", "王五"]
    },
    {
      "id": 2,
      "name": "市场部",
      "leader": "赵六",
      "members": ["赵六", "钱七"]
    }
  ]
  ```

### 3.2 用户列表接口
- **URL**: `/staff/user/`
- **方法**: GET
- **请求头**: `Authorization: Bearer <token>`
- **返回数据**: 按部门分组的用户列表
- **示例返回**:
  ```json
  {
    "技术部": {
      "leader": [
        {
          "uuid": "123e4567-e89b-12d3-a456-426614174000",
          "username": "张三",
          "email": "zhangsan@example.com"
        }
      ],
      "members": [
        {
          "uuid": "234e5678-f90a-23d4-b567-537725285011",
          "username": "李四",
          "email": "lisi@example.com"
        }
      ]
    }
  }
  ```

### 3.3 添加员工接口
- **URL**: `/staff/staff/`
- **方法**: POST
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
  - `username`: 用户名 (必填)
  - `password`: 密码 (必填)
  - `email`: 邮箱 (必填)
- **返回数据**:
  - 成功: `{"message": "添加员工成功，激活邮件正在发送中"}`
  - 失败: `{"error_message": {"username": ["用户名已存在"]}}`
- **示例请求**:
  ```json
  {
    "username": "newuser",
    "password": "password123",
    "email": "newuser@example.com"
  }
  ```

### 3.4 激活邮箱接口
- **URL**: `/staff/staff/activate/`
- **方法**: GET, POST
- **GET请求参数**:
  - `key`: 激活密钥 (从邮件链接获取)
- **POST请求参数**:
  - `password`: 密码 (必填)
- **返回数据**:
  - GET: 激活页面
  - POST成功: `{"message": "邮箱激活成功"}`
  - POST失败: `{"error_message": "激活链接无效"}`

### 3.5 编辑员工接口
- **URL**: `/staff/staff/edit/<uuid>/`
- **方法**: PUT
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
  - `username`: 用户名 (可选)
  - `email`: 邮箱 (可选)
  - `department`: 部门ID (可选)
- **返回数据**:
  - 成功: `{"message": "员工信息更新成功", "data": {...}}`
  - 失败: `{"error_message": "您没有权限编辑该员工信息"}`
- **示例请求**:
  ```json
  {
    "username": "updateduser",
    "email": "updated@example.com",
    "department": 2
  }
  ```

### 3.6 下载员工信息接口
- **URL**: `/staff/download/`
- **方法**: GET
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
  - `uuid`: 员工UUID (可多个，如?uuid=uuid1&uuid=uuid2)
- **返回数据**: Excel文件

## 4. 文件上传相关API

### 4.1 文件上传接口
- **URL**: `/file/upload/`
- **方法**: POST
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
  - `img`: 文件 (必填，multipart/form-data格式)
- **返回数据**:
  - 成功: `{"errno": 0, "data": {"url": "/media/img/xxx.png", "alt": "当前加载较为缓慢，请稍后重试", "href": "/media/img/xxx.png"}}`
  - 失败: `{"errno": 1, "message": "图片上传失败"}`

## 5. 通知相关API

### 5.1 通知管理接口
- **URL**: `/inform/inform/`
- **方法**: GET, POST, PUT, DELETE
- **请求头**: `Authorization: Bearer <token>`
- **GET请求参数**:
  - 支持分页参数 `page`, `page_size`
- **POST请求参数**:
  - `title`: 标题 (必填)
  - `content`: 内容 (必填)
  - `public`: 是否公开 (可选，默认False)
  - `department_ids`: 部门ID列表 (可选)
- **PUT请求参数**:
  - `title`: 标题 (可选)
  - `content`: 内容 (可选)
  - `public`: 是否公开 (可选)
  - `department_ids`: 部门ID列表 (可选)
- **返回数据**:
  - GET: 通知列表
  - POST: 新创建的通知
  - PUT: 更新后的通知
  - DELETE: 204 No Content
- **示例POST请求**:
  ```json
  {
    "title": "公司会议通知",
    "content": "全体员工请注意，明天下午2点在会议室召开全体会议",
    "public": true,
    "department_ids": [1, 2, 3]
  }
  ```

## 6. 首页相关API

### 6.1 最新通知接口
- **URL**: `/home/latest/inform/`
- **方法**: GET
- **请求头**: `Authorization: Bearer <token>`
- **返回数据**: 最新的十条通知
- **示例返回**:
  ```json
  [
    {
      "id": 1,
      "title": "公司会议通知",
      "content": "全体员工请注意...",
      "create_time": "2024-01-01T12:00:00Z"
    }
  ]
  ```

### 6.2 最新考勤记录接口
- **URL**: `/home/latest/attendance/`
- **方法**: GET
- **请求头**: `Authorization: Bearer <token>`
- **返回数据**: 最新的十条考勤记录
- **示例返回**:
  ```json
  [
    {
      "id": 1,
      "type": "事假",
      "start_time": "2024-01-01T09:00:00Z",
      "end_time": "2024-01-02T18:00:00Z",
      "status": "approved"
    }
  ]
  ```

### 6.3 部门员工数量接口
- **URL**: `/home/department/staff/count/`
- **方法**: GET
- **请求头**: `Authorization: Bearer <token>`
- **返回数据**: 每个部门的员工数量
- **示例返回**:
  ```json
  [
    {"name": "技术部", "staff_count": 10},
    {"name": "市场部", "staff_count": 5}
  ]
  ```

## 7. 认证要求

- 除了登录、注册和获取考勤类型等少数接口外，大多数接口都需要在请求头中添加 `Authorization: Bearer <token>` 进行身份验证
- Token有效期为24小时，过期后需要使用刷新Token接口获取新Token
- 不同接口对用户权限有不同要求，例如：
  - 只有超级用户或部门负责人可以编辑员工信息
  - 只有超级用户或高级管理层可以变更部门领导
  - 普通员工只能查看自己或同部门员工的信息

## 8. 错误处理

- 400 Bad Request: 请求参数错误
- 401 Unauthorized: 未授权，Token无效或过期
- 403 Forbidden: 禁止访问，没有权限
- 404 Not Found: 资源不存在
- 500 Internal Server Error: 服务器内部错误

## 9. 分页

- 支持分页的接口默认每页显示10条数据
- 可以通过 `page` 和 `page_size` 参数调整
- 分页响应格式：
  ```json
  {
    "count": 100,
    "next": "http://example.com/api/?page=2",
    "previous": null,
    "results": [...]
  }
  ```