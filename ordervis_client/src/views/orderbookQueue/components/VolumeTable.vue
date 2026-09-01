<template>
  <div class="main-mode" style="width: 100%">
    <div class="header-container">
      <div class="header-left">
        <span :style="{ marginLeft: '5px', color: getPriceColor() }">{{ derection }}</span>
      </div>
      <Button v-if="shouldShowToggleButton" @click="toggleFullscreen" class="icon-button">
        <span v-if="isFullscreen">收起</span>
        <span v-else>展开</span>
      </Button>
    </div>
    <div v-if="lockedOrderStats.length" class="stats-panel">
      <div class="stats-panel-header">
        <span>当前价位锁定订单统计（{{ lockedOrderStats.length }} 个）</span>
        <Tooltip
          v-if="props.showTooltip && props.derection.includes('买一价')"
          title="每个订单分别统计其前方订单、本订单和后方订单；占比以当前价位队列总量为分母，三项合计 100%"
        >
          <QuestionCircleOutlined class="stats-help" />
        </Tooltip>
      </div>
      <div class="stats-grid">
        <div v-for="stat in lockedOrderStats" :key="stat.lockedOrderId" class="stats-card">
          <div class="stats-card-header">
            <span class="stats-order-id">订单ID: {{ stat.lockedOrderId }}</span>
            <span class="stats-position">队列第 {{ stat.queuePosition }} 位</span>
          </div>
          <div class="stats-metrics">
            <div class="stats-metric">
              <span>单前</span>
              <strong>{{ formatVolume(stat.beforeVolume) }}手</strong>
              <small>{{ stat.beforePercent }}%</small>
            </div>
            <div class="stats-metric current">
              <span>本单</span>
              <strong>{{ formatVolume(stat.currentVolume) }}手</strong>
              <small>{{ stat.currentPercent }}%</small>
            </div>
            <div class="stats-metric">
              <span>单后</span>
              <strong>{{ formatVolume(stat.afterVolume) }}手</strong>
              <small>{{ stat.afterPercent }}%</small>
            </div>
          </div>
          <div class="stats-total">队列总量：{{ formatVolume(stat.totalVolume) }}手</div>
        </div>
      </div>
    </div>
    <div class="table-container" :class="{ fullscreen: isFullscreen }">
      <div
        class="volume-grid"
        :class="{ fullscreen: isFullscreen }"
        :style="{ gridTemplateColumns: `repeat(${isFullscreen ? 24 : cols}, 1fr)` }"
      >
        <Tooltip
          v-for="(order, index) in ordersData"
          :key="index"
          :title="getOrderTooltip(order)"
          overlay-class-name="order-tooltip"
          :mouseEnterDelay="0"
          :mouseLeaveDelay="0"
          placement="top"
        >
          <div
            class="volume-cell"
            :class="{ highlighted: isHighlighted(order), clickable: !!order.order_local_id }"
            :style="getCellStyle(order)"
            v-on:click="toggleLock(order)"
          >
            {{ order.remaining_volume || '' }}
          </div>
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script lang="js" setup>
  import { ref, computed, watch } from 'vue';
  import { Button, Tooltip } from 'ant-design-vue';
  import { QuestionCircleOutlined } from '@ant-design/icons-vue';

  const props = defineProps({
    data: {
      type: Object,
      default: () => ({}),
    },
    derection: {
      type: String,
    },
    isFullscreen: {
      type: Boolean,
      default: false,
    },
    tableKey: {
      type: String,
      default: '',
    },
    searchValue: {
      type: String,
      default: '',
    },
    lockedOrderIds: {
      type: Array,
      default: () => [],
    },
    showTooltip: {
      type: Boolean,
      default: false,
    },
    // 普通模式下的网格列数（全屏时固定 24 列）
    cols: {
      type: Number,
      default: 12,
    },
  });

  const emit = defineEmits(['update-fullscreen', 'toggle-lock']);

  // 锁定订单 ID 集合（Set 查询 O(1)，替代数组线性 some）
  const lockedIdSet = computed(() => {
    const ids = props.lockedOrderIds || [];
    return new Set(ids.map((id) => String(id)));
  });

  // 行数据中的订单键是连续的 v1..vN（由 transformOrdersToTableData 生成），
  // 遍历到第一个不存在的键即停，替代原来的 v1..v10000 全量扫描
  const countOrderCells = (row) => {
    let count = 0;
    if (row && typeof row === 'object') {
      while (row[`v${count + 1}`] !== undefined) {
        count += 1;
      }
    }
    return count;
  };

  // 处理订单数据，固定网格布局：普通模式12列，全屏模式24列，动态行数显示所有数据
  const ordersData = computed(() => {
    const cols = props.isFullscreen ? 24 : 12; // 固定列数

    const row = props.data && typeof props.data === 'object' ? props.data : null;
    // 计算实际有数据的格子数量
    const actualDataCount = row ? countOrderCells(row) : 0;

    // 根据数据量计算需要的行数，至少4行
    const neededRows = Math.max(4, Math.ceil(actualDataCount / cols));
    const totalCells = cols * neededRows; // 总格子数
    const result = [];

    // 填充固定数量的格子
    for (let i = 1; i <= totalCells; i++) {
      const colKey = `v${i}`;

      result.push({
        remaining_volume: row?.[colKey] ?? '',
        order_id: row?.[`${colKey}_order_id`] || '',
        order_local_id: row?.[`${colKey}_order_local_id`] || '',
        direction: row?.[`${colKey}_direction`] || '',
        price: row?.[`${colKey}_price`] || '',
        create_time: row?.[`${colKey}_create_time`] || '',
      });
    }

    return result;
  });

  // 判断订单是否应该高亮显示
  const isHighlighted = (order) => {
    if (!order || !order.order_local_id) return false;
    return lockedIdSet.value.has(String(order.order_local_id));
  };

  const toggleLock = (order) => {
    if (!order || !order.order_local_id) return;
    emit('toggle-lock', order);
  };

  // D3 热力梯度：格子底色深度 ∝ 订单量 / 当前档位最大单量
  const maxCellVolume = computed(() => {
    let max = 0;
    for (const order of ordersData.value) {
      const v = Number(order.remaining_volume);
      if (Number.isFinite(v) && v > max) max = v;
    }
    return max;
  });

  const getCellStyle = (order) => {
    const v = Number(order?.remaining_volume);
    if (!Number.isFinite(v) || v <= 0 || maxCellVolume.value <= 0) return {};
    const intensity = v / maxCellVolume.value;
    const alpha = (0.06 + 0.42 * intensity).toFixed(3);
    // 买=红 卖=绿（A 股惯例，与方向标签配色一致）
    const rgb = props.derection?.includes('卖') ? '82, 196, 26' : '245, 34, 45';
    return { backgroundColor: `rgba(${rgb}, ${alpha})` };
  };

  // 获取订单详细信息的提示文本
  // create_time 形如 "2025-08-01 09:34:30.240"，日期已在顶栏选定，悬停只显示时分秒毫秒
  const getOrderTooltip = (order) => {
    if (!order || typeof order !== 'object') return '';

    const orderId = order.order_local_id || order.order_id || '';
    const createTime = (order.create_time || '').split(' ').pop() || '';
    const remainingVolume = order.remaining_volume || '';

    if (!orderId && !createTime && !remainingVolume) return '';

    const tooltip = [
      `订单ID: ${orderId || '暂无数据'}`,
      `创建时间: ${createTime || '暂无数据'}`,
    ];

    return tooltip.join('\n');
  };

  // 计算属性：判断是否显示展开/收起按钮
  const shouldShowToggleButton = computed(() => {
    return props.derection.includes('买') || props.derection.includes('卖');
  });

  const formatVolume = (value) => {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) return '0';
    return numericValue.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
  };

  const isLockedOrder = (orderId) => {
    if (orderId === undefined || orderId === null || orderId === '') return false;
    return lockedIdSet.value.has(String(orderId));
  };

  // 计算属性：为当前价位的每个锁定订单独立统计队列位置和前后数量
  const lockedOrderStats = computed(() => {
    if (!props.lockedOrderIds || props.lockedOrderIds.length === 0) {
      return [];
    }

    const validOrders = [];
    if (props.data && typeof props.data === 'object') {
      const row = props.data;
      // 订单键连续 v1..vN，遇空缺即停
      for (let i = 1; row[`v${i}`] !== undefined; i++) {
        const colKey = `v${i}`;
        const orderLocalId = row[`${colKey}_order_local_id`];
        const remainingVolume = row[colKey];

        if (
          orderLocalId !== undefined &&
          orderLocalId !== null &&
          String(orderLocalId).trim() !== '' &&
          remainingVolume !== undefined &&
          remainingVolume !== null &&
          String(remainingVolume).trim() !== ''
        ) {
          validOrders.push({
            index: i,
            order_local_id: String(orderLocalId),
            remaining_volume: parseFloat(remainingVolume) || 0,
          });
        }
      }
    }

    if (validOrders.length === 0) {
      return [];
    }

    const totalVolume = validOrders.reduce((sum, order) => sum + order.remaining_volume, 0);
    let beforeVolume = 0;
    validOrders.forEach((order) => {
      order.beforeVolume = beforeVolume;
      beforeVolume += order.remaining_volume;
    });

    let afterVolume = 0;
    for (let i = validOrders.length - 1; i >= 0; i -= 1) {
      validOrders[i].afterVolume = afterVolume;
      afterVolume += validOrders[i].remaining_volume;
    }

    const percent = (value) => (totalVolume > 0 ? ((value / totalVolume) * 100).toFixed(1) : '0.0');

    return validOrders
      .filter((order) => isLockedOrder(order.order_local_id))
      .map((order) => ({
        lockedOrderId: order.order_local_id,
        queuePosition: order.index,
        beforeVolume: order.beforeVolume,
        currentVolume: order.remaining_volume,
        afterVolume: order.afterVolume,
        beforePercent: percent(order.beforeVolume),
        currentPercent: percent(order.remaining_volume),
        afterPercent: percent(order.afterVolume),
        totalVolume,
      }));
  });

  const toggleFullscreen = () => {
    if (props.tableKey) {
      emit('update-fullscreen', props.tableKey);
      return;
    }
    if (props.derection.includes('卖')) {
      emit('update-fullscreen', 'ask');
    } else {
      emit('update-fullscreen', 'bid');
    }
  };

  // 根据买卖方向返回对应颜色
  const getPriceColor = () => {
    if (props.derection.includes('卖')) {
      return '#52c41a'; // 绿色表示卖
    } else if (props.derection.includes('买')) {
      return '#f5222d'; // 红色表示买
    }
    return '#000000'; // 默认黑色
  };
