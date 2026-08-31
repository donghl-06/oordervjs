<template>
  <div class="chart-card">
    <div class="chart-card-header">
      <span class="chart-card-title">Q-t 窗口图</span>
      <div class="chart-controls">
        <Select
          v-model:value="windowMs"
          class="chart-select"
          size="small"
          :options="windowOptions"
          :allow-clear="false"
        />
        <Checkbox.Group
          :value="selectedMetrics"
          :options="metricOptions"
          @change="handleMetricsChange"
        />
      </div>
    </div>
    <div v-show="hasData" ref="chartEl" class="flow-chart" />
    <div v-if="!hasData" class="chart-placeholder">
      {{ placeholderText }}
    </div>
  </div>
</template>

<script lang="js" setup>
  import { ref, computed, watch, nextTick } from 'vue';
  import { Select, Checkbox } from 'ant-design-vue';
  import { useDebounceFn } from '@vueuse/core';
  import { useECharts } from '/@/hooks/web/useECharts';
  import { getTradeFlowSeries } from '/@/api/orderbook/orderbook';
  import { parseTimeToMs, formatMsToTimeStr } from '../composables/useSnapshotNavigation';

  /**
   * C2 Q-t 窗口图（修改计划.md）
   * 横轴 = 以当前时刻为右缘的滑动时间窗口（500ms/1s/3s/10s/1min 可选）
   * 纵轴 = 量，指标可选（买一/卖一 × 挂单量/撤单/成交量，最多双选叠加）
   *   挂单量 = 该时刻一档盘口累计等待量（状态量，后端锚点回溯）；
   *   撤单/成交 = 桶内新增量（差分流量）
   * 竖游标 = 当前时刻（窗口右缘）；点击图上某点 → emit('seek', 该桶时间) 主区跳转
   */
  const props = defineProps({
    sym: { type: String, default: '' },
    date: { type: String, default: '' },
    // 当前时刻 HH:mm:ss.SSS（来自 useSnapshotNavigation，窗口右缘锚点）
    currentTime: { type: String, default: '' },
    // TradeBook 数据是否已加载（未加载时不发请求）
    ready: { type: Boolean, default: false },
    dark: { type: Boolean, default: false },
  });

  const emit = defineEmits(['seek']);

  const windowMs = ref(3000);
  const windowOptions = [
    { value: 500, label: '窗口 500ms' },
    { value: 1000, label: '窗口 1s' },
    { value: 3000, label: '窗口 3s' },
    { value: 10000, label: '窗口 10s' },
    { value: 60000, label: '窗口 1min' },
  ];

  // 6 个指标，颜色与页面约定一致（买红卖绿，同侧三指标用明度区分）
  // 挂单量 = 盘口累计等待量（bid_volume/ask_volume）；撤单/成交 = 桶内新增量
  const METRIC_DEFS = [
    { key: 'bid_volume', label: '买一挂单量', color: '#f5222d' },
    { key: 'bid_cancel', label: '买一撤单', color: '#ff9c6e' },
    { key: 'bid_traded', label: '买一成交', color: '#a8071a' },
    { key: 'ask_volume', label: '卖一挂单量', color: '#52c41a' },
    { key: 'ask_cancel', label: '卖一撤单', color: '#95de64' },
    { key: 'ask_traded', label: '卖一成交', color: '#237804' },
  ];
  const metricOptions = METRIC_DEFS.map((m) => ({ value: m.key, label: m.label }));
  const selectedMetrics = ref(['bid_volume', 'ask_volume']);

  // 最多双选叠加：选中第 3 个时丢弃最早选中的
  const handleMetricsChange = (values) => {
    const next = values.length > 2 ? values.slice(values.length - 2) : values;
    selectedMetrics.value = next.length ? next : ['bid_volume'];
  };

  const chartEl = ref(null);
  const { setOptions, getInstance } = useECharts(chartEl, computed(() => (props.dark ? 'dark' : 'light')));

  const buckets = ref([]);
  const fetching = ref(false);
  let requestSeq = 0;

  const hasData = computed(() => buckets.value.length > 0);
  const placeholderText = computed(() => {
    if (!props.ready) return '选择标的与日期并点击「开始」后展示';
    if (fetching.value) return '加载中…';
    return '当前窗口内无流量数据';
  });

  const fetchSeries = async () => {
    if (!props.ready || !props.sym || !props.date || !props.currentTime) return;
    const seq = ++requestSeq;
    fetching.value = true;
    try {
      const res = await getTradeFlowSeries({
        sym: props.sym,
        date: props.date,
        time: props.currentTime,
        window_ms: windowMs.value,
        points: 60,
      });
      if (seq !== requestSeq) return; // 已有更新的请求，丢弃过期响应
      if (res.code === 0 && res.data) {
        buckets.value = res.data.series || [];
      } else {
        buckets.value = [];
      }
    } catch (e) {
      if (seq === requestSeq) buckets.value = [];
    } finally {
      if (seq === requestSeq) fetching.value = false;
    }
  };
  const debouncedFetch = useDebounceFn(fetchSeries, 120);

  // 步进/跳转/窗口切换 → 重新取窗口序列（取数本身 ms 级，120ms 防抖避免快速步进时打满请求）
  watch(
    () => [props.sym, props.date, props.currentTime, windowMs.value, props.ready],
    () => debouncedFetch(),
    { immediate: true },
  );

  // 横轴毫秒标签按窗口大小自适应精度
  const formatAxisMs = (ms) => {
    const full = formatMsToTimeStr(ms); // HH:mm:ss.SSS
    if (windowMs.value >= 60000) return full.slice(0, 8); // HH:mm:ss
    if (windowMs.value >= 3000) return full.slice(3); // mm:ss.SSS
    return full.slice(6); // ss.SSS
  };

  const buildOptions = () => {
    const list = buckets.value;
    const currentMs = parseTimeToMs(props.currentTime);
    const series = selectedMetrics.value.map((key) => {
      const def = METRIC_DEFS.find((m) => m.key === key);
      return {
        name: def.label,
        type: 'line',
        showSymbol: false,
        smooth: false,
        areaStyle: { opacity: 0.12 },
        lineStyle: { width: 1.5 },
        itemStyle: { color: def.color },
        // 桶右缘时间作为 x 值（当日毫秒数，value 轴避免 echarts time 轴时区偏移）
        // 挂单量在锚点缺失时为 null → 折线自然断开而非误导性归零
        data: list.map((b) => [parseTimeToMs(b.end), b[key] ?? null]),
      };
    });

    // 竖游标：当前时刻（窗口右缘）
    if (series.length && currentMs > 0) {
      series[0].markLine = {
        symbol: 'none',
        silent: true,
        animation: false,
        label: {
          formatter: '当前',
          position: 'insideEndTop',
          fontSize: 10,
          color: '#8b95a7',
        },
        lineStyle: { color: '#69b1ff', width: 1, type: 'dashed' },
        data: [{ xAxis: currentMs }],
      };
    }

    const textColor = props.dark ? '#8b95a7' : '#667085';
    const splitColor = props.dark ? '#2c3342' : '#eef2f7';

    return {
      animation: false,
      grid: { left: 48, right: 14, top: 26, bottom: 22 },
      legend: {
        top: 0,
        right: 0,
        itemWidth: 12,
        itemHeight: 8,
        textStyle: { fontSize: 10, color: textColor },
      },
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v) => (v == null ? '--' : Number(v).toLocaleString('zh-CN')),
        axisPointer: {
          label: { formatter: (p) => formatMsToTimeStr(p.value) },
        },
      },
      xAxis: {
        type: 'value',
        min: currentMs - windowMs.value,
        max: currentMs,
        axisLabel: { formatter: formatAxisMs, fontSize: 10, color: textColor },
        splitLine: { show: false },
        axisLine: { lineStyle: { color: splitColor } },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: {
          fontSize: 10,
          color: textColor,
          formatter: (v) => (v >= 10000 ? `${v / 10000}万` : v),
        },
        splitLine: { lineStyle: { color: splitColor } },
      },
      series,
    };
  };

  let boundInstance = null;

  // 数据 / 指标 / 主题 / 当前时刻变化 → 重绘
  watch([buckets, selectedMetrics, () => props.dark, () => props.currentTime], async () => {
    if (!hasData.value) return;
    await nextTick(); // 等 v-show 生效、容器高度恢复
    const inst = getInstance();
    inst?.resize(); // 初次 init 时容器可能 display:none（0 尺寸），此处纠正
    setOptions(buildOptions());
    // 点击图上某点 → 主区跳转到该时刻（图↔格联动）；
    // 暗色切换会 dispose 重建实例，故按实例去重绑定而非只绑一次
    if (inst && inst !== boundInstance) {
      boundInstance = inst;
      inst.on('click', (params) => {
        const ms = Array.isArray(params.value) ? params.value[0] : null;
        if (ms) emit('seek', formatMsToTimeStr(Math.round(ms)));
      });
    }
  });
</script>

<style lang="less" scoped>
  .chart-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 4px;
  }

  .chart-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;

    :deep(.ant-checkbox-group) {
      display: inline-flex;
      flex-wrap: wrap;
      gap: 2px 6px;
    }

    :deep(.ant-checkbox-wrapper) {
      font-size: 11px;
      margin-inline-end: 0;
    }
  }

  .chart-select {
    width: 96px;
  }

  .flow-chart {
    height: 200px;
    width: 100%;
  }
</style>
