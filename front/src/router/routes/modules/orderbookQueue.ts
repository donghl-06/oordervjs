import type { AppRouteModule } from '/@/router/types';

import { LAYOUT } from '/@/router/constant';
import { t } from '/@/hooks/web/useI18n';

const dataView: AppRouteModule = {
  path: '/orderbookQueue',
  name: 'orderbookQueue',
  component: LAYOUT,
  redirect: '/orderbookQueue/volumeQueue',
  meta: {
    orderNo: 10,
    icon: 'ion:git-compare-outline',
    title: '订单簿',
    ignoreAuth: true,
  },
  children: [
    {
      path: 'volumeQueue',
      name: 'volumeQueuePage',
      component: () => import('/@/views/orderbookQueue/volumeQueue.vue'),
      meta: {
        title: '交易量队列',
        icon: 'simple-icons:about-dot-me',
        ignoreAuth: true,
      },
    },
    {
      path: 'ordersDataGenerate',
      name: 'ordersDataGeneratePage',
      component: () => import('/@/views/orderbookQueue/ordersDataGenerate.vue'),
      meta: {
        title: '数据生成',
        icon: 'simple-icons:about-dot-me',
        ignoreAuth: true,
      },
    },
  ],
};

export default dataView;
