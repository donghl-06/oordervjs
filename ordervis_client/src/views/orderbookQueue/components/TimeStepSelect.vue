<template>
  <Tooltip
    :visible="invalid"
    title="输入非法：请输入 数字+单位（ms / s / min），如 200ms、5s、1min"
    placement="bottom"
    color="#ff4d4f"
  >
    <AutoComplete
      v-model:value="text"
      class="time-step-select"
      :class="{ 'input-invalid': invalid }"
      :options="autoOptions"
      :placeholder="placeholder"
      :allow-clear="false"
      :default-active-first-option="false"
      @select="handleCommit"
      @blur="handleBlur"
      @keydown.enter="handleCommit(text)"
    />
  </Tooltip>
</template>

<script lang="js" setup>
  import { ref, computed, watch } from 'vue';
  import { AutoComplete, Tooltip } from 'ant-design-vue';

  /**
   * 时间步长选择器：下拉选项 + 自由输入「数字+单位（ms/s/min）」。
   * 值以毫秒数为唯一口径（v-model:value）。
   * 输入非法时：不跳转、输入内容保持不变，旁边弹出报错提示；
   * 用户重新输入或 3 秒后提示自动消失。
   *
   * 注意（antd-vue 3.x）：
   * - Tooltip 受控属性是 visible（open 是 4.x 才有），用错会导致悬浮即弹出报错；
   * - AutoComplete 需关闭 default-active-first-option，否则回车会被内部
   *   拦截选中高亮项（如输入 1huiac 回车却提交 1s），绕过 parseText 校验。
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
  const invalid = ref(false);
  let invalidTimer = null;

  const showInvalid = () => {
    invalid.value = true;
    clearTimeout(invalidTimer);
    invalidTimer = setTimeout(() => {
      invalid.value = false;
    }, 3000);
  };

  // 用户重新输入时立即清除报错状态
  watch(text, () => {
    invalid.value = false;
    clearTimeout(invalidTimer);
  });

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
      // 非法输入：不改动生效值、不回写输入框，只弹报错提示
      showInvalid();
      return;
    }
    invalid.value = false;
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
    width: 88px;

    &.input-invalid :deep(.ant-select-selector) {
      border-color: #ff4d4f !important;
    }
  }
</style>
