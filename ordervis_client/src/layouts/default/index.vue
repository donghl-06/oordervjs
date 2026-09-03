<template>
  <Layout :class="layoutClass">
    <LayoutSideBar v-if="getShowSidebar" />
    <Layout :class="[prefixCls, `${prefixCls}__content-layout`]">
      <!-- 顶部 header 已按需求移除：订单搜索迁入业务页顶栏，登录状态迁入暗色开关右侧 -->
      <LayoutContent />
    </Layout>
  </Layout>
</template>

<script lang="ts">
  import { defineComponent, computed, unref } from 'vue';
  import { Layout } from 'ant-design-vue';
  import { createAsyncComponent } from '/@/utils/factory/createAsyncComponent';

  import LayoutSideBar from './sider/index.vue';
  import LayoutContent from './content/index.vue';

  import { useMenuSetting } from '/@/hooks/setting/useMenuSetting';
  import { useDesign } from '/@/hooks/web/useDesign';

  export default defineComponent({
    name: 'DefaultLayout',
    components: {
      Layout,
      LayoutSideBar,
      LayoutContent,
    },
    setup() {
      const { prefixCls } = useDesign('default-layout');
      const { getShowSidebar } = useMenuSetting();

      const layoutClass = computed(() => {
        return [
          prefixCls,
          {
            'ant-layout-has-sider': unref(getShowSidebar),
          },
        ];
      });

      return {
        prefixCls,
        layoutClass,
        getShowSidebar,
      };
    },
  });
</script>
<style lang="less">
  @prefix-cls: ~'@{namespace}-default-layout';

  .@{prefix-cls} {
    width: 100%;
    min-height: 100%;
    background-color: @content-bg;
    display: flex;
    flex-direction: column;

    &__content-layout {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .ant-layout {
      overflow: hidden;
    }

    .ant-layout-header {
      flex: none;
    }

    .ant-layout-content {
      flex: auto;
      min-height: 0;
    }
  }
</style>
