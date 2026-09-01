# OrderVis Server - FastAPI 版本

基于FastAPI的交易数据可视化服务器，专注于TradeBook快照查询和数据管理。

## 主要功能

1. **TradeBook管理**: 支持交易账本数据的创建、存储和查询
2. **快照查询**: 按时间、ID、索引多种方式查询交易快照
3. **交易日管理**: 获取交易日列表和标的列表
4. **本地缓存**: 高效的本地缓存存储，支持自动过期清理
5. **自动数据获取**: 首次访问时自动从aqdatac获取交易数据
6. **第三方认证**: 支持JWT token验证，无需内置用户管理
7. **统一响应格式**: 所有API使用统一的 `{code, data, message}` 响应格式

## 快速开始

### 1. 环境配置
```bash
# 设置aqdatac认证信息
export aq_username="your-username"
export aq_password="your-password"

# 设置JWT密钥
export JWT_SECRET_KEY="your-secret-key"
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动服务器
```bash
# 开发模式
python main.py

# 生产模式（多进程）
uvicorn main:app --host 0.0.0.0 --port 18080 --workers 4
```

### 4. 访问API
- API文档: http://localhost:18080/docs
- 交易日列表: http://localhost:18080/tradebook/DateList
- 标的列表: http://localhost:18080/tradebook/symList

## 项目结构

```
ordervis_server/
├── main.py              # FastAPI主服务器
├── start.py             # 生产模式启动脚本
├── test.py              # API测试脚本
├── requirements.txt     # Python依赖
├── README.md           # 项目说明
├── run.sh              # Shell启动脚本
├── lib/                # C++库目录
├── routers/            # API路由
│   ├── auth.py         # 认证路由
│   └── tradebook.py    # TradeBook相关路由
├── utils/              # 工具函数
│   ├── auth.py         # 认证模块
│   ├── tradebook.py    # TradeBook数据类
│   ├── shared_storage.py # 共享存储管理
│   └── utils.py        # 数据库工具函数
├── config/             # 配置文件
│   └── auth_config.py  # 认证配置
├── docs/               # 文档
│   ├── AUTH_SETUP.md   # 认证设置文档
│   └── TRADEBOOK_STORAGE.md # TradeBook存储文档
├── package/            # 核心包
├── log/                # 日志文件
├── data/               # 数据目录
├── docker-compose.yml  # Docker配置
├── Dockerfile          # Docker镜像
└── .gitignore         # Git忽略文件
```

## 运行服务器

### 开发模式
```bash
python main.py
```

### 生产模式
```bash
python start.py
```

### 直接使用uvicorn
```bash
uvicorn main:app --host 0.0.0.0 --port 18080 --workers 4
```

## API响应格式

所有API接口都使用统一的响应格式：

```json
{
  "code": 0,           // 0: 成功, 1: 失败
  "data": {...},       // 响应数据
  "message": "..."     // 响应消息
}
```

### 成功响应示例
```json
{
  "code": 0,
  "data": {
    "symbol": "000001.SZ",
    "date": "2024-01-15",
    "total_snapshots": 1000
  },
  "message": "获取快照摘要成功"
}
```

### 失败响应示例
```json
{
  "code": 1,
  "data": null,
  "message": "TradeBook 000001.SZ_2024-01-15 不存在"
}
```

## 主要API端点

### 基础数据接口
- `GET /tradebook/DateList` - 获取交易日列表
  - 返回: 日期字符串列表 (YYYY-MM-DD格式)
- `GET /tradebook/symList` - 获取标的列表
  - 返回: 可回放标的对象列表（code/type）；基金仅包含有订单簿数据的场内 ETF/LOF，场外 .OF 基金不返回

### 认证相关
- `GET /auth/me` - 获取当前用户信息（需要有效token）
- `GET /auth/verify` - 验证token并返回用户信息
- `POST /auth/verify-only` - 仅验证token有效性

### TradeBook相关
- `GET /tradebook/snapshots_summary` - 获取TradeBook快照摘要
  - 参数: `sym` (交易对), `date` (日期)
  - 返回: 包含总快照数、总变化数、时间范围等摘要信息
- `GET /tradebook/snapshot_by_time` - 按时间获取快照
  - 参数: `sym` (交易对), `date` (日期), `time` (时间，格式: HH:MM:SS.fff)
  - 返回: 指定时间的快照数据
- `GET /tradebook/snapshot_by_id` - 按ID获取快照
  - 参数: `sym` (交易对), `date` (日期), `id` (快照ID)
  - 返回: 指定ID的快照数据
- `GET /tradebook/snapshot_by_index` - 按索引获取快照
  - 参数: `sym` (交易对), `date` (日期), `index` (快照索引)
  - 返回: 指定索引的快照数据
- `GET /tradebook/pastTimeTradeInfo` - 获取订单统计信息
  - 参数: `sym` (交易对), `date` (日期), `time` (时间，格式: HH:MM:SS.fff)
  - 返回: 统计信息包含过去1min,3s,500ms,50ms,10 ('买一新增撤单', '买一新增挂单', '买一新增成交', '卖一新增撤单', '卖一新增挂单', '卖一新增成交')

## 核心特性

### 统一响应格式

- **一致性**: 所有API接口使用相同的响应结构
- **错误处理**: 统一的错误码和错误消息格式
- **前端友好**: 便于前端统一处理API响应

### TradeBook本地缓存存储

系统使用高效的本地缓存来管理TradeBook对象：

- **本地缓存**: 每个进程维护独立的内存缓存，避免序列化问题
- **自动数据获取**: 首次访问时自动从aqdatac获取csord、cstra、cstick数据
- **自动过期清理**: 12小时未访问的TradeBook自动清理
- **线程安全**: 使用线程锁确保并发安全
- **访问时间追踪**: 自动更新最后访问时间

### 数据获取机制

系统支持自动从aqdatac获取交易数据：

- **csord数据**: 逐笔委托数据
- **cstra数据**: 逐笔成交数据  
- **cstick数据**: 分钟K线数据

数据文件存储在`./data/`目录下，格式为：
- `csord_{symbol}_{date}.csv`
- `cstra_{symbol}_{date}.csv`
- `cstick_{symbol}_{date}.csv`


## 认证配置

### JWT认证设置

在`config/auth_config.py`中配置认证参数：

```python
class AuthConfig:
    SECRET_KEY = "your-secret-key"
    ALGORITHM = "HS256"
    VERIFY_EXPIRATION = True
    # 其他配置...
