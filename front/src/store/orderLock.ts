/**
 * 订单锁定状态管理
 * 使用Pinia替代路由参数传递，更安全可靠
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export interface OrderLockData {
  orderId: string;
  sym: string;
  date: string;
  timestamp: string;
  fromGlobalSearch?: boolean;
}

export const useOrderLockStore = defineStore('orderLock', () => {
  // 订单锁定数据
  const lockData = ref<OrderLockData | null>(null);
  
  // 是否正在处理锁定
  const isProcessing = ref(false);
  
  // 处理结果
  const result = ref<{
    success: boolean;
    message: string;
    error?: any;
  } | null>(null);

  // 设置锁定数据
  const setLockData = (data: OrderLockData) => {
    lockData.value = data;
    isProcessing.value = false;
    result.value = null;
  };

  // 开始处理锁定
  const startProcessing = () => {
    isProcessing.value = true;
    result.value = null;
  };

  // 设置处理结果
  const setResult = (success: boolean, message: string, error?: any) => {
    isProcessing.value = false;
    result.value = { success, message, error };
  };

  // 清除锁定数据
  const clearLockData = () => {
    lockData.value = null;
    isProcessing.value = false;
    result.value = null;
  };

  // 检查是否有待处理的锁定数据
  const hasPendingLock = () => {
    return lockData.value !== null && !isProcessing.value;
  };

  // 计算属性：是否有锁定数据
  const hasLockData = computed(() => lockData.value !== null);

  return {
    lockData,
    isProcessing,
    result,
    hasLockData,
    setLockData,
    startProcessing,
    setResult,
    clearLockData,
    hasPendingLock
  };
});