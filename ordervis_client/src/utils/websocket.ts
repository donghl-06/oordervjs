/**
 * WebSocket 工具类
 * 用于管理 WebSocket 连接和进度监听
 */

export interface ProgressData {
  id: string;
  symbol: string;
  date: string;
  status: 'initializing' | 'completed' | 'failed';
  progress: number;
  message: string;
  created_at: string;
  completed_at?: string;
  error?: string;
}

export interface WebSocketMessage {
  type: 'task_info' | 'task_completed' | 'progress_update' | 'error' | 'pong';
  data?: ProgressData;
  message?: string;
  timestamp?: string;
}

export class ProgressWebSocket {
  private ws: WebSocket | null = null;
  private taskId: string;
  private baseUrl: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5; // 降低重连次数
  private reconnectDelay = 1000; // 1秒
  private isManualClose = false;
  private queryRetryCount = 0; // 新增：查询重试计数
  private maxQueryRetries = 5; // 新增：最大查询重试次数
  private hasFinalStatus = false; // 新增：是否已获得最终状态

  // 事件回调
  private onProgressUpdate: ((data: ProgressData) => void) | null = null;
  private onCompleted: ((data: ProgressData) => void) | null = null;
  private onError: ((error: string) => void) | null = null;
  private onConnected: (() => void) | null = null;
  private onDisconnected: (() => void) | null = null;

  constructor(taskId: string, baseUrl?: string) {
    this.taskId = taskId;
    // NOTE: 浏览器里 ws://127.0.0.1 指向「用户电脑本机」，远程 Docker/仅转发 Vite 端口时会连错；开发环境默认同源 + Vite /ws 代理
    const fromEnv = import.meta.env.VITE_WS_URL?.trim();
    if (baseUrl !== undefined && baseUrl !== '') {
      this.baseUrl = baseUrl;
    } else if (fromEnv) {
      this.baseUrl = fromEnv;
    } else if (import.meta.env.DEV && typeof window !== 'undefined') {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      this.baseUrl = `${proto}//${window.location.host}`;
    } else {
      this.baseUrl = 'ws://127.0.0.1:18080';
    }
    console.log('🏗️ 创建WebSocket实例，taskId:', taskId, 'baseUrl:', this.baseUrl);
  }

  /**
   * 查询当前进度（仅在WebSocket超时时使用）
   */
  private async queryProgressOnTimeout(): Promise<boolean> {
    // 检查是否已获得最终状态
    if (this.hasFinalStatus) {
      console.log('🔒 已获得最终状态，停止查询');
      return true;
    }

    // 检查查询重试次数
    this.queryRetryCount++;
    if (this.queryRetryCount > this.maxQueryRetries) {
      console.error('❌ 查询重试次数已达上限，停止监听');
      this.hasFinalStatus = true;
      this.onError?.('查询重试次数过多，停止监听');
      return true;
    }

    try {
      console.log(
        `⏰ WebSocket超时，查询进度 (${this.queryRetryCount}/${this.maxQueryRetries})，taskId:`,
        this.taskId,
      );

      // 动态导入API函数
      const { getProgress } = await import('/@/api/orderbook/orderbook');
      const result = await getProgress(this.taskId);

      console.log('📊 超时查询进度结果:', result);

      if (result && result.code === 0 && result.data) {
        const progressData = result.data;
        console.log('📈 处理超时查询到的进度数据:', progressData);

        // 触发进度更新回调
        this.onProgressUpdate?.(progressData);

        // 如果任务已完成，触发完成回调并返回true表示应该退出监听循环
        if (progressData.status === 'completed') {
          console.log('✅ 任务已完成，设置最终状态');
          this.hasFinalStatus = true;
          this.onCompleted?.(progressData);
          return true; // 任务完成，应该退出监听循环
        } else if (progressData.status === 'failed') {
          console.error(
            '🚫 任务失败，设置最终状态，状态:',
            progressData.status,
            '错误信息:',
            progressData.error,
          );
          this.hasFinalStatus = true;
          this.onError?.(progressData.error || progressData.message || '任务执行失败');
          return true; // 任务失败，应该退出监听循环
        }

        // 重置查询重试计数（如果收到了有效的进度数据）
        this.queryRetryCount = 0;
      } else {
        console.warn('⚠️ 超时查询进度失败:', {
          result: result,
          taskId: this.taskId,
          queryRetryCount: this.queryRetryCount,
          timestamp: new Date().toISOString(),
        });

        // 如果查询失败可能是服务器问题，检查错误类型
        if (result && result.code !== 0) {
          console.error('❌ 服务器返回错误:', result.message);
          this.hasFinalStatus = true;
          this.onError?.(result.message || '服务器错误');
          return true; // 服务器错误，退出监听
        }
      }
      return false; // 继续监听
    } catch (error: any) {
      console.error('❌ 超时查询进度出错详情:', {
        error: error.message || error,
        stack: error.stack,
        taskId: this.taskId,
        queryRetryCount: this.queryRetryCount,
        timestamp: new Date().toISOString(),
      });

      // 检查是否是网络错误
      if (
        error.message?.includes('NetworkError') ||
        error.message?.includes('fetch') ||
        error.message?.includes('Connection refused') ||
        error.message?.includes('Failed to fetch')
      ) {
        console.error('🌐 网络连接错误，设置最终状态');
        this.hasFinalStatus = true;
        this.onError?.('网络连接错误：服务器可能已断开连接');
        return true; // 网络错误，退出监听
      }

      // 其他错误，检查重试次数
      if (this.queryRetryCount >= this.maxQueryRetries) {
        console.error('❌ 查询错误次数过多，停止监听');
        this.hasFinalStatus = true;
        this.onError?.('查询错误次数过多，停止监听');
        return true;
      }

      return false; // 其他错误继续监听
    }
  }

