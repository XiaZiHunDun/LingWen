# 环境配置手册

> **最后更新**: 2026-07-13  
> **适用版本**: v12

---

## 1. 环境变量

### 1.1 必选环境变量

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `LINGWEN_PROJECT_ROOT` | 项目根目录 | 当前目录 | `/home/ailearn/projects/LingWen` |

### 1.2 LLM相关

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `MINIMAX_API_KEY` | MiniMax API Key | 无 | `sk-xxx` |
| `OPENAI_API_KEY` | OpenAI API Key | 无 | `sk-xxx` |
| `ANTHROPIC_API_KEY` | Anthropic API Key | 无 | `sk-xxx` |
| `LLM_PROVIDER` | 默认LLM提供商 | `minimax` | `minimax/openai/anthropic` |

### 1.3 数据库相关

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `WORKFLOW_DB_PATH` | 工作流数据库路径 | `.state/workflow.db` | `/data/workflow.db` |
| `RIPPLE_DB_PATH` | 涟漪数据库路径 | `.state/ripple.db` | `/data/ripple.db` |
| `COST_TRACKER_DB_PATH` | 成本追踪数据库路径 | `.state/cost_tracker.db` | `/data/cost_tracker.db` |

### 1.4 服务相关

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `DASHBOARD_PORT` | 后端服务端口 | 8000 | 8765 |
| `FRONTEND_PORT` | 前端开发端口 | 5173 | 3000 |
| `ALLOWED_ORIGINS` | CORS允许的来源 | `*` | `http://localhost:5173` |

### 1.5 测试相关

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `LINGWEN_ALLOW_STRESS_TEST` | 是否允许压力测试 | 0 | 1 |
| `LINGWEN_E2E_LIVE` | 是否运行Live E2E测试 | 0 | 1 |
| `LINGWEN_POST_CHECK_LLM` | 是否运行LLM后检查 | 1 | 0 |

### 1.6 开发相关

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `LINGWEN_DEBUG` | 调试模式 | 0 | 1 |
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG/WARN/ERROR` |

---

## 2. 环境搭建步骤

### 2.1 本地开发环境（Windows）

```bash
# 1. 进入项目目录
cd /y/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装后端依赖
pip install -e .

# 4. 安装前端依赖
cd dashboard/frontend
pnpm install
cd ../..

# 5. 创建环境变量文件
cp .env.example .env
# 编辑 .env 添加 API Key

# 6. 验证安装
pytest -q                          # 期望3274 passed
cd dashboard/frontend && pnpm test # 期望192 passed
```

### 2.2 虚拟机测试环境（Ubuntu）

```bash
# 1. 进入项目目录
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装后端依赖
pip install -e .

# 4. 安装前端依赖
cd dashboard/frontend
pnpm install
cd ../..

# 5. 创建环境变量文件
cp .env.example .env
# 编辑 .env 添加 API Key

# 6. 验证安装
pytest -q                          # 期望3274 passed
cd dashboard/frontend && pnpm test # 期望192 passed

# 7. 启动服务
python dashboard/app.py &          # 后端端口8000
cd dashboard/frontend && pnpm dev --port 5173 --strictPort &
```

---

## 3. 服务启动

### 3.1 后端服务

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen

# 开发模式
python dashboard/app.py

# 生产模式（使用uvicorn）
uvicorn dashboard.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3.2 前端服务

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/dashboard/frontend

# 开发模式
pnpm dev --port 5173 --strictPort

# 生产构建
pnpm build

# 预览构建结果
pnpm preview --port 5173
```

---

## 4. 环境检查清单

### 启动前检查

- [ ] Python 3.11+ 已安装
- [ ] Node.js 20+ 已安装
- [ ] pnpm 9+ 已安装
- [ ] 虚拟环境已激活
- [ ] 后端依赖已安装 (`pip install -e .`)
- [ ] 前端依赖已安装 (`pnpm install`)
- [ ] `.env` 文件已配置（至少包含 `MINIMAX_API_KEY`）
- [ ] `LINGWEN_PROJECT_ROOT` 环境变量已设置

### 服务健康检查

```bash
# 检查后端健康
curl http://localhost:8000/api/health

# 检查前端是否可访问
curl http://localhost:5173

# 检查数据库连接
python -c "from infra.state.database import get_connection; get_connection().connect()"
```

---

## 5. 常见问题

### Q: 前端依赖安装失败？

```bash
# 清理缓存重试
pnpm store prune
pnpm install --shamefully-hoist
```

### Q: pytest 运行报错？

```bash
# 检查虚拟环境
which python
pip list | grep pytest

# 更新依赖
pip install -e . --upgrade
```

### Q: 服务启动后无法访问？

```bash
# 检查端口占用
lsof -i :8000
lsof -i :5173

# 检查防火墙
sudo ufw status
sudo ufw allow 8000
sudo ufw allow 5173
```

---

## 6. 协作黑板访问

### 位置

```
LingWen/
└── collaboration/
    ├── COLLABORATION_GUIDE.md
    ├── CURRENT_STATUS.md
    ├── ACTIVE_TASK.md
    ├── BACKLOG.md
    ├── TEST_LOG.md
    ├── DEPLOYMENT_LOG.md
    └── ENV_CONFIG.md
```

### 快速查看

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen

cat collaboration/CURRENT_STATUS.md
cat collaboration/ACTIVE_TASK.md
cat collaboration/BACKLOG.md
```