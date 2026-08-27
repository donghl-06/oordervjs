<script lang="ts" setup>
  import { ref } from 'vue';
  import { Card } from 'ant-design-vue';
  import { PageWrapper } from '/@/components/Page';

  const loading = ref(true);

  setTimeout(() => {
    loading.value = false;
  }, 1500);
</script>

<template>
  <PageWrapper>
    <template #headerContent> headerContent1 </template>
    <div class="lg:flex">
      <div class="lg:w-7/10 w-full !mr-4 enter-y"> left content </div>
      <div class="lg:w-3/10 w-full enter-y"> right content </div>
    </div>
  </PageWrapper>
</template>
