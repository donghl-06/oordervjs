<template>
  <Modal
    :visible="visible"
    title="选择要锁定的订单"
    width="860px"
    :confirm-loading="false"
    :ok-button-props="{ disabled: selectedKeys.length === 0 }"
    :ok-text="`锁定选中订单（${selectedKeys.length}）`"
    cancel-text="取消"
    centered
    @ok="handleConfirm"
    @cancel="handleCancel"
  >
    <!-- 按下单时间定位入口 -->
    <div class="locate-bar">
      <span class="locate-title">按下单时间定位：</span>
      <Input
        v-model:value="locateForm.order_time"
        class="locate-input time"
        placeholder="下单时间 HH:mm:ss.SSS"
        size="small"
      />
      <InputNumber
        v-model:value="locateForm.order_price"
        class="locate-input"
        :precision="pricePrecision"
        :step="priceStep"
        :controls="false"
        placeholder="价格"
        size="small"
      />
      <InputNumber
        v-model:value="locateForm.order_size"
        class="locate-input"
        :controls="false"
        placeholder="数量"
        size="small"
      />
      <RadioGroup v-model:value="locateForm.order_side" size="small">
        <Radio :value="1">买</Radio>
        <Radio :value="-1">卖</Radio>
      </RadioGroup>
      <Button type="primary" size="small" :loading="locating" @click="handleLocate">定位</Button>
    </div>

    <Table
      :data-source="candidates"
      :columns="columns"
      :pagination="false"
      :scroll="{ y: 360 }"
      size="small"
      row-key="order_local_id"
      :row-selection="rowSelection"
      :row-class-name="rowClassName"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'price'">
          {{ formatPrice(record.price) }}
        </template>
        <template v-else-if="column.dataIndex === 'create_time'">
          {{ record.create_time || '暂无数据' }}
        </template>
        <template v-else-if="column.dataIndex === 'direction'">
          <span :style="{ color: record.direction === '买' ? '#f5222d' : '#52c41a' }">
            {{ record.direction }}
          </span>
        </template>
      </template>
    </Table>
    <div class="table-footer"
      >共 {{ candidates.length }} 笔符合条件的订单，已选 {{ selectedKeys.length }} 笔</div
    >
  </Modal>
</template>

<script lang="js" setup>
  import { ref, computed, reactive } from 'vue';
  import { Modal, Table, Input, InputNumber, Radio, RadioGroup, Button } from 'ant-design-vue';
  import { findOrder } from '/@/api/orderbook/orderbook';
  import { useMessage } from '/@/hooks/web/useMessage';

  const props = defineProps({
    visible: { type: Boolean, default: false },
    // 候选订单: [{ order_local_id, order_id, volume, price(原始int), levelLabel, direction, create_time }]
    candidates: { type: Array, default: () => [] },
    sym: { type: String, default: '' },
    date: { type: String, default: '' },
    isEtf: { type: Boolean, default: false },
  });

  const emit = defineEmits(['update:visible', 'confirm']);
  const { createMessage } = useMessage();

  const selectedKeys = ref([]);
  const highlightedId = ref('');
  const locating = ref(false);
  const locateForm = reactive({
    order_time: '',
    order_price: null,
    order_size: null,
    order_side: 1,
  });

  const pricePrecision = computed(() => (props.isEtf ? 3 : 2));
  const priceStep = computed(() => (props.isEtf ? 0.001 : 0.01));

  const columns = [
    { title: '订单ID', dataIndex: 'order_local_id', width: 110 },
    { title: '档位', dataIndex: 'levelLabel', width: 60 },
    { title: '方向', dataIndex: 'direction', width: 60 },
    { title: '价格', dataIndex: 'price', width: 90 },
    { title: '剩余量', dataIndex: 'volume', width: 90 },
    { title: '下单时间', dataIndex: 'create_time', width: 180 },
  ];

  const rowSelection = computed(() => ({
    selectedRowKeys: selectedKeys.value,
    onChange: (keys) => {
      selectedKeys.value = keys;
    },
  }));

  const rowClassName = (record) =>
    String(record.order_local_id) === String(highlightedId.value) ? 'locate-hit-row' : '';

  // 后端快照价格为整数（实际价格×10000）
  const formatPrice = (price) => {
    if (price === '' || price === null || price === undefined) return '';
    return (Number(price) / 10000).toFixed(pricePrecision.value);
  };

  const handleLocate = async () => {
    if (!locateForm.order_time || !locateForm.order_price || !locateForm.order_size) {
      createMessage.warning('请填写下单时间、价格和数量');
      return;
    }
    if (!props.sym || !props.date) {
      createMessage.warning('缺少证券代码或日期');
      return;
    }
    locating.value = true;
    try {
      const res = await findOrder({
        sym: props.sym,
        date: props.date,
        order_time: locateForm.order_time,
        order_price: locateForm.order_price,
        order_size: locateForm.order_size,
        order_side: locateForm.order_side,
      });
      const result = res?.data?.result;
      if (result?.success && result.orderid != null) {
        const hitId = String(result.orderid);
        const inList = props.candidates.some((c) => String(c.order_local_id) === hitId);
        highlightedId.value = hitId;
        if (inList) {
          if (!selectedKeys.value.includes(hitId)) {
            selectedKeys.value = [...selectedKeys.value, hitId];
          }
          createMessage.success(`已定位并勾选订单 ${hitId}（下单时间 ${result.datetime}）`);
        } else {
          createMessage.warning(
            `找到订单 ${hitId}（下单时间 ${result.datetime}），但它不在当前快照六档队列中（可能已成交/撤单或不在买一~卖三）`,
          );
        }
      } else {
        createMessage.info(result?.message || '未找到匹配的订单');
      }
    } catch (e) {
      createMessage.error('定位请求失败，请检查网络连接');
    } finally {
      locating.value = false;
    }
  };

  const handleConfirm = () => {
    if (selectedKeys.value.length === 0) return;
    emit('confirm', [...selectedKeys.value]);
    resetState();
  };

  const handleCancel = () => {
    emit('update:visible', false);
    resetState();
  };

  const resetState = () => {
    emit('update:visible', false);
    selectedKeys.value = [];
    highlightedId.value = '';
  };
</script>

<style lang="less" scoped>
  .locate-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    padding: 8px 10px;
    border: 1px solid #e8eef5;
    border-radius: 5px;
    background: #f7faff;
    flex-wrap: wrap;

    .locate-title {
      color: #425466;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
    }

    .locate-input {
      width: 100px;

      &.time {
        width: 160px;
      }
    }
  }

  .table-footer {
    margin-top: 8px;
    color: #98a2b3;
    font-size: 12px;
    text-align: right;
  }

  :deep(.locate-hit-row) > td {
    background: #fff7e6 !important;
  }
</style>
