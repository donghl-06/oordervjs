import { ref, computed, watch } from 'vue';

/**
 * useSnapshotNavigation —— 快照导航的「当前时刻」唯一状态源（第 5 步从 volumeQueue.vue 抽取）
 *
 * 设计约定（修改计划.md D6）：
 * - selectTime / changeIndex / orderIndex / snapshotId 由本 composable 持有，
 *   页面内所有导航入口（时间步进、订单步进、时间跳转、快捷键、图表点击 seek）
 *   最终都写这几个 ref，图表区（C2/C5）只读它们来跟随，保证联动不脱节。
 * - localStorage 语义沿用页面约定：volumeQueue_* 键仅会话内共享，刷新由页面 onMounted 清空。
 *
 * 纯时间工具函数同时以具名导出提供，图表组件（TradeFlowChart/LockedOrderChart）
 * 只做展示时可直接 import { parseTimeToMs } 而不必实例化 composable。
 */

// ==================== 纯时间工具（无状态，可单独导入） ====================

/** HH:mm:ss.SSS → 当日毫秒数（0 点起算），非法输入返回 0；
 *  毫秒部分超过 3 位（如 pandas 时间戳的微秒 .123456）截断处理 */
export const parseTimeToMs = (timeStr) => {
  if (!timeStr) return 0;
  const [hours, minutes, seconds] = timeStr.split(':');
  const [sec, ms] = (seconds || '0').split('.');
  const msPart = (ms || '0').slice(0, 3).padEnd(3, '0');
  return (
    parseInt(hours) * 3600000 + parseInt(minutes) * 60000 + parseInt(sec) * 1000 + parseInt(msPart)
  );
};

/** 当日毫秒数 → HH:mm:ss.SSS */
export const formatMsToTimeStr = (msValue) => {
  const h = Math.floor(msValue / 3600000);
  const m = Math.floor((msValue % 3600000) / 60000);
  const s = Math.floor((msValue % 60000) / 1000);
  const mm = msValue % 1000;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s
    .toString()
    .padStart(2, '0')}.${mm.toString().padStart(3, '0')}`;
};

/** 从完整时间戳（如 2025-08-01 09:30:00.050）提取 HH:mm:ss.SSS 时间部分 */
export const extractTimeFromTimestamp = (timestamp) => {
  if (!timestamp) return '';
  if (timestamp.match(/^\d{2}:\d{2}:\d{2}\.\d{3}$/)) {
    return timestamp;
  }
  if (timestamp.includes(' ')) {
    return timestamp.split(' ')[1] || '';
  }
  return timestamp;
};

/** 只显示时分秒（displayTime 计算属性用） */
export const formatTimeDisplay = (timestamp) => {
  if (!timestamp) return '';
  if (timestamp.includes(' ')) {
    return timestamp.split(' ')[1];
  }
  return timestamp;
};

/** HH:mm:ss.SSS / HH:mm:ss / H:mm:ss 格式校验 */
export const isValidTimeFormat = (timeStr) => {
  if (!timeStr) return false;
  const timeRegex = /^([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])(\.\d{1,3})?$/;
  return timeRegex.test(timeStr);
};

/** 交易时段边界检查（09:30:00.000 - 15:00:00.000），越界返回修正值 */
export const checkTimeBoundary = (timeStr) => {
  const minTime = '09:30:00.000';
  const maxTime = '15:00:00.000';

  if (!isValidTimeFormat(timeStr)) {
    console.warn('⚠️ 时间格式无效:', timeStr);
    return { valid: false, corrected: minTime, reason: 'format' };
  }

  const baseDate = '2000-01-01 ';
  try {
    const inputTime = new Date(baseDate + timeStr);
    const minDateTime = new Date(baseDate + minTime);
    const maxDateTime = new Date(baseDate + maxTime);

    if (isNaN(inputTime.getTime())) {
      console.warn('⚠️ 无法解析时间:', timeStr);
      return { valid: false, corrected: minTime, reason: 'parse' };
    }
    if (inputTime < minDateTime) {
      console.warn('⚠️ 时间早于开盘时间:', timeStr);
      return { valid: false, corrected: minTime, reason: 'early' };
    }
    if (inputTime > maxTime) {
      console.warn('⚠️ 时间晚于收盘时间:', timeStr);
      return { valid: false, corrected: maxTime, reason: 'late' };
    }
    return { valid: true, corrected: timeStr, reason: null };
  } catch (error) {
    console.error('❌ 时间边界检查异常:', error);
    return { valid: false, corrected: minTime, reason: 'error' };
  }
};

// ==================== 导航状态 ====================

export function useSnapshotNavigation() {
  // 从localStorage恢复orderIndex，如果没有则默认为0
  const orderIndex = ref(parseInt(localStorage.getItem('volumeQueue_orderIndex')) || 0);

  // 存储API返回的change_index
  const changeIndex = ref(0);

  // 存储API返回的snapshot_id
  const snapshotId = ref(0);

  // 从localStorage恢复selectTime，只有在来自GlobalOrderSearch的跳转时才恢复
  // 否则默认为空字符串，确保用户关闭页面重新进入时时间为空
  const isFromGlobalSearch =
    localStorage.getItem('globalSearch_orderId') && localStorage.getItem('triggerLockOrder');
  const selectTime = ref(
    isFromGlobalSearch ? localStorage.getItem('volumeQueue_timestamp') || '' : '',
  );

  // 当前时刻的毫秒数（0 点起算），供图表区做时间轴定位
  const currentTimeMs = computed(() => parseTimeToMs(selectTime.value));

  // 计算属性：用于显示的时间戳（只显示时分秒）
  const displayTime = computed({
    get: () => formatTimeDisplay(selectTime.value),
    set: (value) => {
      // 放宽：输入时不做边界检测，直接存入原始值
      selectTime.value = value;
    },
  });

  // 监听selectTime变化并持久化到localStorage
  watch(selectTime, (newValue) => {
    localStorage.setItem('volumeQueue_timestamp', newValue || '');
  });

  // 监听orderIndex变化并持久化到localStorage
  watch(orderIndex, (newValue) => {
    localStorage.setItem('volumeQueue_orderIndex', (newValue || '').toString());
  });

  return {
    // 状态
    selectTime,
    changeIndex,
    orderIndex,
    snapshotId,
    currentTimeMs,
    displayTime,
    // 工具（同名透出，页面原有调用点无需改名）
    parseTimeToMs,
    formatMsToTimeStr,
    extractTimeFromTimestamp,
    formatTimeDisplay,
    isValidTimeFormat,
    checkTimeBoundary,
  };
}
