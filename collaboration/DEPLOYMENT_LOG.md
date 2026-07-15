# 部署日志

> **最后更新**: 2026-07-13  
> **更新者**: Local-A  
> **谁可以更新**: 所有助手

---

## 使用说明

1. **每次部署后追加记录**，不要删除旧记录
2. 按时间倒序排列，最新的在最上面
3. 部署失败也要记录，方便排查问题
4. 任何助手都可以执行部署并更新此文件
5. 部署前建议先看 `ENV_CONFIG.md` 了解环境配置

---

## 部署记录模板

```markdown
### 2026-07-13 15:00 - P1稳定化部署（示例）

| 字段 | 值 |
|------|-----|
| **部署ID** | DEPLOY-P1-001 |
| **关联任务** | P1-STABILIZATION / P1-H10 |
| **部署版本** | v12.1.0 |
| **部署环境** | VM Ubuntu 22.04 |
| **部署类型** | 增量更新 / 全量部署 / 回滚 |
| **结果** | ✅ 成功 / ❌ 失败 |
| **部署者** | VM-A |
| **commit hash** | abc1234 |

**部署步骤**:
1. 拉取代码: `git pull origin main`
2. 安装依赖: `pip install -e .`
3. 构建前端: `cd dashboard/frontend && pnpm build`
4. 重启服务: `systemctl restart lingwen-backend`
5. 验证: `curl http://localhost:8000/api/health`

**变更内容**:
- 前端API timeout修复
- FastAPI中间件添加
- Ripple N+1查询优化

**遇到的问题**:
- 问题1：描述和解决方案

**日志路径**: `logs/deployment/2026-07-13-p1-stabilization.log`
**备注**: 无
```

---

## 部署记录

### 2026-07-13 10:00 - Phase 15.0 T1 部署（本地）

| 字段 | 值 |
|------|-----|
| **部署ID** | DEPLOY-15T1-001 |
| **关联任务** | Phase 15.0 T1 |
| **部署版本** | v12.0.0 |
| **部署环境** | Windows 10 本地 |
| **部署类型** | 增量更新 |
| **结果** | ✅ 成功 |
| **部署者** | Local-A |
| **commit hash** | a9ed735a |

**部署步骤**:
1. 确认代码: `git log --oneline -1`
2. 安装依赖: `pip install -e .`
3. 构建前端: `cd dashboard/frontend && pnpm build`
4. 启动服务: `python dashboard/app.py`
5. 验证: `curl http://localhost:8000/api/health`

**变更内容**:
- dashboard/app.py 6265→296行重构
- 11 routes modules拆分
- Pydantic v2 forward refs修复

**备注**: Phase 15.0 T1 完成后的本地部署验证

---

## 部署配置参考

### systemd 服务配置示例

```ini
# /etc/systemd/system/lingwen-backend.service

[Unit]
Description=LingWen Backend Service
After=network.target

[Service]
Type=simple
User=ailearn
WorkingDirectory=/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen
Environment=LINGWEN_PROJECT_ROOT=/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen
Environment=MINIMAX_API_KEY=sk-xxx
ExecStart=/home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/venv/bin/uvicorn dashboard.app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Nginx 反向代理配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /home/ailearn/projects/LingWen/dashboard/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 标准部署流程

### 完整部署流程

```bash
# 1. 进入项目目录
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen

# 2. 拉取最新代码
git pull origin main

# 3. 切换到部署分支（如有）
git checkout deployment

# 4. 安装/更新依赖
pip install -e .

# 5. 构建前端
cd dashboard/frontend
pnpm install
pnpm build
cd ../..

# 6. 运行测试（可选但推荐）
pytest -q
cd dashboard/frontend && pnpm test
cd ../..

# 7. 备份数据库（重要）
cp infra/.state/*.db backups/

# 8. 重启服务
systemctl restart lingwen-backend

# 9. 验证部署
curl http://localhost:8000/api/health

# 10. 记录部署日志
# 编辑 collaboration/DEPLOYMENT_LOG.md 添加记录
```

### 快速部署（仅代码更新）

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen
git pull origin main
systemctl restart lingwen-backend
curl http://localhost:8000/api/health
```

### 回滚流程

```bash
# 1. 停止服务
systemctl stop lingwen-backend

# 2. 回滚代码
git revert <commit-hash>
# 或
git checkout <previous-tag>

# 3. 恢复数据库
cp backups/*.db infra/.state/

# 4. 重启服务
systemctl start lingwen-backend

# 5. 验证回滚
curl http://localhost:8000/api/health

# 6. 记录回滚日志
```

---

## 部署状态看板

| 环境 | 版本 | 状态 | 最后部署 | 部署者 |
|------|------|------|----------|--------|
| 本地开发 | v12.0.0 | ✅ 运行中 | 2026-07-13 | Local-A |
| VM测试 | - | ⏳ 待部署 | - | - |
| CI | v12.0.0 | ✅ 构建通过 | 2026-07-13 | CI Bot |

---

## 部署检查清单

### 部署前

- [ ] 代码已提交并 push
- [ ] 本地测试通过
- [ ] 数据库已备份
- [ ] 有回滚计划

### 部署后

- [ ] 服务正常启动
- [ ] API 健康检查通过
- [ ] 前端页面可访问
- [ ] 核心功能正常
- [ ] 日志无异常错误
- [ ] 部署记录已更新

---

## 最近变更

| 时间 | 更新者 | 变更 |
|------|--------|------|
| 2026-07-13 10:00 | Local-A | 初始化部署日志，添加本地基线部署记录 |
| 2026-07-13 11:00 | Local-A | 将黑板从 novel-factory/ 移至 LingWen/ 根目录 |