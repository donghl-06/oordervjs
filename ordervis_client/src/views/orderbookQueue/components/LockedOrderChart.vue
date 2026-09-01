<template>
  <div class="chart-card">
    <div class="chart-card-header">
      <span class="chart-card-title">锁定订单图表</span>
      <div class="chart-controls">
        <Select
          v-model:value="windowMs"
          class="chart-select"
          size="small"
          :options="windowOptions"
          :allow-clear="false"
        />
        <Radio.Group v-model:value="metric" size="small" option-type="button" :options="metricOptions" />
      </div>
    </div>

    <!-- 摘要行：每个锁定订单一条（数据来自 B4 order_lifecycle） -->
    <div v-if="summaryChips.length" class="lock-summary">
      <span v-for="chip in summaryChips" :key="chip.id" class="summary-chip" :style="{ borderColor: chip.color, color: chip.color }">
        <b>{{ chip.id }}</b> · 挂出 {{ chip.createTime }} · 存活 {{ chip.lifespan }} · 成交 {{ chip.filledPct }} · {{ chip.outcome }}
      </span>
    </div>

    <div v-show="hasPoints" ref="chartEl" class="lock-chart" />
    <div v-if="!hasPoints" class="chart-placeholder">
      {{ placeholderText }}
    </div>
  </div>
</template>