</script>

<style lang="less" scoped>
  .main-mode {
    .header-container {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 0px;
      margin-bottom: 0px;
    }

    .header-left {
      display: flex;
      align-items: center;
      flex: 1;
      flex-wrap: wrap;
    }

    // 针对 Ant Design 按钮的具体样式覆盖
    :deep(.ant-btn.icon-button) {
      margin-right: 5px; /* 距离容器右侧5px */
      cursor: pointer;
      display: inline-block; /* 确保按钮显示 */
      font-size: 12px !important; /* 缩小字体大小 */
      padding: 2px 6px !important; /* 减小内边距来降低高度 */
      height: 20px !important; /* 直接设置高度，比默认的28px小2px */
      line-height: 1 !important; /* 调整行高 */
      min-height: 20px !important; /* 确保最小高度也是26px */
    }

    // 备用选择器，确保样式生效
    .icon-button {
      margin-right: 5px; /* 距离容器右侧5px */
      // background: none;
      // border: none;
      cursor: pointer;
      display: inline-block; /* 确保按钮显示 */
    }

    .stats-panel {
      margin: 4px 0 8px;
      padding: 6px 8px;
      border: 1px solid #d9e2ec;
      border-radius: 5px;
      background: #f7faff;
    }

    .stats-panel-header {
      display: flex;
      align-items: center;
      margin-bottom: 5px;
      color: #425466;
      font-size: 11px;
      font-weight: 600;
    }

    .stats-help {
      margin-left: 5px;
      color: #1890ff;
      cursor: pointer;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 6px;
      max-height: 126px;
      overflow-y: auto;
      padding-right: 2px;
    }

    .stats-card {
      min-width: 0;
      padding: 6px 8px;
      border: 1px solid #e1e6ed;
      border-radius: 4px;
      background: #fff;
    }

    .stats-card-header,
    .stats-total {
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: #667085;
      font-size: 11px;
    }

    .stats-order-id {
      overflow: hidden;
      color: #262626;
      font-weight: 600;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .stats-position {
      flex-shrink: 0;
      margin-left: 8px;
    }

    .stats-metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 4px;
      margin: 6px 0;
    }

    .stats-metric {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 3px 2px;
      border-radius: 3px;
      background: #f5f7fa;
      color: #667085;
      font-size: 10px;

      strong {
        margin-top: 1px;
        color: #1890ff;
        font-size: 11px;
      }

      small {
        color: #98a2b3;
        font-size: 10px;
      }
    }

    .stats-metric.current {
      background: #e6f7ff;

      strong {
        color: #096dd9;
      }
    }

    .stats-total {
      justify-content: flex-end;
      color: #52c41a;
    }

    @media (max-width: 700px) {
      .stats-grid {
        grid-template-columns: minmax(0, 1fr);
      }
    }
    .table-container {
      margin-top: 0px;
      margin-bottom: 10px;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      background-color: #fff;
      min-height: 162px; /* 最少4行的高度 */
      max-height: 162px; /* 设置最大高度，超出时显示滚动条 */
      overflow-y: auto; /* 数据过多时显示垂直滚动条 */
      overflow-x: hidden; /* 隐藏水平滚动条 */
    }

    .table-container.fullscreen {
      min-height: 320px;
      max-height: calc(100vh - 260px);
    }

    .volume-grid {
      display: grid;
      /* 列数由模板内联样式控制（cols prop / 全屏24列） */
      gap: 0px; /* 移除间隙 */
      width: 100%;
      padding: 0px; /* 移除内边距 */
    }

    .volume-grid.fullscreen .volume-cell {
      height: 48px;
      font-size: 13px;
    }

    .volume-cell {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 40px; /* 固定高度，确保4行正好填满容器 */
      font-size: 11px;
      font-variant-numeric: tabular-nums; /* D2 等宽数字 */
      border: 1px solid #d9d9d9;
      background-color: #fafafa;
      text-align: center;
      padding: 0px;
      word-break: break-all;
      overflow: hidden;
      margin: 0px; /* 确保没有外边距 */
      transition: background-color 0.25s ease; /* D3 量变化时底色平滑过渡 */
      cursor: default;
    }

    .volume-cell.clickable {
      cursor: pointer;
    }

    .volume-cell.clickable:hover {
      box-shadow: inset 0 0 0 1px #1677ff;
    }

    .volume-cell.highlighted {
      background-color: #000000 !important;
      color: #ffffff !important;
    }

    // D1 暗色主题（.ov-dark 挂在页面根节点）
    .ov-dark .table-container {
      border-color: #3a3f4b;
      background-color: #1f2430;
    }

    .ov-dark .volume-cell {
      border-color: #3a3f4b;
      background-color: #242a38;
      color: #d5dbe7;
    }

    .ov-dark .volume-cell.highlighted {
      background-color: #f0c674 !important;
      color: #1f2430 !important;
    }
  }

  :deep(.order-tooltip .ant-tooltip-inner) {
    min-width: 150px;
    padding: 8px 10px;
    border: 1px solid rgba(255, 255, 255, 0.28);
    border-radius: 5px;
    background: rgba(15, 23, 42, 0.88);
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.24);
    color: #fff;
    font-size: 12px;
    line-height: 1.7;
    white-space: pre-line;
  }

  :deep(.order-tooltip .ant-tooltip-arrow-content) {
    background: rgba(15, 23, 42, 0.88);
  }
</style>
