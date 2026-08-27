# 前端进度条实现

## 核心代码

```javascript
// 1. 初始化TradeBook
async function initTradeBook(symbol, date) {
    const response = await fetch('/tradebook/init_tradebook', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: new URLSearchParams({sym: symbol, date: date})
    });
    const result = await response.json();
    return result.code === 0 ? result.data.task_id : null;
}

// 2. WebSocket监听进度
function listenProgress(taskId, onUpdate) {
    const ws = new WebSocket(`ws://localhost:18080/ws/progress/${taskId}`);
    
    ws.onmessage = (event) => {
        const {type, data, timestamp} = JSON.parse(event.data);
        
        if (type === 'task_info') {
            onUpdate(data.progress, data.message);
        } else if (type === 'task_completed') {
            onUpdate(100, '完成');
            ws.close();
        } else if (type === 'ping') {
            ws.send(JSON.stringify({type: 'pong', timestamp}));
        }
    };
    
    return ws;
}

// 3. 更新进度条
function updateProgress(progress, message) {
    document.getElementById('progress-bar').style.width = progress + '%';
    document.getElementById('progress-text').textContent = `${progress}% - ${message}`;
}
```

## 使用示例

```javascript
// 完整流程
async function startProgress() {
    const taskId = await initTradeBook('000001.SZ', '20231201');
    if (taskId) {
        listenProgress(taskId, updateProgress);
    }
}
```

## WebSocket消息格式

```json
// 服务器发送的进度消息
{
    "type": "task_info",
    "data": {
        "progress": 20,
        "message": "处理进度: 20%",
        "status": "initializing"
    }
}

// 服务器发送的心跳消息
{
    "type": "ping",
    "timestamp": 1642723200.123
}

// 客户端响应心跳
{
    "type": "pong", 
    "timestamp": 1642723200.123
}

// 任务完成消息
{
    "type": "task_completed"
}
```


