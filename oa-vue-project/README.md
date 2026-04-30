# OA系统前端项目

这是一个基于Vue 3的办公自动化系统前端项目，提供员工管理、考勤管理、通知管理等功能。

## 技术栈

- **前端框架**: Vue 3 + Vue Router 4
- **状态管理**: Pinia
- **UI组件库**: Element Plus (基于Vue 3)
- **构建工具**: Vite
- **HTTP客户端**: Axios
- **富文本编辑器**: WangEditor
- **图表库**: ECharts
- **CSS框架**: Bootstrap
- **代码格式化**: Prettier

## 环境要求

- Node.js: ^20.19.0 或 >=22.12.0
- npm: 推荐使用最新版本

## 项目克隆

```bash
# 克隆项目到本地
https://github.com/RMA-MUN/oa-brain

# 进入项目目录
cd oa-vue-project
```

## 安装依赖

```bash
# 使用npm安装依赖
npm install

# 或使用yarn安装依赖
yarn install
```

## 项目启动

```bash
# 开发环境启动
npm run dev

# 或
yarn dev

# 构建生产版本
npm run build

# 或
yarn build

# 预览生产构建
npm run preview

# 或
yarn preview
```

## 项目结构

```
src/
├── api/            # API请求封装
├── assets/         # 静态资源
│   ├── css/        # CSS样式文件
│   ├── img/        # 图片资源
│   └── js/         # JS文件
├── components/     # 公共组件
├── router/         # 路由配置
├── stores/         # Pinia状态管理
├── views/          # 页面组件
├── App.vue         # 根组件
└── main.js         # 入口文件
```

## 主要功能模块

- **员工管理**: 员工信息的增删改查
- **考勤管理**: 考勤记录查看与统计
- **通知管理**: 系统通知发布与查看
- **AI对话**：深度集成AI服务，全自动考勤、通知等功能

## 代码规范

项目使用Prettier进行代码格式化，可通过以下命令格式化代码：

```bash
npm run format
# 或
yarn format
```

## 注意事项

1. 请确保Node.js版本符合要求
2. 开发环境配置在.env.development文件中
3. 生产环境配置在.env.production文件中
4. 构建后的文件位于dist目录下