  /**
   * 连接 WebSocket 并开始监听进度更新
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.baseUrl}/ws/progress/${this.taskId}`;
        console.log('🔗 连接 WebSocket:', wsUrl);

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = async () => {
          console.log('✅ WebSocket 连接成功');
          this.reconnectAttempts = 0;
          this.onConnected?.();

          // 发送心跳包（类似demo中的await websocket.send(json.dumps({"type": "ping"}))）
          console.log('💓 发送初始心跳包');
          this.sendPing();

          // 延迟一下再开始监听，确保后端准备好发送消息
          setTimeout(async () => {
            console.log('🎧 延迟200ms后开始监听，确保不错过初始消息');

            // 先主动查询一次当前进度，避免错过初始状态
            console.log('🔍 连接后立即查询一次进度，确保获取当前状态');
            await this.queryProgressOnTimeout();

            this.startListening();
          }, 200);

          resolve();
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket 错误详情:', {
            error: error,
            url: wsUrl,
            taskId: this.taskId,
            readyState: this.ws?.readyState,
            timestamp: new Date().toISOString(),
          });
          reject(new Error(`WebSocket 连接失败: ${error.type || 'Unknown error'}`));
        };

        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket 连接关闭详情:', {
            code: event.code,
            reason: event.reason,
            wasClean: event.wasClean,
            taskId: this.taskId,
            isManualClose: this.isManualClose,
            hasFinalStatus: this.hasFinalStatus,
            reconnectAttempts: this.reconnectAttempts,
            timestamp: new Date().toISOString(),
          });
          this.onDisconnected?.();

          // 如果已经获得最终状态或者是手动关闭，不再重连
          if (this.hasFinalStatus || this.isManualClose) {
            console.log('🔒 已获得最终状态或手动关闭，不进行重连');
            return;
          }

          // 如果不是手动关闭且没有最终状态，尝试重连
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            console.log(`🔄 准备重连 (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
            this.reconnect();
          } else {
            console.error('❌ 已达到最大重连次数，停止重连');
            this.hasFinalStatus = true;
            this.onError?.('连接失败：已达到最大重连次数');
          }
        };
      } catch (error) {
        console.error('❌ 创建 WebSocket 连接失败:', error);
        reject(error);
      }
    });
  }

  /**
   * 开始监听WebSocket消息（参考demo_progress.py的实现）
   */
  private async startListening() {
    console.log('🎧 开始监听WebSocket消息');
    let consecutiveTimeouts = 0;

    while (
      this.ws &&
      this.ws.readyState === WebSocket.OPEN &&
      !this.isManualClose &&
      !this.hasFinalStatus
    ) {
      try {
        // 等待消息，超时时间1秒（类似demo中的timeout=1.0）
        console.log('⏳ 等待WebSocket消息，超时1秒...');
        const message = await this.waitForMessage(1000);

        if (message) {
          console.log('📨 收到WebSocket消息，开始处理');
          consecutiveTimeouts = 0; // 重置超时计数
          this.handleMessage(message);

          // 如果收到完成消息，退出监听循环
          if (message.type === 'task_completed') {
            console.log('✅ 收到task_completed消息，退出监听循环');
            break;
          }
        }
      } catch (error: any) {
        if (error.message === 'timeout') {
          consecutiveTimeouts++;
          console.log(
            `⏰ WebSocket接收超时（连续 ${consecutiveTimeouts} 次），开始查询进度`,
          );

          const shouldExit = await this.queryProgressOnTimeout();
          if (shouldExit) {
            console.log('🏁 查询显示任务已完成，退出监听循环');
            break;
          }

          // 后端当前通过 HTTP 查询返回进度，WebSocket 主要维持连接和心跳。
          // 只要 HTTP 查询仍然成功，就持续监听直到任务完成或失败。
          console.log('🔄 进度查询正常，继续监听循环');
        } else {
          console.error('❌ 监听过程中出错:', error);
          break;
        }
      }
    }

    console.log('🔚 监听循环结束，连接状态:', this.ws?.readyState);
    // 确保连接关闭
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('🔒 主动关闭WebSocket连接');
      this.ws.close();
    }
  }

  /**
   * 等待WebSocket消息（带超时）
   */
  private waitForMessage(timeout: number): Promise<WebSocketMessage | null> {
    return new Promise((resolve, reject) => {
      let isResolved = false;

      const timer = setTimeout(() => {
        if (!isResolved) {
          isResolved = true;
          console.log('⏰ WebSocket消息等待超时');
          reject(new Error('timeout'));
        }
      }, timeout);

      const handleMessage = (event: MessageEvent) => {
        if (!isResolved) {
          isResolved = true;
          clearTimeout(timer);
          this.ws?.removeEventListener('message', handleMessage);

          try {
            console.log('🔄 收到原始 WebSocket 数据:', event.data);
            const message: WebSocketMessage = JSON.parse(event.data);
            console.log('🔍 解析后的消息对象:', message);
            resolve(message);
          } catch (error) {
            console.error('❌ 解析 WebSocket 消息错误:', error, '原始数据:', event.data);
            resolve(null);
          }
        }
      };

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.addEventListener('message', handleMessage);
        console.log('👂 已添加消息监听器，等待消息...');
      } else {
        isResolved = true;
        clearTimeout(timer);
        console.warn('⚠️ WebSocket连接不可用');
        reject(new Error('WebSocket not available'));
      }
    });
  }

  /**
   * 发送心跳包
   */
  private sendPing() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const pingMessage = JSON.stringify({
        type: 'ping',
        timestamp: Date.now().toString(),
      });
      console.log('💓 发送心跳包');
      this.ws.send(pingMessage);
    }
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage) {
    console.log('🔵 收到 WebSocket 消息:', JSON.stringify(message, null, 2));

    switch (message.type) {
      case 'task_info':
        console.log('📊 处理 task_info 消息:', message.data);
        if (message.data) {
          console.log(
            '📈 更新进度 - 进度:',
            message.data.progress,
            '状态:',
            message.data.status,
            '消息:',
            message.data.message,
          );
          this.onProgressUpdate?.(message.data);

          // 检查是否为最终状态
          if (message.data.status === 'completed' || message.data.status === 'failed') {
            console.log('🔒 收到最终状态，设置标志:', message.data.status);
            this.hasFinalStatus = true;

            if (message.data.status === 'failed') {
              this.onError?.(message.data.error || message.data.message || '任务执行失败');
            }
          }
        } else {
          console.warn('⚠️ task_info 消息没有 data 字段');
        }
        break;

      case 'progress_update':
        console.log('📊 处理 progress_update 消息:', message.data);
        if (message.data) {
          console.log(
            '📈 更新进度 - 进度:',
            message.data.progress,
            '状态:',
            message.data.status,
            '消息:',
            message.data.message,
          );
          this.onProgressUpdate?.(message.data);
        } else {
          console.warn('⚠️ progress_update 消息没有 data 字段');
        }
        break;

      case 'task_completed':
        console.log('✅ 处理 task_completed 消息:', message.data);
        this.hasFinalStatus = true; // 设置最终状态标志
        if (message.data) {
          this.onCompleted?.(message.data);
          // 注意：不立即关闭连接，让监听循环自然退出
        } else {
          console.warn('⚠️ task_completed 消息没有 data 字段');
        }
        break;

      case 'error':
        console.log('❌ 处理 error 消息:', message.message);
        this.hasFinalStatus = true; // 错误也是最终状态
        this.onError?.(message.message || '未知错误');
        break;

      case 'pong':
        console.log('💓 收到心跳响应');
        // 心跳响应，保持连接
        break;

      default:
        console.warn('❓ 未知的消息类型:', message.type, '完整消息:', message);
    }
  }

  /**
   * 重连
   */
  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket 重连次数超过最大限制');
      this.onError?.('连接失败，请刷新页面重试');
      return;
    }

    this.reconnectAttempts++;
    console.log(`尝试重连 WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('重连失败:', error);
      });
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  /**
   * 手动停止监听（数据加载完成时调用）
   */
  stopListening() {
    console.log('⏹️ 手动停止WebSocket监听（数据加载完成）');
    this.isManualClose = true;
    this.hasFinalStatus = true; // 设置最终状态，避免重连

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 关闭连接
   */
  close() {
    console.log('🔒 手动关闭WebSocket连接');
    this.isManualClose = true;
    this.hasFinalStatus = true;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 重置状态（用于重新启动监听）
   */
  reset() {
    console.log('🔄 重置WebSocket状态');
    this.reconnectAttempts = 0;
    this.queryRetryCount = 0;
    this.hasFinalStatus = false;
    this.isManualClose = false;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 设置事件监听器
   */
  onProgress(callback: (data: ProgressData) => void) {
    this.onProgressUpdate = callback;
    return this;
  }

  onComplete(callback: (data: ProgressData) => void) {
    this.onCompleted = callback;
    return this;
  }

  onErrorOccurred(callback: (error: string) => void) {
    this.onError = callback;
    return this;
  }

  onConnect(callback: () => void) {
    this.onConnected = callback;
    return this;
  }

  onDisconnect(callback: () => void) {
    this.onDisconnected = callback;
    return this;
  }

  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

/**
 * 创建进度监听器的便捷函数
 */
export function createProgressListener(taskId: string): ProgressWebSocket {
  return new ProgressWebSocket(taskId);
}
