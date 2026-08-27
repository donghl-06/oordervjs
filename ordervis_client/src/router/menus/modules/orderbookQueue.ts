import type { MenuModule } from '/@/router/types';
import { t } from '/@/hooks/web/useI18n';
const menu: MenuModule = {
  orderNo: 10,
  menu: {
    name: '订单簿',
    path: '/orderbookQueue',
    children: [
      {
        name: '交易量队列',
        path: 'volumeQueue',
      },
      // {
      //   name: '数据生成',
      //   path: 'ordersDataGenerate',
      // },
    ],
  },
};
export default menu;
