/**
 * 订单锁定功能相关的统一错误处理和用户反馈工具
 */

export interface OrderLockError {
  type: 'validation' | 'api' | 'network' | 'timeout' | 'notfound' | 'unknown';
  code?: string | number;
  message: string;
  details?: any;
}

export interface OrderLockResult {
  success: boolean;
  message: string;
  data?: any;
  error?: OrderLockError;
}

/**
 * 统一的错误处理函数
 */
export function handleOrderLockError(error: any, context?: string): OrderLockError {
  console.error(`[OrderLock Error] ${context || 'Unknown context'}:`, error);
  
  // 如果是标准的OrderLockError对象，直接返回
  if (error && error.type && error.message) {
    return error;
  }
  
  // 网络错误
  if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network Error') || !error?.response) {
    return {
      type: 'network',
      message: '网络连接失败，请检查网络设置',
      details: error
    };
  }
  
  // API错误（HTTP状态码错误）
  if (error?.response) {
    const status = error.response.status;
    const message = error.response.data?.message || error.message || 'API请求失败';
    
    switch (status) {
      case 400:
        return {
          type: 'validation',
          message: `参数错误: ${message}`,
          code: status,
          details: error.response.data
        };
      case 404:
        return {
          type: 'notfound',
          message: '未找到相关订单数据',
          code: status,
          details: error.response.data
        };
      case 408:
        return {
          type: 'timeout',
          message: '请求超时，请稍后重试',
          code: status,
          details: error.response.data
        };
      case 500:
        return {
          type: 'api',
          message: '服务器内部错误，请稍后重试',
          code: status,
          details: error.response.data
        };
      default:
        return {
          type: 'api',
          message: `API请求失败 (${status}): ${message}`,
          code: status,
          details: error.response.data
        };
    }
  }
  
  // 超时错误
  if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
    return {
      type: 'timeout',
      message: '请求超时，请检查网络连接或稍后重试',
      details: error
    };
  }
  
  // 未知错误
  return {
    type: 'unknown',
    message: error?.message || '发生未知错误，请稍后重试',
    details: error
  };
}

/**
 * 统一的用户反馈函数
 */
export function showOrderLockFeedback(result: OrderLockResult) {
  const message = (window as any).$message;
  
  if (!message) {
    console.warn('Message component not available');
    return;
  }
  
  if (result.success) {
    message.success(result.message || '操作成功');
  } else {
    const error = result.error;
    
    // 根据错误类型显示不同的提示
    switch (error?.type) {
      case 'validation':
        message.warning(error.message);
        break;
      case 'network':
        message.error(error.message + ' (请检查网络连接)');
        break;
      case 'timeout':
        message.warning(error.message + ' (是否需要重试？)');
        break;
      case 'notfound':
        message.info(error.message);
        break;
      case 'api':
        message.error(error.message);
        break;
      default:
        message.error(error?.message || result.message || '操作失败');
    }
  }
}

/**
 * 验证订单锁定数据的完整性
 */
export function validateOrderLockData(data: any): OrderLockResult {
  const requiredFields = ['orderId', 'sym', 'date'];
  const missingFields = requiredFields.filter(field => !data || !data[field]);
  
  if (missingFields.length > 0) {
    return {
      success: false,
      message: `缺少必要参数: ${missingFields.join(', ')}`,
      error: {
        type: 'validation',
        message: `参数验证失败，缺少: ${missingFields.join(', ')}`
      }
    };
  }
  
  // 验证订单ID格式
  if (typeof data.orderId !== 'string' && typeof data.orderId !== 'number') {
    return {
      success: false,
      message: '订单ID格式不正确',
      error: {
        type: 'validation',
        message: '订单ID必须是字符串或数字类型'
      }
    };
  }
  
  // 验证股票代码格式
  if (typeof data.sym !== 'string' || data.sym.length === 0) {
    return {
      success: false,
      message: '股票代码格式不正确',
      error: {
        type: 'validation',
        message: '股票代码必须是有效的字符串'
      }
    };
  }
  
  // 验证日期格式
  if (typeof data.date !== 'string' || data.date.length === 0) {
    return {
      success: false,
      message: '交易日期格式不正确',
      error: {
        type: 'validation',
        message: '交易日期必须是有效的字符串'
      }
    };
  }
  
  return {
    success: true,
    message: '参数验证通过'
  };
}

/**
 * 创建订单锁定的成功结果对象
 */
export function createOrderLockSuccess(message: string, data?: any): OrderLockResult {
  return {
    success: true,
    message,
    data
  };
}

/**
 * 创建订单锁定的失败结果对象
 */
export function createOrderLockError(error: OrderLockError, message?: string): OrderLockResult {
  return {
    success: false,
    message: message || error.message,
    error
  };
}

/**
 * 延迟函数，用于异步操作
 */
export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 订单锁定操作的重试机制
 */
export async function retryOrderLockOperation<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  delayMs: number = 1000
): Promise<T> {
  let lastError: any;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      console.warn(`[OrderLock] 操作失败，第 ${i + 1} 次重试:`, error);
      
      if (i < maxRetries - 1) {
        await delay(delayMs);
      }
    }
  }
  
  throw lastError;
}