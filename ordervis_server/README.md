# OrderVis Server

基于 FastAPI 的高频订单簿可视化后端，负责 TradeBook 数据初始化、盘口快照查询、订单生命周期与成交预测分析。

## 主要功能

1. **TradeBook 管理**：交易账本数据的创建、本地缓存和查询（基于 C++ 引擎 `pywangcai_orderbook`，Python 层封装）
2. **快照查询**：按时间、快照 ID、变化索引多种方式查询盘口快照，支持相邻变化点导航
3. **流量与队列序列**：Q-t 窗口流量序列（买一/卖一挂单、撤单、成交）、锁定订单身前/身后量采样序列
4. **订单分析**：订单生命周期（挂出/成交/撤单/存活时间）、真实成交结果与预测成交时间
5. **异步初始化**：TradeBook 初始化为后台任务，通过 WebSocket / HTTP 双通道汇报进度
6. **自动数据获取**：首次访问时自动通过 adata 拉取逐笔委托/逐笔成交/分钟K线数据
7. **认证**：JWT token 验证，并提供与前端 mock 对齐的登录接口
8. **统一响应格式**：业务 API 使用统一的 `{code, data, message}` 响应格式

## 环境要求

- Python 3.11
- C++ 动态库 `lib/pywangcai_orderbook`（仓库自带，不可改动）
- adata 数据源账号（逐笔数据拉取，需要有效的访问令牌；令牌失效时用环境变量中的账号兜底重新登录）

```bash
# adata 登录凭据（令牌失效时兜底使用）
export aq_username="your-username"
export aq_password="your-password"

# JWT 密钥
export JWT_SECRET_KEY="your-secret-key"
```

## 安装依赖

```bash
pip install -r requirements.txt
```

注意：运行环境需要能同时 `import adata`（数据源 SDK）与 `import lib`（C++ 引擎封装）。若二者不在同一个 Python 环境，需要在启动时把对应的 site-packages 追加进 `sys.path`（见下文"双环境启动"）。

## 启动服务器

代码内部使用包形式导入（`ordervis_server.main:app`），**必须在仓库根目录下启动**，不要在 `ordervis_server/` 目录内直接 `python main.py`。

### 开发模式（仓库根目录）

```bash
uvicorn ordervis_server.main:app --host 127.0.0.1 --port 18080 --reload
```

### 生产模式（多进程）

```bash
uvicorn ordervis_server.main:app --host 0.0.0.0 --port 18080 --workers 4
```

### 双环境启动（项目 venv + adata 环境分离时）

```bash
cd ordervis_server
setsid nohup ../.venv/bin/python -c "
import sys
sys.path.insert(0, '<仓库根目录绝对路径>')
sys.path.append('<adata 环境 site-packages 绝对路径>')
import uvicorn
uvicorn.run('ordervis_server.main:app', host='127.0.0.1', port=18080, log_level='info')
" >> log/server.log 2>&1 &
```

### 验证

- API 文档: http://127.0.0.1:18080/docs
- 交易日列表: http://127.0.0.1:18080/basic-api/tradebook/DateList
- 日志：`ordervis_server/log/server.log`

## 项目结构

```
ordervis_server/
├── main.py               # FastAPI 应用入口（注册中间件与路由）
├── start.py              # 多 worker 启动脚本
├── test.py               # API 测试脚本
├── requirements.txt      # Python 依赖
├── run.sh                # Shell 启动脚本
├── lib/                  # C++ 引擎库（pywangcai_orderbook，不可改动）
├── routers/              # API 路由
│   ├── auth.py           # 认证与登录
│   ├── tradebook.py      # TradeBook 业务接口
│   ├── progress.py       # 初始化进度（HTTP 轮询）
│   └── websocket.py      # 初始化进度（WebSocket 推送）
├── utils/                # 工具层
│   ├── tradebook.py      # TradeBook 数据类
│   ├── shared_storage.py # 本地缓存管理（12 小时未访问自动清理）
│   ├── adata_session.py  # adata 会话保活（refresh / 兜底重登）
│   ├── adata_worker.py   # 数据拉取子进程
│   ├── adata_converter.py# 数据格式转换
│   ├── progress_manager.py # 初始化任务进度管理
│   ├── response.py       # 统一响应格式
│   └── auth.py           # JWT 认证模块
├── config/               # 配置（认证参数等）
├── docs/                 # 补充文档（前端初始化对接示例）
├── test/                 # 校验脚本（orderid 对齐校验等）
├── package/              # 日志等基础设施
├── data/                 # 数据目录（CSV 缓存，不入库）
└── log/                  # 日志目录
```

