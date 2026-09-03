<template>
  <div class="chart-card summary-tables-card">
    <div class="chart-card-header">
      <span class="chart-card-title">盘口统计表</span>
      <Button class="collapse-btn" type="link" size="small" @click="collapsed = !collapsed">
        {{ collapsed ? '展开' : '收起' }}
      </Button>
    </div>
    <div v-show="!collapsed" class="summary-tables">
      <!-- 表一：买卖1-3 档位总量与订单数 -->
      <div class="summary-table-block">
        <div class="block-title">六档挂单量</div>
        <table class="summary-table">
          <thead>
            <tr>
              <th>档位</th>
              <th>总量</th>
              <th>订单数</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in levelData"
              :key="item.level"
              :class="item.level.startsWith('买') ? 'bid' : 'ask'"
            >
              <td class="level-name">{{ item.level }}</td>
              <td class="num">{{ formatVol(item.volume) }}</td>
              <td class="num">{{ item.number === '' ? '--' : item.number }}单</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 表二：一档流量（新增挂单/撤单/成交 × 细分时间窗） -->
      <div class="summary-table-block flows">
        <div class="block-title">一档流量</div>
        <table class="summary-table">
          <thead>
            <tr>
              <th>指标</th>
              <th v-for="col in timeColumns" :key="col.key">{{ col.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in tradeData"
              :key="row.level"
              :class="row.level.startsWith('买') ? 'bid' : 'ask'"
            >
              <td class="level-name">{{ row.level }}</td>
              <td v-for="col in timeColumns" :key="col.key" class="num">{{ formatVol(row[col.key]) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script lang="js" setup>
  /**
   * 盘口统计表格（原左下角汇总条改造）：
   * 表一 = 买卖1-3 档总量/订单数；表二 = 一档流量指标 × 细分时间窗。
   * 时间窗由 3s/1min 细分为 10ms/50ms/500ms/3s/1min（后端 pastTimeTradeInfo 已返回全部粒度）。
   */
  import { ref } from 'vue';
  import { Button } from 'ant-design-vue';

  defineProps({
    levelData: { type: Array, default: () => [] },
    tradeData: { type: Array, default: () => [] },
  });

  // 收起/展开：收起后只留表头一行，后续卡片自动上移
  const collapsed = ref(false);

  const timeColumns = [
    { key: 'last_10ms', label: '10ms' },
    { key: 'last_50ms', label: '50ms' },
    { key: 'last_500ms', label: '500ms' },
    { key: 'last_3s', label: '3s' },
    { key: 'last_1min', label: '1min' },
  ];

  const formatVol = (v) => {
    if (v === '' || v === null || v === undefined) return '--';
    const n = Number(v);
    return Number.isFinite(n) ? n.toLocaleString('zh-CN') : String(v);
  };
</script>

<style lang="less" scoped>
  .summary-tables-card {
    min-height: 0;
  }

  .chart-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
  }

  .chart-card-title {
    color: #425466;
    font-size: 12px;
    font-weight: 600;
  }

  // 收起/展开按钮：贴 header 右端，收起时整卡只剩这一行
  .collapse-btn {
    padding: 0 2px;
    height: 20px;
    color: #667085;
    font-size: 11px;
  }

  .summary-tables {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: flex-start;
  }

  .summary-table-block {
    flex: 0 0 200px;
    min-width: 0;

    &.flows {
      flex: 1 1 380px;
    }
  }

  .block-title {
    margin-bottom: 4px;
    color: #425466;
    font-size: 12px;
    font-weight: 600;
  }

  .summary-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
    font-variant-numeric: tabular-nums;

    th,
    td {
      padding: 3px 6px;
      border-bottom: 1px solid #eef2f7;
      text-align: center;
      white-space: nowrap;
    }

    th {
      color: #667085;
      font-weight: 600;
      background: #f7f9fc;
    }

    .level-name {
      font-weight: 600;
    }

    .num {
      text-align: right;
    }

    tr.bid .level-name {
      color: #f5222d;
    }

    tr.ask .level-name {
      color: #52c41a;
    }
  }

  .ov-dark & {
    .summary-table {
      th {
        color: #8b95a7;
        background: #242a38;
      }

      th,
      td {
        border-bottom-color: #2c3342;
      }
    }

    .block-title {
      color: #8b95a7;
    }
  }
</style>
