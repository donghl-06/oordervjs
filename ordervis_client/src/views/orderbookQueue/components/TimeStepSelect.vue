<template>
  <AutoComplete
    v-model:value="text"
    class="time-step-select"
    :options="autoOptions"
    :placeholder="placeholder"
    :allow-clear="false"
    @select="handleCommit"
    @blur="handleBlur"
    @keydown.enter="handleCommit(text)"
  />
</template>

<script lang="js" setup>
  import { ref, computed, watch } from 'vue';
  import { AutoComplete } from 'ant-design-vue';

  /**
   * 时间步长选择器：下拉选项 + 自由输入「数字+单位（ms/s/min）」。
   * 值以毫秒数为唯一口径（v-model:value），输入非法时回退到上一个有效值。
   */
  const props = defineProps({
    value: { type: Number, default: 30 },
    // 预设选项（毫秒数数组）
    presets: { type: Array, default: () => [10, 30, 100, 500] },
    placeholder: { type: String, default: '如 200ms、5s、1min' },
  });
  const emit = defineEmits(['update:value', 'change']);

  const formatMs = (ms) => {
    if (ms % 60000 === 0) return `${ms / 60000}min`;
    if (ms % 1000 === 0) return `${ms / 1000}s`;
    return `${ms}ms`;
  };

  const parseText = (raw) => {
    const match = /^\s*(\d+(?:\.\d+)?)\s*(ms|min|s)\s*$/i.exec(String(raw || ''));
    if (!match) return null;
    const amount = Number(match[1]);
    const unit = match[2].toLowerCase();
    const factor = unit === 'ms' ? 1 : unit === 's' ? 1000 : 60000;
    const ms = Math.round(amount * factor);
    // 合理范围：1ms ~ 1h
    if (!Number.isFinite(ms) || ms < 1 || ms > 3600000) return null;
    return ms;
  };

  const text = ref(formatMs(props.value));

  // 外部值变化（如初始化/重置）时同步显示文本
  watch(
    () => props.value,
    (ms) => {
      if (parseText(text.value) !== ms) text.value = formatMs(ms);
    },
  );

  const autoOptions = computed(() =>
    props.presets.map((ms) => ({ value: formatMs(ms), label: formatMs(ms) })),
  );

  const handleCommit = (raw) => {
    const ms = parseText(raw);
    if (ms === null) {
      text.value = formatMs(props.value);
      return;
    }
    text.value = formatMs(ms);
    if (ms !== props.value) {
      emit('update:value', ms);
      emit('change', ms);
    }
  };

  const handleBlur = () => handleCommit(text.value);
</script>

<style lang="less" scoped>
  .time-step-select {
    width: 96px;
  }
</style>
