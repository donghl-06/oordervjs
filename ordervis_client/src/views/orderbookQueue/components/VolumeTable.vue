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
    <div class="table-container" :class="{ fullscreen: isFullscreen }">
      <div
        class="volume-grid"
        :class="{ fullscreen: isFullscreen }"
        :style="{ gridTemplateColumns: `repeat(${isFullscreen ? 6 : cols}, 1fr)` }"
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
            @contextmenu.prevent.stop="inspectExecution(order)"
          >
            {{ order.remaining_volume || '' }}
          </div>
        </Tooltip>
      </div>
    </div>
  </div>
</template>

<script lang="js" setup>
  import { computed } from 'vue';
  import { Button, Tooltip } from 'ant-design-vue';

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
    // 普通模式下的网格列数（全屏时固定 24 列）
    cols: {
      type: Number,
      default: 12,
    },
  });

  const emit = defineEmits(['update-fullscreen', 'toggle-lock', 'inspect-execution']);

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

  // 处理订单数据，固定网格布局：普通模式按 cols 列，全屏模式6列，动态行数显示所有数据
  const ordersData = computed(() => {
    const cols = props.isFullscreen ? 6 : props.cols; // 与模板网格列数保持一致

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

  const inspectExecution = (order) => {
    if (!order || !order.order_local_id) return;
    emit('inspect-execution', { ...order, tableKey: props.tableKey });
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
      '右键查看成交时间分析',
    ];

    return tooltip.join('\n');
  };

  // 计算属性：判断是否显示展开/收起按钮
  const shouldShowToggleButton = computed(() => {
    return props.derection.includes('买') || props.derection.includes('卖');
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
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 0;
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

    .table-container {
      flex: 1;
      margin-top: 0px;
      margin-bottom: 8px;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      background-color: #fff;
      min-height: 0; /* flex 撑满父级，由父级分配高度 */
      overflow-y: auto; /* 订单过多时显示垂直滚动条 */
      overflow-x: hidden; /* 隐藏水平滚动条 */
    }

    .volume-grid {
      display: grid;
      /* 列数由模板内联样式控制（cols prop / 全屏6列） */
      grid-auto-rows: minmax(36px, 1fr); /* 行高自适应撑满容器，订单多时保持最小行高滚动 */
      gap: 0px; /* 移除间隙 */
      width: 100%;
      min-height: 100%; /* 订单少时拉伸填满，订单多时超出滚动 */
      padding: 0px; /* 移除内边距 */
    }

    .volume-grid.fullscreen {
      grid-auto-rows: minmax(52px, 1fr);
    }

    .volume-grid.fullscreen .volume-cell {
      font-size: 16px;
    }

    .volume-cell {
      display: flex;
      align-items: center;
      justify-content: center;
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