## API 概览

业务路由统一挂载在 `/basic-api` 前缀下（直连后端必须带前缀，否则返回"实体或资源不存在"）；WebSocket 不带前缀。

### 认证（/basic-api）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/auth/login` | 用户登录 |
| GET | `/auth/getUserInfo` | 获取用户信息 |
| GET | `/auth/getPermCode` | 获取权限码 |
| GET | `/auth/logout` | 用户登出 |
| GET | `/auth/me` | 获取当前用户信息（需 token） |
| GET | `/auth/verify` | 验证 token 并返回用户信息 |
| POST | `/auth/verify-only` | 仅验证 token 有效性 |

### TradeBook（/basic-api/tradebook）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/DateList` | 交易日列表 |
| GET | `/symList` | 标的列表（基金仅含场内 ETF/LOF，不含场外 .OF） |
| POST | `/init_tradebook` | 异步初始化 TradeBook（返回 task_id） |
| GET | `/progress/{task_id}` | 查询初始化进度（HTTP 轮询通道） |
| GET | `/snapshots_summary` | 快照摘要（总快照数、时间范围等） |
| GET | `/snapshot_by_time` | 按时间获取快照（HH:MM:SS.fff） |
| GET | `/snapshot_by_id` | 按快照 ID 获取 |
| GET | `/snapshot_by_index` | 按变化索引获取 |
| GET | `/next_change` | 获取前后相邻的盘口变化快照 |
| GET | `/trade_flow_series` | Q-t 窗口流量序列（挂单/撤单/成交） |
| GET | `/order_lifecycle` | 订单生命周期与真实成交摘要 |
| GET | `/order_execution_estimate` | 预测成交时间与真实成交结果 |
| GET | `/order_queue_series` | 锁定订单身前/身后量采样序列 |
| GET | `/pastTimeTradeInfo` | 历史窗口订单统计 |
| GET | `/find_order` | 按时间/价格/数量/方向查找订单 |

### WebSocket

| 路径 | 说明 |
| --- | --- |
| `/ws/progress/{task_id}` | TradeBook 初始化进度实时推送 |

## 响应格式

业务 API 统一使用：

```json
{
  "code": 0,
  "data": {},
  "message": "..."
}
```

`code` 为 0 表示成功，非 0 表示失败。

## 数据与缓存

- **数据源**：首次访问某标的/日期时自动通过 adata 拉取三类数据——逐笔委托（csord）、逐笔成交（cstra）、分钟K线（cstick），缓存为 `./data/` 下的 CSV：`csord_{symbol}_{date}.csv` 等。
- **TradeBook 缓存**：每个进程维护独立内存缓存，12 小时未访问自动清理；线程安全。
- **关键口径**：快照订单的 `order_local_id` 与 CSV 逐笔委托 `orderid` 一一对应（SZ/SH 均 100% 命中）；快照内的 `order_id` 是引擎内部序号，不可用于关联。

## 测试与校验

```bash
# API 冒烟测试（需服务已启动）
python test.py

# 订单 ID 对齐校验
python test/check_alignment.py <symbol> <date>
```

## 注意事项

1. **C++ 库不可改动**：`lib/pywangcai_orderbook` 为预编译动态库，后端改动仅限 Python 层。
2. **工作目录**：必须从仓库根目录以包路径启动（`ordervis_server.main:app`）。
3. **数据目录**：确保 `./data/` 存在且有读写权限；首次拉取数据需要网络与有效的 adata 凭据。
4. **多进程缓存**：多 worker 下每个进程独立缓存，相同数据可能被重复初始化。
5. **JWT 密钥**：生产环境务必使用安全密钥。
