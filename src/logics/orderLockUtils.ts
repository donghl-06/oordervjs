/**
 * 订单锁定相关工具函数
 * 提供统一的错误处理和用户反馈机制
 */

import { useMessage } from '/@/hooks/web/useMessage';

// 定义接口类型
export interface OrderLockError {
  code: string;
  message: string;
  details?: any;
}

export interface OrderLockResult {
  success: boolean;
  message: string;
  data?: any;
  error?: OrderLockError;
}

// 错误代码常量
export const ORDER_LOCK_ERRORS = {
  INVALID_ORDER_ID: 'INVALID_ORDER_ID',
  MISSING_REQUIRED_DATA: 'MISSING_REQUIRED_DATA',
  NOT_FOUND_ORDER: 'NOT_FOUND_ORDER',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const;

// 错误处理函数
export const handleOrderLockError = (error: any): OrderLockResult => {
  console.error('订单锁定错误:', error);
  
  let result: OrderLockResult = {
    success: false,
    message: '订单锁定失败',
    error: {
      code: ORDER_LOCK_ERRORS.UNKNOWN_ERROR,
      message: error?.message || '未知错误'
    }
  };

  // 根据错误类型进行分类处理
  if (error?.message?.includes('订单ID')) {
    result.error = {
      code: ORDER_LOCK_ERRORS.INVALID_ORDER_ID,
      message: '订单ID格式不正确或为空'
    };
    result.message = '请检查订单ID是否正确';
  } else if (error?.message?.includes('股票代码') || error?.message?.includes('日期')) {
    result.error = {
      code: ORDER_LOCK_ERRORS.MISSING_REQUIRED_DATA,
      message: '缺少必需的股票代码或日期信息'
    };
    result.message = '请确保股票代码和日期信息完整';
  } else if (error?.message?.includes('未找到')) {
    result.error = {
      code: ORDER_LOCK_ERRORS.NOT_FOUND_ORDER,
      message: '未找到匹配的订单数据'
    };
    result.message = '请检查订单ID是否正确或订单是否存在';
  } else if (error?.code === 'ECONNREFUSED' || error?.message?.includes('网络')) {
    result.error = {
      code: ORDER_LOCK_ERRORS.NETWORK_ERROR,
      message: '网络连接失败'
    };
    result.message = '网络连接异常，请检查网络设置';
  } else if (error?.message?.includes('timeout') || error?.code === 'ETIMEDOUT') {
    result.error = {
      code: ORDER_LOCK_ERRORS.TIMEOUT_ERROR,
      message: '请求超时'
    };
    result.message = '操作超时，请重试';
  }

  return result;
};

// 用户反馈函数
export const showOrderLockFeedback = (result: OrderLockResult): void => {
  const { createMessage } = useMessage();
  
  if (result.success) {
    createMessage.success(result.message);
  } else {
    const messageType = result.error?.code === ORDER_LOCK_ERRORS.NETWORK_ERROR || 
                       result.error?.code === ORDER_LOCK_ERRORS.TIMEOUT_ERROR 
                       ? 'warning' : 'error';
    createMessage[messageType](result.message);
  }
  
  console.log('订单锁定反馈:', result);
};

// 数据验证函数
export const validateOrderLockData = (lockData: any): OrderLockResult => {
  try {
    // 验证必要字段
    if (!lockData) {
      return {
        success: false,
        message: '锁定数据不能为空',
        error: {
          code: ORDER_LOCK_ERRORS.MISSING_REQUIRED_DATA,
          message: '锁定数据为空'
        }
      };
    }

    // 验证订单ID
    if (!lockData.orderId || typeof lockData.orderId !== 'string') {
      return {
        success: false,
        message: '订单ID无效',
        error: {
          code: ORDER_LOCK_ERRORS.INVALID_ORDER_ID,
          message: '订单ID必须是非空字符串'
        }
      };
    }

    // 验证其他必要字段
    const requiredFields = ['sym', 'date', 'timestamp'];
    for (const field of requiredFields) {
      if (!lockData[field]) {
        return {
          success: false,
          message: `缺少必要字段: ${field}`,
          error: {
            code: ORDER_LOCK_ERRORS.MISSING_REQUIRED_DATA,
            message: `缺少必要字段: ${field}`
          }
        };
      }
    }

    return {
      success: true,
      message: '数据验证通过',
      data: lockData
    };
  } catch (error) {
    return handleOrderLockError(error);
  }
};

// 包装异步操作的工具函数
export const withOrderLockErrorHandling = async <T>(
  operation: () => Promise<T>,
  context?: string
): Promise<OrderLockResult & { data?: T }> => {
  try {
    console.log(`开始执行${context || '订单锁定'}操作`);
    const data = await operation();
    
    return {
      success: true,
      message: `${context || '订单锁定'}操作成功`,
      data
    };
  } catch (error) {
    const result = handleOrderLockError(error);
    console.error(`${context || '订单锁定'}操作失败:`, error);
    return result;
  }
};

// 清理URL参数中的锁定信息
export const cleanLockParamsFromUrl = (router: any): void => {
  try {
    const currentRoute = router.currentRoute.value;
    if (currentRoute?.query) {
      const { orderId, sym, date, timestamp, lock, ...otherParams } = currentRoute.query;
      
      // 如果存在锁定参数，则清理它们
      if (orderId || sym || date || timestamp || lock) {
        router.replace({
          ...currentRoute,
          query: otherParams
        });
        console.log('已清理URL中的锁定参数');
      }
    }
  } catch (error) {
    console.warn('清理URL锁定参数失败:', error);
  }
};

// 格式化时间戳
export const formatTimestamp = (timestamp: string | number): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (error) {
    return String(timestamp);
  }
};