```

### 环境变量

可以通过环境变量覆盖配置：

```bash
# JWT认证配置
export JWT_SECRET_KEY="your-secret-key"
export JWT_ALGORITHM="HS256"

# aqdatac数据源配置
export aq_username="your-aqdatac-username"
export aq_password="your-aqdatac-password"
```

## 测试

运行测试脚本验证API功能：

```bash
python test.py
```

测试脚本会验证：
- 交易日列表接口
- 标的列表接口
- TradeBook快照查询接口
- 性能测试

## 部署建议

### 开发环境
```bash
python main.py  # 单进程，热重载
```

### 生产环境
```bash
python start.py  # 多worker进程
# 或
uvicorn main:app --host 0.0.0.0 --port 18080 --workers 4
```

### Docker部署
```bash
docker-compose up -d
```

## 注意事项

1. **C++库**: 确保`lib/pywangcai_orderbook`库可正常访问
2. **数据目录**: 确保`./data/`目录存在且有读写权限
3. **认证密钥**: 生产环境务必使用安全的JWT密钥
4. **aqdatac配置**: 确保`aq_username`和`aq_password`环境变量已正确设置
5. **多进程缓存**: 每个Worker进程维护独立缓存，相同数据可能被重复创建
6. **数据文件**: 首次访问时会自动下载数据文件，请确保网络连接正常
7. **响应格式**: 所有API现在使用统一的`{code, data, message}`格式，前端需要相应更新 