// Used to configure the general configuration of some components without modifying the components

import type { SorterResult } from '../components/Table';

export default {
  // basic-table setting
  // 基础表格配置
  table: {
    // Form interface request general configuration
    // support xxx.xxx.xxx
    // 表格接口请求通用配置，可在组件prop覆盖
    // 支持 xxx.xxx.xxx格式
    fetchSetting: {
      // The field name of the current page passed to the background
      // 传给后台的当前页字段
      pageField: 'page',
      // The number field name of each page displayed in the background
      // 传给后台的每页显示多少条的字段
      sizeField: 'pageSize',
      // Field name of the form data returned by the interface
      // 接口返回表格数据的字段
      listField: 'items',
      // Total number of tables returned by the interface field name
      // 接口返回表格总数的字段
      totalField: 'total',
    },
    // Number of pages that can be selected
    // 可选的分页选项
    pageSizeOptions: ['10', '50', '80', '100'],
    // Default display quantity on one page
    //默认每页显示多少条
    defaultPageSize: 10,
    // Default Size
    // 默认大小
    defaultSize: 'middle',
    // Custom general sort function
    // 默认排序方法
    defaultSortFn: (sortInfo: SorterResult) => {
      const { field, order } = sortInfo;
      if (field && order) {
        return {
          // The sort field passed to the backend you
          // 排序字段
          field,
          // Sorting method passed to the background asc/desc
          // 排序方式 asc/desc
          order,
        };
      } else {
        return {};
      }
    },
    // Custom general filter function
    // 自定义过滤方法
    defaultFilterFn: (data: Partial<Recordable<string[]>>) => {
      return data;
    },
  },
  // scrollbar setting
  // 滚动组件配置
  scrollbar: {
    // Whether to use native scroll bar
    // After opening, the menu, modal, drawer will change the pop-up scroll bar to native
    // 是否使用原生滚动样式
    // 开启后，菜单，弹窗，抽屉会使用原生滚动条组件
    native: false,
  },
};
