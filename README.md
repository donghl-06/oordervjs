# OrderVis

面向股票和场内基金（ETF/LOF）的高频订单簿可视化回放平台。以交易日、证券代码和回放时间为入口，还原买卖盘口六档订单队列，支持时间/订单双维度步进、订单锁定追踪和成交时间预测分析。

## 仓库结构

```
project2/
├── ordervis_server/    # FastAPI 后端（端口 18080，业务路由前缀 /basic-api）
├── ordervis_client/    # Vue3 + Vite 前端（dev 端口 3100，代理到后端）
└── log/                # 运行日志
```

后端基于 C++ 订单簿引擎（`pywangcai_orderbook`，预编译动态库）做 Python 层封装；前端基于 vben 2.x 裁剪而来，核心业务页面为 `/orderbookQueue/volumeQueue`。

## 主要功能

- **盘口回放**：买一~买三、卖一~卖三六档订单队列逐快照回放，格子按订单量热力着色（买红卖绿）
- **多维导航**：时间小步/大步步进（预设 + 自定义输入）、按订单变化点步进、精确时间跳转、图表点击联动，全部入口共用同一份导航状态
- **Q-t 窗口图**：买一/卖一挂单量、新增挂单、撤单、成交的时间序列（500ms / 1s / 3s / 10s / 1min 窗口）
- **订单锁定**：点击格子、按剩余量多选、按订单 ID 三种锁定方式；锁定订单图展示身前量/身后量/队列位置趋势及生命周期摘要
- **成交时间分析**：右键订单格子查看预测成交时间（身前消耗速度 + 同价成交速度，五维度加权可信度评分）与全天真实成交结果
- **主题**：浅色/暗色切换

## 环境配置

### 后端（ordervis_server）

- Python 3.11
- 数据源 SDK `adata`（逐笔数据拉取），凭据通过环境变量提供：

```bash
export aq_username="your-adata-username"
export aq_password="your-adata-password"
export JWT_SECRET_KEY="your-secret-key"
```

```bash
python -m venv .venv
.venv/bin/pip install -r ordervis_server/requirements.txt
```

要求运行环境能同时 `import adata` 与 `import lib`（C++ 引擎封装）。两者若分属不同 Python 环境，启动时需把对应 site-packages 追加进 `sys.path`，详见 `ordervis_server/README.md`。

### 前端（ordervis_client）

- Node.js >= 14（推荐 16/18）、pnpm

```bash
cd ordervis_client
pnpm install
```

## 启动

### 1. 后端（仓库根目录，端口 18080）

```bash
.venv/bin/python -m uvicorn ordervis_server.main:app --host 127.0.0.1 --port 18080
```

验证：浏览器访问 http://127.0.0.1:18080/docs 能看到 API 文档。

### 2. 前端（端口 3100）

```bash
cd ordervis_client && pnpm dev
```

访问 http://localhost:3100 ，使用 mock 账号 `admin / 123456` 登录。

远程/后台运行时建议脱离终端启动，避免终端断开杀掉进程：

```bash
# 后端
cd ordervis_server && setsid nohup ../.venv/bin/python -m uvicorn ordervis_server.main:app --host 127.0.0.1 --port 18080 >> log/server.log 2>&1 &

# 前端
cd ordervis_client && setsid nohup pnpm dev > /tmp/vite-dev.log 2>&1 &
```

## 使用方法

1. 登录后进入「交易量队列」页面；
2. 依次选择类型（股票/基金）→ 证券代码 → 交易日期，点击「开始」；
3. 首次加载某标的/日期时后端自动拉取逐笔数据并初始化 TradeBook，进度通过 WebSocket 实时展示；已初始化过的数据直接复用；
4. 初始化完成后加载 09:30:00.000 的初始快照，之后可：
   - 用顶栏 ◀ ▶ / ◀◀ ▶▶ 按时间小步/大步移动（步长可自定义，如 `200ms`、`5s`）；
   - 按订单步长（±1/±10/±100/±500）在盘口变化点间跳转；
   - 输入 `HH:mm:ss.SSS` 点击「跳转」精确到某一时刻；
   - 点击右侧图表的时间点，主盘口同步跳转；
5. 点击订单格子锁定订单，右侧出现该订单的队列变化趋势与生命周期摘要；右键格子查看成交时间分析；
6. 顶栏「已锁定」可查看/管理全部锁定订单。

快捷键：`←/→` 小步；`Shift + ←/→` 大步；`Ctrl/Alt + ←/→` 按订单步长。

## 端口与代理

| 用途 | 地址 |
| --- | --- |
| 前端 dev server | http://localhost:3100 |
| 后端 API | http://127.0.0.1:18080/basic-api/* |
| 后端 WebSocket | ws://127.0.0.1:18080/ws/progress/{task_id} |

开发环境下前端的 `/basic-api` 与 `/ws` 由 Vite 代理到 18080（见 `ordervis_client/.env.development` 与 `vite.config.ts`）。

## 更多文档

- 后端接口与部署细节：`ordervis_server/README.md`
- 前端结构与开发说明：`ordervis_client/README.md`
