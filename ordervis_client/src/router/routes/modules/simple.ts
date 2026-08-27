import type { AppRouteModule } from '/@/router/types';

import { LAYOUT } from '/@/router/constant';
import { t } from '/@/hooks/web/useI18n';

const simple: AppRouteModule = {
  path: '/simple',
  name: 'Simple',
  component: LAYOUT,
  redirect: '/simple/index',
  meta: {
    // hideChildrenInMenu: true,
    icon: 'simple-icons:about-dot-me',
    title: 'simple',
    orderNo: 100000,
    hideMenu: true,
  },
  children: [
    {
      path: 'index',
      name: 'SimplePage',
      component: () => import('/@/views/simple/index.vue'),
      meta: {
        title: '基础页面',
        icon: 'simple-icons:about-dot-me',
        hideMenu: true,
      },
    },
  ],
};

export default simple;
