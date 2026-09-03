<template>
  <div class="chart-card">
    <div class="chart-card-header">
      <span class="chart-card-title">锁定订单图表</span>
      <div v-if="!collapsed" class="chart-controls">
        <Select
          v-model:value="windowMs"
          class="chart-select"
          size="small"
          :options="windowOptions"
          :allow-clear="false"
        />
        <Radio.Group v-model:value="metric" size="small" option-type="button" :options="metricOptions" />
      </div>
      <Button class="collapse-btn" type="link" size="small" @click="collapsed = !collapsed">
        {{ collapsed ? '展开' : '收起' }}
      </Button>
    </div>

    <!-- 收起时 v-show 隐藏而非销毁，保住 ECharts 实例，展开后由 ResizeObserver 自动纠正尺寸 -->
    <div v-show="!collapsed" class="lock-card-body">

    <!-- 锁定订单队列统计（原左侧 VolumeTable 统计卡片，移入本模块，覆盖全部六个档位） -->
    <div v-if="statsCards.length" class="stats-panel">
      <div class="stats-panel-header">
        <span>锁定订单队列统计（{{ statsCards.length }} 个）</span>
        <Tooltip title="每个订单分别统计其前方订单、本订单和后方订单；占比以所在档位队列总量为分母，三项合计 100%">
          <QuestionCircleOutlined class="stats-help" />
        </Tooltip>
      </div>
      <div class="stats-grid">
        <div v-for="stat in statsCards" :key="stat.id" class="stats-card">
          <div class="stats-card-header">
            <span class="stats-order-id" :style="{ color: stat.color }">订单ID: {{ stat.id }}</span>
            <span class="stats-position">{{ stat.levelLabel }} · 队列第 {{ stat.queuePosition }} 位 · 队列位置 {{ stat.positionPercent }}%</span>
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

    <!-- 摘要表格：每个锁定订单一行（数据来自 B4 order_lifecycle） -->
    <div v-if="summaryRows.length" class="lock-summary">
      <table class="summary-table">
        <thead>
          <tr>
            <th>订单ID</th>
            <th>挂出时间</th>
            <th>存活时间</th>
            <th>成交/撤单时间</th>
            <th>成交占比</th>
            <th>最终结果</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in summaryRows" :key="row.id" :style="{ color: row.color }">
            <td>
              <span class="summary-id" :style="{ borderColor: row.color, color: row.color }">{{ row.id }}</span>
            </td>
            <td>{{ row.createTime }}</td>
            <td>{{ row.lifespan }}</td>
            <td>
              <template v-if="row.endTime">{{ row.endTime }}<span class="end-tag" :class="row.endKind">{{ row.endKind === 'trade' ? '成交' : '撤单' }}</span></template>
              <template v-else>--</template>
            </td>
            <td>{{ row.filledPct }}</td>
            <td>{{ row.outcome }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-show="hasPoints" ref="chartEl" class="lock-chart" />
    <div v-if="!hasPoints" class="chart-placeholder">
      {{ placeholderText }}
    </div>

    <div v-if="queueRows.length" class="queue-position-panel">
      <div class="queue-position-title">当前队列位置（队首 → 队尾）</div>
      <div v-for="row in queueRows" :key="row.id" class="queue-position-row">
        <span class="queue-order-label" :style="{ color: row.color }">订单 {{ row.id }}</span>
        <div class="queue-axis">
          <span class="queue-end-label">队首</span>
          <div v-if="row.available" class="queue-track">
            <Tooltip :title="getQueueTooltip(row)" placement="top">
              <span
                class="queue-order-marker"
                :style="{ left: row.centerPct + '%', backgroundColor: row.color }"
              />
            </Tooltip>
          </div>
          <div v-else class="queue-track queue-track-unavailable">
            <span>当前不在盘口</span>
          </div>
          <span class="queue-end-label">队尾</span>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script lang="js" setup>
  import { ref, computed, watch, nextTick } from 'vue';
  import { Select, Radio, Tooltip, Button } from 'ant-design-vue';
  import { QuestionCircleOutlined } from '@ant-design/icons-vue';
  import { useDebounceFn, useResizeObserver } from '@vueuse/core';
  import { useECharts } from '/@/hooks/web/useECharts';
  import { getOrderLifecycle, getOrderQueueSeries } from '/@/api/orderbook/orderbook';
  import { parseTimeToMs, formatMsToTimeStr } from '../composables/useSnapshotNavigation';

  const LEVEL_LABELS = {
    bid1: '买一', bid2: '买二', bid3: '买三',
    ask1: '卖一', ask2: '卖二', ask3: '卖三',
  };

  const formatVolume = (value) => {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return '0';
    return numeric.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
  };

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

  // 收起/展开：收起后只留表头一行，后续卡片自动上移
  const collapsed = ref(false);

  const SERIES_COLORS = ['#1677ff', '#722ed1', '#eb2f96', '#fa8c16', '#13c2c2', '#fa541c'];
  const SAMPLE_POINTS = 60;

  const windowMs = ref(3000);
  const windowOptions = [
    { value: 500, label: '500ms' },
    { value: 1000, label: '1s' },
    { value: 3000, label: '3s' },
    { value: 10000, label: '10s' },
    { value: 60000, label: '1min' },
  ];

  const metric = ref('ahead'); // ahead=身前量 / behind=身后量 / position=队列位置比例
  const metricOptions = [
    { value: 'ahead', label: '身前量' },
    { value: 'behind', label: '身后量' },
    { value: 'position', label: '队列位置' },
  ];

  // { [orderLocalId]: [{ t, ahead, behind }] } —— 后端按窗口均匀采样
  const tracks = ref({});
  // { [orderLocalId]: { summary, events } | null } —— B4 生命周期缓存
  const lifecycles = ref({});
  const fetching = ref(false);
  let requestSeq = 0;

  const chartEl = ref(null);
  const { setOptions, getInstance } = useECharts(chartEl, computed(() => (props.dark ? 'dark' : 'light')));

  // 卡片高度固定，但窗口/布局变化时仍需纠正画布尺寸
  useResizeObserver(
    chartEl,
    useDebounceFn(() => getInstance()?.resize(), 100),
  );

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
            const ahead = queue ? Number(queue.ahead_volume) || 0 : null;
            const behind = queue ? Number(queue.behind_volume) || 0 : null;
            const orderVolume = queue ? Number(queue.remaining_volume) || 0 : null;
            const total = ahead != null && behind != null && orderVolume != null
              ? ahead + behind + orderVolume
              : 0;
            nextTracks[id].push({
              t,
              ahead,
              behind,
              orderVolume,
              level: queue?.level || null,
              queuePosition: queue?.position ?? null,
              totalVolume: total,
              positionPct: total > 0 ? ((ahead + orderVolume / 2) / total) * 100 : null,
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

  // 当前队列位置必须和左侧 VolumeTable 使用完全相同的快照。
  // 左侧表格按 v1..vN 读取 data[0][0]，这里复用同样的读取口径，避免
  // 后端异步采样序列尚未刷新时，右侧显示上一个时刻的数据。
  const currentSnapshotReady = computed(() => {
    const snapshotTime = props.volumeData?.datetime;
    const snapshotTimeText = snapshotTime ? String(snapshotTime).split(" ").pop() : "";
    return Boolean(snapshotTimeText) && parseTimeToMs(snapshotTimeText) === currentMs.value;
  });

  const currentSnapshotPositions = computed(() => {
    if (!currentSnapshotReady.value) return {};

    const lockedSet = new Set(props.lockedIds.map((id) => String(id)));
    const positions = {};
    const levelKeys = ["bid1", "bid2", "bid3", "ask1", "ask2", "ask3"];

    levelKeys.forEach((levelKey) => {
      const row = props.volumeData?.[levelKey]?.data?.[0]?.[0];
      if (!row) return;

      const orders = [];
      for (let index = 1; row["v" + index] !== undefined; index += 1) {
        const colKey = "v" + index;
        const orderId = row[colKey + "_order_local_id"];
        const volume = row[colKey];
        if (
          orderId !== undefined &&
          orderId !== null &&
          String(orderId).trim() !== "" &&
          volume !== undefined &&
          volume !== null &&
          String(volume).trim() !== ""
        ) {
          orders.push({
            id: String(orderId),
            volume: Number.parseFloat(volume) || 0,
          });
        }
      }

      const total = orders.reduce((sum, order) => sum + order.volume, 0);
      let ahead = 0;
      orders.forEach((order, orderIndex) => {
        let behind = total - ahead - order.volume;
        if (behind < 0) behind = 0;
        if (lockedSet.has(order.id)) {
          positions[order.id] = {
            ahead,
            behind,
            orderVolume: order.volume,
            level: levelKey,
            queuePosition: orderIndex + 1,
            totalVolume: total,
            positionPct: total > 0 ? ((ahead + order.volume / 2) / total) * 100 : null,
          };
        }
        ahead += order.volume;
      });
    });

    return positions;
  });

  // 将当前快照作为序列的右端点，保证右侧曲线、右侧一维轴和左侧统计
  // 在当前时刻使用同一份订单队列数据；窗口内的历史点仍来自后端采样。
  const syncCurrentSnapshotPoint = () => {
    const now = currentMs.value;
    const currentPositions = currentSnapshotPositions.value;
    if (!now || !currentSnapshotReady.value) return;

    const nextTracks = {};
    props.lockedIds.forEach((id) => {
      const key = String(id);
      const list = (tracks.value[key] || []).filter((point) => point.t !== now);
      const current = currentPositions[key];
      list.push({
        t: now,
        ahead: current ? current.ahead : null,
        behind: current ? current.behind : null,
        orderVolume: current ? current.orderVolume : null,
        level: current ? current.level : null,
        queuePosition: current ? current.queuePosition : null,
        totalVolume: current ? current.totalVolume : null,
        positionPct: current ? current.positionPct : null,
      });
      list.sort((a, b) => a.t - b.t);
      nextTracks[key] = list;
    });
    tracks.value = nextTracks;
  };

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

  const queueRows = computed(() => {
    const now = currentMs.value;
    return props.lockedIds.map((id, i) => {
      const snapshotPoint = currentSnapshotPositions.value[String(id)];
      let point = currentSnapshotReady.value ? (snapshotPoint || null) : null;
      if (!currentSnapshotReady.value) {
        const list = tracks.value[id] || [];
        for (let index = list.length - 1; index >= 0; index--) {
          if (list[index].t <= now) {
            point = list[index];
            break;
          }
        }
      }

      const color = SERIES_COLORS[i % SERIES_COLORS.length];
      if (
        !point ||
        point.ahead == null ||
        point.behind == null ||
        point.orderVolume == null
      ) {
        return { id: String(id), color, available: false };
      }

      const ahead = Math.max(0, Number(point.ahead) || 0);
      const orderVolume = Math.max(0, Number(point.orderVolume) || 0);
      const behind = Math.max(0, Number(point.behind) || 0);
      const total = ahead + orderVolume + behind;
      if (total <= 0) return { id: String(id), color, available: false };

      const startPct = (ahead / total) * 100;
      const endPct = ((ahead + orderVolume) / total) * 100;
      return {
        id: String(id),
        color,
        available: true,
        ahead,
        orderVolume,
        behind,
        startPct,
        endPct,
        centerPct: ((startPct + endPct) / 2),
      };
    });
  });

  const getQueueTooltip = (row) =>
    '队列位置：' + row.centerPct.toFixed(2) + '%';

  // 锁定订单队列统计卡片：优先取当前快照（与左侧表格同一份数据），
  // 快照未就绪时回退到采样序列中当前时刻之前的最近一点。
  const statsCards = computed(() => {
    const now = currentMs.value;
    const percent = (value, total) => (total > 0 ? ((value / total) * 100).toFixed(2) : '0.00');

    return props.lockedIds
      .map((id, i) => {
        const key = String(id);
        let point = currentSnapshotReady.value ? currentSnapshotPositions.value[key] : null;
        if (!point) {
          const list = tracks.value[key] || [];
          for (let index = list.length - 1; index >= 0; index--) {
            if (list[index].t <= now && list[index].ahead != null) {
              point = list[index];
              break;
            }
          }
        }
        if (!point || point.ahead == null || point.orderVolume == null) return null;

        const total = point.totalVolume != null
          ? point.totalVolume
          : point.ahead + point.orderVolume + (point.behind || 0);
        if (total <= 0) return null;

        return {
          id: key,
          color: SERIES_COLORS[i % SERIES_COLORS.length],
          levelLabel: LEVEL_LABELS[point.level] || '--',
          queuePosition: point.queuePosition ?? '--',
          beforeVolume: point.ahead,
          currentVolume: point.orderVolume,
          afterVolume: point.behind || 0,
          beforePercent: percent(point.ahead, total),
          currentPercent: percent(point.orderVolume, total),
          afterPercent: percent(point.behind || 0, total),
          positionPercent: total > 0
            ? (((point.ahead + point.orderVolume / 2) / total) * 100).toFixed(2)
            : '0.00',
          totalVolume: total,
        };
      })
      .filter(Boolean);
  });

  // 摘要表格行：挂出/存活/成交或撤单时间/成交占比/最终结果（B4 order_lifecycle）
  const summaryRows = computed(() => {
    return props.lockedIds
      .map((id, i) => {
        const lc = lifecycles.value[id];
        if (!lc || !lc.summary) return null;
        const s = lc.summary;
        const lifespan =
          s.lifespan_ms >= 1000 ? `${(s.lifespan_ms / 1000).toFixed(1)}s` : `${s.lifespan_ms}ms`;
        const filledPct = s.size ? `${Math.round((s.filled_size / s.size) * 100)}%` : '--';
        const createTime = (s.create_time || '').split(' ')[1] || s.create_time || '--';

        // 成交/撤单时间按最终结果二选一：全部成交→最后成交时刻；
        // 撤单类结局→最后撤单时刻；收盘残留→无终结事件
        const events = lc.events || [];
        const outcome = s.outcome || '--';
        let endTime = null;
        let endKind = null;
        if (outcome.includes('撤单')) {
          const cancels = events.filter((ev) => ev.type === 'cancel');
          if (cancels.length) {
            endTime = (cancels[cancels.length - 1].time || '').split(' ')[1] || cancels[cancels.length - 1].time;
            endKind = 'cancel';
          }
        } else if (outcome.includes('成交') && outcome !== '收盘残留') {
          const trades = events.filter((ev) => ev.type === 'trade');
          if (trades.length) {
            endTime = (trades[trades.length - 1].time || '').split(' ')[1] || trades[trades.length - 1].time;
            endKind = 'trade';
          }
        }

        return {
          id: String(id),
          createTime,
          lifespan,
          endTime,
          endKind,
          filledPct,
          outcome,
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

  const getQueuePositionPct = (queue) => {
    if (!queue) return null;
    const ahead = Number(queue.ahead_volume) || 0;
    const behind = Number(queue.behind_volume) || 0;
    const orderVolume = Number(queue.remaining_volume) || 0;
    const total = ahead + orderVolume + behind;
    return total > 0 ? ((ahead + orderVolume / 2) / total) * 100 : null;
  };

  // 事件时刻的纵轴取值：优先用生命周期自带的队列位置，
  // 否则使用采样序列中事件之前最近的非空值。
  const eventY = (id, eventMs, queue) => {
    if (metric.value === 'position') {
      const positionPct = getQueuePositionPct(queue);
      if (positionPct != null) return positionPct;
    } else {
      const key = metric.value === 'ahead' ? 'ahead_volume' : 'behind_volume';
      if (queue && queue[key] != null) return queue[key];
    }

    const list = tracks.value[id] || [];
    const localKey = metric.value === 'position' ? 'positionPct' : metric.value;
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
        .map((p) => [p.t, metric.value === 'position' ? p.positionPct : p[metric.value]]);

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
        valueFormatter: (v) => {
          if (v == null) return '--';
          return metric.value === 'position' ? Number(v).toFixed(2) + '%' : Number(v).toLocaleString('zh-CN');
        },
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
        name: metric.value === 'position' ? '队列位置 (%)' : metric.value === 'ahead' ? '身前量（手）' : '身后量（手）',
        nameTextStyle: { fontSize: 10, color: textColor },
        min: metric.value === 'position' ? 0 : undefined,
        max: metric.value === 'position' ? 100 : undefined,
        minInterval: metric.value === 'position' ? 10 : 1,
        axisLabel: {
          fontSize: 10,
          color: textColor,
          formatter: (v) => {
            if (metric.value === 'position') return Number(v).toFixed(0) + '%';
            const numeric = Number(v);
            if (!Number.isFinite(numeric)) return '';
            if (Math.abs(numeric) >= 10000) return (numeric / 10000).toFixed(2) + '万';
            return numeric.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
          },
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
  watch([() => props.currentTime, () => props.volumeData], () => {
    syncCurrentSnapshotPoint();
    renderChart();
  });
  watch([metric, () => props.dark], renderChart);
</script>

<style lang="less" scoped>
  .chart-card {
    display: flex;
    flex-direction: column;
  }

  .chart-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 4px;
    margin-bottom: 4px;
  }

  // 收起/展开按钮：贴 header 右端，收起时整卡只剩这一行
  .collapse-btn {
    margin-left: auto;
    padding: 0 2px;
    height: 20px;
    color: #667085;
    font-size: 11px;
  }

  // 收起后主体隐藏，卡片自然收缩为一行
  .lock-card-body {
    display: contents;
  }

  .chart-card-title {
    color: #425466;
    font-size: 12px;
    font-weight: 600;
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
    grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
    gap: 6px;
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

  .lock-summary {
    margin-bottom: 6px;
    overflow-x: auto;
  }

  .summary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    font-variant-numeric: tabular-nums;

    th,
    td {
      padding: 4px 8px;
      border-bottom: 1px solid #eef2f7;
      text-align: center;
      white-space: nowrap;
    }

    th {
      color: #667085;
      font-weight: 600;
      background: #f7f9fc;
    }

    td {
      color: inherit;
    }
  }

  .summary-id {
    padding-left: 5px;
    border-left: 3px solid;
    font-weight: 600;
  }

  .end-tag {
    margin-left: 4px;
    padding: 0 4px;
    border-radius: 3px;
    font-size: 10px;

    &.trade {
      color: #c41d7f;
      background: #fff0f6;
    }

    &.cancel {
      color: #595959;
      background: #f5f5f5;
    }
  }

  .lock-chart {
    width: 100%;
    height: 200px;
  }


  .queue-position-panel {
    margin-top: 6px;
    padding-top: 6px;
    border-top: 1px solid #eef2f7;
  }

  .queue-position-title {
    margin-bottom: 6px;
    color: #667085;
    font-size: 11px;
  }

  .queue-position-row {
    display: grid;
    grid-template-columns: 82px minmax(0, 1fr);
    align-items: center;
    gap: 8px;
    min-height: 25px;
  }

  .queue-order-label {
    overflow: hidden;
    font-size: 11px;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .queue-axis {
    display: grid;
    grid-template-columns: 28px minmax(80px, 1fr) 28px;
    align-items: center;
    gap: 6px;
  }

  .queue-end-label {
    color: #98a2b3;
    font-size: 10px;
    text-align: center;
    white-space: nowrap;
  }

  .queue-track {
    position: relative;
    height: 12px;
    border: 1px solid #d0d5dd;
    border-radius: 8px;
    background: linear-gradient(90deg, #f2f4f7 0%, #e4e7ec 50%, #f2f4f7 100%);
  }

  .queue-track::before {
    position: absolute;
    top: 50%;
    right: 6px;
    left: 6px;
    height: 2px;
    background: #98a2b3;
    content: '';
    transform: translateY(-50%);
  }

  .queue-order-marker {
    position: absolute;
    z-index: 1;
    top: 50%;
    width: 12px;
    height: 12px;
    border: 2px solid #fff;
    border-radius: 50%;
    box-shadow: 0 0 0 1px currentColor, 0 1px 3px rgb(16 24 40 / 30%);
    cursor: help;
    transform: translate(-50%, -50%);
  }

  .queue-track-unavailable {
    display: flex;
    align-items: center;
    justify-content: center;
    border-style: dashed;
    color: #98a2b3;
    font-size: 10px;
  }

  @media (prefers-color-scheme: dark) {
    .queue-position-panel {
      border-top-color: #2c3342;
    }

    .queue-position-title,
    .queue-end-label {
      color: #8b95a7;
    }

    .queue-track {
      border-color: #475467;
      background: linear-gradient(90deg, #252b36 0%, #343c4a 50%, #252b36 100%);
    }

    .queue-track::before {
      background: #667085;
    }

    .queue-order-marker {
      border-color: #1b212c;
    }
  }
</style>
