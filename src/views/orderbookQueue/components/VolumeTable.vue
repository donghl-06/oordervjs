<template>
  <div class="main-mode" style="width: 100%">
    <div class="header-container">
      <div class="header-left">
        <span :style="{ marginLeft: '5px', color: getPriceColor() }">{{ derection }}</span>
        <!-- 锁定订单统计信息 - 紧跟在derection后面 -->
        <span v-if="lockedOrderStats" class="stats-inline">
          <span class="stats-separator">|</span>
          <span class="stats-label">单前:</span>
          <span class="stats-value"
            >{{ lockedOrderStats.beforeVolume }}手 ({{ lockedOrderStats.beforePercent }}%)</span
          >
          <span class="stats-label">单后:</span>
          <span class="stats-value"
            >{{ lockedOrderStats.afterVolume }}手 ({{ lockedOrderStats.afterPercent }}%)</span
          >
          <span class="stats-total">总计: {{ lockedOrderStats.totalVolume }}手</span>
          <Tooltip
            v-if="props.showTooltip && props.derection.includes('买一价')"
            title="单前/单后展示的是第一个锁定订单之前/之后订单的手数总和，总计和百分比不包含第一个锁定订单"
          >
            <QuestionCircleOutlined style="margin-left: 4px; color: #1890ff; cursor: pointer" />
          </Tooltip>
        </span>
      </div>
      <Button v-if="shouldShowToggleButton" @click="toggleFullscreen" class="icon-button">
        <span v-if="isFullscreen">收起</span>
        <span v-else>展开</span>
      </Button>
    </div>
    <div class="table-container">
      <div class="volume-grid" :class="{ fullscreen: isFullscreen }">
        <Tooltip
          v-for="(order, index) in ordersData"
          :key="index"
          :title="getOrderTooltip(order)"
          :mouseEnterDelay="0"
          :mouseLeaveDelay="0"
          placement="top"
        >
          <div class="volume-cell" :class="{ highlighted: isHighlighted(order) }">
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
  });

  const emit = defineEmits(['update-fullscreen']);

  // 处理订单数据，固定网格布局：普通模式12列，全屏模式24列，动态行数显示所有数据
  const ordersData = computed(() => {
    const cols = props.isFullscreen ? 24 : 12; // 固定列数

    // 首先计算实际有数据的格子数量
    let actualDataCount = 0;
    if (props.data && typeof props.data === 'object') {
      const row = props.data;
      // 计算实际有数据的格子数量
      for (let i = 1; i <= 10000; i++) { // 检查足够多的格子以支持大量数据
        const colKey = `v${i}`;
        if (row[colKey] !== undefined && row[colKey] !== '') {
          actualDataCount = i;
        }
      }
    }

    // 根据数据量计算需要的行数，至少4行
    const neededRows = Math.max(4, Math.ceil(actualDataCount / cols));
    const totalCells = cols * neededRows; // 总格子数
    const result = [];

    console.log('VolumeTable接收到的props.data:', props.data);
    console.log('网格配置: 列数=', cols, '行数=', neededRows, '总格子数=', totalCells);

    // 如果没有数据或数据不是对象，填充空格子
    if (!props.data || typeof props.data !== 'object') {
      console.log('数据为空或格式不正确，填充空格子');
      for (let i = 0; i < totalCells; i++) {
        result.push({
          remaining_volume: '',
          order_id: '',
          order_local_id: '',
          direction: '',
          price: '',
          create_time: ''
        });
      }
      return result;
    }

    const row = props.data;
    console.log('处理的row数据:', row);

    // 填充固定数量的格子
    for (let i = 1; i <= totalCells; i++) {
      const colKey = `v${i}`;
      const remainingVolume = row[colKey];

      const orderData = {
        remaining_volume: remainingVolume || '',
        order_id: row[`${colKey}_order_id`] || '',
        order_local_id: row[`${colKey}_order_local_id`] || '',
        direction: row[`${colKey}_direction`] || '',
        price: row[`${colKey}_price`] || '',
        create_time: row[`${colKey}_create_time`] || ''
      };

      result.push(orderData);
    }

    console.log('最终返回的ordersData:', result, '长度:', result.length);
    return result;
  });

  // 判断订单是否应该高亮显示
  const isHighlighted = (order) => {
    if (!order || !order.order_local_id) return false;
    return props.lockedOrderIds.includes(order.order_local_id);
  };

  // 获取订单详细信息的提示文本
  const getOrderTooltip = (order) => {
    if (!order || typeof order !== 'object') return '';

    const orderId = order.order_id || '';
    const orderLocalId = order.order_local_id || '';
    const direction = order.direction || '';
    const price = order.price || '';
    const createTime = order.create_time || '';
    const remainingVolume = order.remaining_volume || '';

    if (!orderId && !orderLocalId && !price && !remainingVolume) return '';

    const tooltip = [];
    // if (remainingVolume) tooltip.push(`数量: ${remainingVolume}`);
    if (orderLocalId) tooltip.push(`订单ID: ${orderLocalId}`);
    // if (direction) tooltip.push(`方向: ${direction}`);
    if (price) tooltip.push(`价格: ${price}`);
    if (createTime) tooltip.push(`创建时间: ${createTime}`);

    return tooltip.join('\n');
  };

  // 计算属性：判断是否显示展开/收起按钮
  const shouldShowToggleButton = computed(() => {
    return props.derection.includes('买一价') || props.derection.includes('卖一价');
  });

  // 计算属性：统计锁定订单前后的remaining volume
  const lockedOrderStats = computed(() => {
    if (!props.lockedOrderIds || props.lockedOrderIds.length === 0) {
      return null;
    }

    // 获取所有有效订单（有order_local_id且不为空的订单）
    const validOrders = [];
    if (props.data && typeof props.data === 'object') {
      const row = props.data;
      for (let i = 1; i <= 10000; i++) {
        const colKey = `v${i}`;
        const orderLocalId = row[`${colKey}_order_local_id`];
        const remainingVolume = row[colKey];

        // 只统计有订单ID且有数量的有效订单
        if (orderLocalId && orderLocalId.trim() !== '' && remainingVolume && remainingVolume.toString().trim() !== '') {
          validOrders.push({
            index: i,
            order_local_id: orderLocalId,
            remaining_volume: parseFloat(remainingVolume) || 0
          });
        }
      }
    }

    if (validOrders.length === 0) {
      return null;
    }

    // 找到第一个被锁定的订单
    let firstLockedIndex = -1;
    for (let i = 0; i < validOrders.length; i++) {
      if (props.lockedOrderIds.includes(validOrders[i].order_local_id)) {
        firstLockedIndex = i;
        break;
      }
    }

    // 如果没有找到锁定的订单，返回null
    if (firstLockedIndex === -1) {
      return null;
    }

    // 计算锁定订单前后的remaining volume总和
    let beforeVolumeSum = 0;
    let afterVolumeSum = 0;

    // 统计锁定订单前面的volume
    for (let i = 0; i < firstLockedIndex; i++) {
      beforeVolumeSum += validOrders[i].remaining_volume;
    }

    // 统计锁定订单后面的volume
    for (let i = firstLockedIndex + 1; i < validOrders.length; i++) {
      afterVolumeSum += validOrders[i].remaining_volume;
    }

    // 计算总volume（不包含锁定订单本身）
    const totalVolumeExcludingLocked = beforeVolumeSum + afterVolumeSum;

    // 计算百分比（分母不包含锁定订单）
    const beforePercent = totalVolumeExcludingLocked > 0 ? ((beforeVolumeSum / totalVolumeExcludingLocked) * 100).toFixed(1) : '0.0';
    const afterPercent = totalVolumeExcludingLocked > 0 ? ((afterVolumeSum / totalVolumeExcludingLocked) * 100).toFixed(1) : '0.0';

    return {
      beforeVolume: beforeVolumeSum,
      afterVolume: afterVolumeSum,
      beforePercent,
      afterPercent,
      totalVolume: totalVolumeExcludingLocked,
      lockedOrderId: validOrders[firstLockedIndex].order_local_id
    };
  });

  const toggleFullscreen = () => {
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

    .stats-inline {
      margin-left: 10px;
      font-size: 11px;
      display: inline-flex;
      align-items: center;
      gap: 6px;

      .stats-separator {
        color: #ccc;
        margin: 0 6px;
      }

      .stats-label {
        color: #666;
        font-weight: 500;
        white-space: nowrap;
      }

      .stats-value {
        color: #1890ff;
        font-weight: 600;
        white-space: nowrap;
      }

      .stats-total {
        color: #52c41a;
        font-weight: 500;
        white-space: nowrap;
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

    .volume-grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr); /* 固定12列 */
      gap: 0px; /* 移除间隙 */
      width: 100%;
      padding: 0px; /* 移除内边距 */
    }

    .volume-grid.fullscreen {
      grid-template-columns: repeat(24, 1fr); /* 全屏时固定24列 */
    }

    .volume-cell {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 40px; /* 固定高度，确保4行正好填满容器 */
      font-size: 11px;
      border: 1px solid #d9d9d9;
      background-color: #fafafa;
      text-align: center;
      padding: 0px;
      word-break: break-all;
      overflow: hidden;
      margin: 0px; /* 确保没有外边距 */
    }

    .volume-cell.highlighted {
      background-color: #000000 !important;
      color: #ffffff !important;
    }
  }
</style>
