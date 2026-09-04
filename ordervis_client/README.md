# OrderVis Client

OrderVis 高频订单簿可视化平台的前端，基于 Vue 3 + Vite + TypeScript，框架底子为 vben 2.x（已裁剪为单一业务页面）。

## 功能概览

核心业务页面：`/orderbookQueue/volumeQueue`（订单簿队列回放）

- **盘口队列回放**：买一至买三、卖一至卖三共六档订单队列，格子按订单量热力着色（买红卖绿）
- **时间导航**：时间小步/大步步进（支持自定义输入如 `200ms`、`5s`、`1min`）、按订单变化点步进、时间跳转、图表点击联动
- **订单锁定**：点击格子锁定、按剩余量筛选多选锁定、按订单 ID 锁定；锁定订单图展示身前/身后量与队列位置趋势
- **Q-t 窗口图**：买一/卖一挂单量、新增挂单、撤单、成交的时间序列（500ms~1min 窗口，最多双指标）
- **成交时间分析**：右键订单格子查看预测成交时间（五维度可信度评分）与完整交易日的真实成交结果
- **主题**：浅色/暗色切换，偏好存 localStorage

快捷键：`←/→` 小步移动；`Shift + ←/→` 大步移动；`Ctrl/Alt + ←/→` 按订单步长移动。

## 技术栈

Vue 3 · Vite 2 · TypeScript · ant-design-vue 3.2 · ECharts 5 · Pinia · pnpm

## 环境准备

- Node.js >= 14（推荐 16/18）
- pnpm

## 使用

```bash
cd ordervis_client

# 安装依赖
pnpm install

# 开发（默认 http://localhost:3100）
pnpm dev

# 类型检查 / 代码检查 / 单元测试
pnpm type:check
pnpm lint:eslint
pnpm test:unit

# 生产打包（输出 dist/）
pnpm build
```

远程/后台开发时，dev server 建议脱离终端启动，避免终端断开把 vite 杀掉：

```bash
cd ordervis_client && setsid nohup pnpm dev > /tmp/vite-dev.log 2>&1 &
```

vite 重启后首次访问是冷编译，加载页停留 20~30 秒属正常现象。

## 与后端的对接

- 业务接口走 `/basic-api` 前缀，开发环境由 Vite 代理到 `http://127.0.0.1:18080/basic-api`（见 `.env.development` 的 `VITE_PROXY`）。
- WebSocket（初始化进度）经 Vite `/ws` 代理到后端 18080；`VITE_WS_URL` 留空即使用当前页面 host，远程开发时不会误连本机。
- 后端未启动时页面可打开，但点击"开始"初始化会失败。

## 登录

开发/生产构建均开启了 mock（`VITE_USE_MOCK=true`），登录接口由 `mock/sys` 提供：

- 账号：`admin` / `123456`（或 `test` / `123456`）

## 目录结构（业务相关）

```
ordervis_client/src/
├── views/orderbookQueue/
│   ├── volumeQueue.vue                  # 业务主页面（布局/数据加载/导航/锁定/联动）
│   ├── components/
│   │   ├── VolumeTable.vue              # 单档盘口队列表格
│   │   ├── LockOrderSelector.vue        # 按量锁定选择器
│   │   ├── TimeStepSelect.vue           # 时间步长选择器（预设+自定义输入）
│   │   ├── TradeFlowChart.vue           # Q-t 窗口图
│   │   ├── LockedOrderChart.vue         # 锁定订单图表
│   │   └── SummaryTables.vue            # 汇总表格
│   └── composables/useSnapshotNavigation.js  # 快照导航唯一状态源
├── api/orderbook/orderbook.ts           # 后端接口封装
├── store/orderLock.ts                   # 跨页面订单锁定请求（Pinia）
└── utils/securityType.ts                # 证券类型工具
```

其余为 vben 框架通用层（布局、路由、组件封装等）。

## License

[MIT](./LICENSE)
