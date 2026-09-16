# FlowPilot 开发环境

环境：WSL Ubuntu 24.04、Windows VS Code + Remote WSL、Python 3.12、uv、Node.js、npm、Git。

## 安装项目依赖

在项目根目录执行：

```bash
uv sync --locked
cd frontend
npm ci
```

Python 依赖安装在根目录 `.venv`，前端依赖安装在 `frontend/node_modules`。
`uv.lock` 和 `frontend/package-lock.json` 用于复现版本。
由于本次官方 PyPI 下载速度异常缓慢，Python 项目已配置清华大学 PyPI 镜像，配置位于 `pyproject.toml`。

## 启动 PostgreSQL 16 和 Redis

先在 Windows 启动 Docker Desktop，在 Settings → Resources → WSL Integration 中启用当前 Ubuntu 并应用。

首次配置时复制 `.env.example` 为 `.env`，修改密码及 DATABASE_URL 中的对应密码。本次初始化已生成本地 `.env`，无需覆盖。

```bash
docker compose up -d --wait
docker compose ps
```

数据库：`localhost:5432`，用户名/数据库名均为 `flowpilot`；Redis：`localhost:6379`。
数据保存在 Docker volumes 中。

## 启动开发服务

分别在三个 WSL 终端中执行：

```bash
# 项目根目录：FastAPI，http://localhost:8000/docs
uv run --env-file .env uvicorn backend.app.main:app --reload
```

```bash
# 项目根目录：Celery，需要 Redis 已启动
uv run --env-file .env celery -A backend.app.worker:app worker --loglevel=info
```

```bash
# 前端：http://localhost:5173
cd frontend
npm run dev
```

`GET /health` 是后端启动检查接口。LangGraph、LangChain 已列入依赖，使用模型时再配置对应提供商和 API key。
后端配置统一定义在 `backend/app/core/config.py`，从环境变量或项目根目录 `.env` 加载，并由 API、数据库和 Celery 共用。日志配置位于 `backend/app/core/log.py`，通过 `LOG_LEVEL` 控制级别，默认输出到控制台。

## CRM Deal Runtime

配置 `DEEPSEEK_API_KEY` 后，可通过 `initialize_runtime` 创建固定顺序的 LangGraph：

```text
获取 CRM Context → DealAnalysis（LLM）→ NextAction（LLM）
```

```python
from sqlalchemy.orm import Session

from backend.app.agent import initialize_runtime

with Session(engine) as session:
    runtime = initialize_runtime(session)
    result = runtime.run(opportunity_id=1)
    print(result.deal_analysis)
    print(result.next_action)
```

CRM Context 由数据库中的商机、客户、负责人、近期互动和未完成任务组成；两个模型步骤分别位于 `backend/app/agent/prompts/deal_analysis.py` 与 `backend/app/agent/prompts/next_action.py`，并使用 Pydantic 结构化输出。runtime 初始化本身不会请求模型，只有调用 `run` 才会产生两次 LLM 请求。

## 验证与停止

```bash
uv pip check
cd frontend
npm run build
npm run lint
```

在项目根目录运行 `docker compose stop` 可停止基础设施并保留数据。
Git 已配置 GitHub origin，账户认证沿用本机配置。

## 数据库迁移

数据库结构由 Alembic 管理，首次初始化或更新到最新版本执行：

```bash
uv run --env-file .env alembic upgrade head
```

修改 ORM 模型后生成迁移：

```bash
uv run --env-file .env alembic revision --autogenerate -m "变更说明"
```

迁移配置位于 `alembic.ini`，脚本位于 `migrations/`。提交自动生成的迁移前需要检查 upgrade 和 downgrade 内容。
如果数据库此前已通过 `backend.app.db.init_db` 创建，并确认结构与当前 CRM V1 完全一致，应先备份并执行 `alembic stamp 20260915_0001` 交由 Alembic 接管；`stamp` 只记录版本，不执行建表。

## CRM V1 数据层

已定义 User、Company、Contact、Opportunity、Activity、Task 六个模型。
数据库关系、字段约定、建表命令与测试步骤见 [CRM V1 数据结构](docs/crm-v1.md)。