<script lang="js" setup>
  import { ref, computed, watch, nextTick } from 'vue';
  import { Select, Radio } from 'ant-design-vue';
  import { useDebounceFn } from '@vueuse/core';
  import { useECharts } from '/@/hooks/web/useECharts';
  import { getOrderLifecycle, getOrderQueueSeries } from '/@/api/orderbook/orderbook';
  import { parseTimeToMs, formatMsToTimeStr } from '../composables/useSnapshotNavigation';

  /**
   * C5 锁定订单身前/身后量图
   * 横轴 = 以当前时刻为右缘的滑动时间窗口（与 C2 同控件）
   * 纵轴 = 同档位身前量或身后量
   * 数据由后端按窗口均匀采样盘口快照生成，避免只记录用户浏览过的时刻。
   * 事件标记与摘要行来自 B4 order_lifecycle（每个订单只取一次，本地缓存）。
   */
  const props = defineProps({
    sym: { type: String, default: '' },
    date: { type: String, default: '' },
    // 锁定的 order_local_id 字符串数组
    lockedIds: { type: Array, default: () => [] },
    // 保留该参数以兼容父组件；序列数据由后端按时间窗口计算
    volumeData: { type: Object, default: () => ({}) },
    currentTime: { type: String, default: '' },
    dark: { type: Boolean, default: false },
  });

  const emit = defineEmits(['seek']);

  const SERIES_COLORS = ['#1677ff', '#722ed1', '#eb2f96', '#fa8c16', '#13c2c2', '#fa541c'];
  const SAMPLE_POINTS = 60;

  const windowMs = ref(3000);
  const windowOptions = [
    { value: 500, label: '窗口 500ms' },
    { value: 1000, label: '窗口 1s' },
    { value: 3000, label: '窗口 3s' },
    { value: 10000, label: '窗口 10s' },
    { value: 60000, label: '窗口 1min' },
  ];

  const metric = ref('ahead'); // ahead=身前量 / behind=身后量
  const metricOptions = [
    { value: 'ahead', label: '身前量' },
    { value: 'behind', label: '身后量' },
  ];

  // { [orderLocalId]: [{ t, ahead, behind }] } —— 后端按窗口均匀采样
  const tracks = ref({});
  // { [orderLocalId]: { summary, events } | null } —— B4 生命周期缓存
  const lifecycles = ref({});
  const fetching = ref(false);
  let requestSeq = 0;

  const chartEl = ref(null);
  const { setOptions, getInstance } = useECharts(chartEl, computed(() => (props.dark ? 'dark' : 'light')));

  // 必须定义在 immediate 监听器之前，避免组件首次挂载时访问未初始化的 const。
  const fetchLifecycle = async (id) => {
    if (!props.sym || !props.date) return;
    try {
      const res = await getOrderLifecycle({ sym: props.sym, date: props.date, order_id: id });
      lifecycles.value[id] = res.code === 0 && res.data ? res.data : null;
    } catch (e) {
      lifecycles.value[id] = null;
    }
    renderChart();
  };

  const fetchSeries = async () => {
    const seq = ++requestSeq;
    if (!props.lockedIds.length || !props.sym || !props.date || !props.currentTime) {
      tracks.value = {};
      fetching.value = false;
      return;
    }

    fetching.value = true;
    try {
      const res = await getOrderQueueSeries({
        sym: props.sym,
        date: props.date,
        time: props.currentTime,
        window_ms: windowMs.value,
        order_ids: props.lockedIds.join(','),
        points: SAMPLE_POINTS,
      });
      if (seq !== requestSeq) return;

      const nextTracks = {};
      props.lockedIds.forEach((id) => {
        nextTracks[id] = [];
      });

      if (res.code === 0 && res.data) {
        for (const point of res.data.series || []) {
          const t = parseTimeToMs(point.time);
          if (!t) continue;
          for (const id of props.lockedIds) {
            const queue = point.orders?.[String(id)];
            nextTracks[id].push({
              t,
              ahead: queue ? Number(queue.ahead_volume) || 0 : null,
              behind: queue ? Number(queue.behind_volume) || 0 : null,
            });
          }
        }
      }

      tracks.value = nextTracks;
      renderChart();
    } catch (e) {
      if (seq === requestSeq) {
        tracks.value = {};
        renderChart();
      }
    } finally {
      if (seq === requestSeq) fetching.value = false;
    }
  };
  const debouncedFetch = useDebounceFn(fetchSeries, 120);

  // 锁定集合变化：初始化新订单轨迹、清理解除锁定的订单、拉取生命周期。
  watch(
    () => [...props.lockedIds],
    (ids) => {
      const idSet = new Set(ids.map(String));
      Object.keys(tracks.value).forEach((id) => {
        if (!idSet.has(id)) delete tracks.value[id];
      });
      Object.keys(lifecycles.value).forEach((id) => {
        if (!idSet.has(id)) delete lifecycles.value[id];
      });
      ids.forEach((id) => {
        if (!(id in lifecycles.value)) fetchLifecycle(id);
      });
      debouncedFetch();
    },
    { immediate: true },
  );

  // 换标的/换日期 → 本地缓存作废，并重新请求当前窗口。
  watch(
    () => [props.sym, props.date],
    () => {
      tracks.value = {};
      lifecycles.value = {};
      props.lockedIds.forEach((id) => fetchLifecycle(id));
      debouncedFetch();
    },
  );

  const currentMs = computed(() => parseTimeToMs(props.currentTime));

  const hasPoints = computed(() =>
    props.lockedIds.some((id) =>
      (tracks.value[id] || []).some((point) => point.ahead != null || point.behind != null),
    ),
  );

  const placeholderText = computed(() => {
    if (!props.lockedIds.length) return '暂无锁定订单';
    if (fetching.value) return '正在计算锁定订单队列变化…';
    return '当前窗口内没有可见的锁定订单队列数据';
  });

  const summaryChips = computed(() => {
    return props.lockedIds
      .map((id, i) => {
        const lc = lifecycles.value[id];
        if (!lc || !lc.summary) return null;
        const s = lc.summary;
        const lifespan =
          s.lifespan_ms >= 1000 ? `${(s.lifespan_ms / 1000).toFixed(1)}s` : `${s.lifespan_ms}ms`;
        const filledPct = s.size ? `${Math.round((s.filled_size / s.size) * 100)}%` : '--';
        const createTime = (s.create_time || '').split(' ')[1] || s.create_time || '--';
        return {
          id: String(id),
          createTime,
          lifespan,
          filledPct,
          outcome: s.outcome || '--',
          color: SERIES_COLORS[i % SERIES_COLORS.length],
        };
      })
      .filter(Boolean);
  });

  const formatAxisMs = (ms) => {
    const full = formatMsToTimeStr(ms);
    if (windowMs.value >= 60000) return full.slice(0, 8);
    if (windowMs.value >= 3000) return full.slice(3);
    return full.slice(6);
  };

  // 事件时刻的纵轴取值：优先用生命周期自带的队列位置，
  // 否则使用采样序列中事件之前最近的非空值。
  const eventY = (id, eventMs, queue) => {
    const key = metric.value === 'ahead' ? 'ahead_volume' : 'behind_volume';
    if (queue && queue[key] != null) return queue[key];
    const list = tracks.value[id] || [];
    const localKey = metric.value;
    for (let i = list.length - 1; i >= 0; i--) {
      if (list[i].t <= eventMs && list[i][localKey] != null) return list[i][localKey];
    }
    return null;
  };

  const buildOptions = () => {
    const minMs = currentMs.value - windowMs.value;
    const maxMs = currentMs.value;

    const series = [];
    props.lockedIds.forEach((id, i) => {
      const color = SERIES_COLORS[i % SERIES_COLORS.length];
      const points = (tracks.value[id] || [])
        .filter((p) => p.t >= minMs && p.t <= maxMs)
        .map((p) => [p.t, p[metric.value]]);

      // 成交/撤单事件标记（B4），仅画窗口内的
      const lc = lifecycles.value[id];
      const markers = [];
      if (lc && lc.events) {
        for (const ev of lc.events) {
          if (ev.type !== 'trade' && ev.type !== 'cancel') continue;
          const evMs = parseTimeToMs((ev.time || '').split(' ')[1] || ev.time);
          if (!evMs || evMs < minMs || evMs > maxMs) continue;
          const y = eventY(id, evMs, ev.queue);
          if (y == null) continue;
          markers.push({
            coord: [evMs, y],
            value: ev.type === 'trade' ? '成' : '撤',
            itemStyle: { color: ev.type === 'trade' ? '#fa541c' : '#8c8c8c' },
          });
        }
      }

      series.push({
        name: `订单 ${id}`,
        type: 'line',
        showSymbol: false,
        smooth: false,
        lineStyle: { width: 1.5 },
        itemStyle: { color },
        data: points,
        markPoint: {
          symbol: 'circle',
          symbolSize: 16,
          label: { fontSize: 9, color: '#fff' },
          data: markers,
        },
      });
    });

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
        min: minMs,
        max: maxMs,
        axisLabel: { formatter: formatAxisMs, fontSize: 10, color: textColor },
        splitLine: { show: false },
        axisLine: { lineStyle: { color: splitColor } },
      },
      yAxis: {
        type: 'value',
        name: metric.value === 'ahead' ? '身前量' : '身后量',
        nameTextStyle: { fontSize: 10, color: textColor },
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

  const renderChart = async () => {
    if (!hasPoints.value) return;
    await nextTick();
    const inst = getInstance();
    inst?.resize();
    setOptions(buildOptions());
    // 点击图上某点 → 主区跳转到该时刻（图↔格联动）。
    if (inst && inst !== boundInstance) {
      boundInstance = inst;
      inst.on('click', (params) => {
        const ms = Array.isArray(params.value) ? params.value[0] : null;
        if (ms) emit('seek', formatMsToTimeStr(Math.round(ms)));
      });
    }
  };

  // 时间 / 窗口变化重新按窗口采样；指标和主题变化只重绘。
  watch([() => props.currentTime, windowMs], () => debouncedFetch());
  watch([metric, () => props.dark], renderChart);
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
  }

  .chart-select {
    width: 96px;
  }

  .lock-summary {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 10px;
    margin-bottom: 4px;
    font-size: 11px;
  }

  .summary-chip {
    border-left: 3px solid;
    padding-left: 5px;
    white-space: nowrap;
  }

  .lock-chart {
    height: 200px;
    width: 100%;
  }
</style>
