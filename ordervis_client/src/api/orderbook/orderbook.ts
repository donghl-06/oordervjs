import { defHttp } from '/@/utils/http/axios';
import { processApiData } from '/@/utils/dataProcessor';

export async function getSymList(params: any) {
  try {
    const response = await defHttp.get({
      url: '/tradebook/symList',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching syms:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getDateList(params: any) {
  try {
    const response = await defHttp.get({
      url: '/tradebook/DateList',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching dateList:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getVolumeData(params: any) {
  try {
    const response = await defHttp.get({
      url: '/volume_queue/volumeData',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching volumeData:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getDatetimeList(params: any) {
  try {
    const response = await defHttp.get({
      url: '/volume_queue/datetimelist',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching datetimeList:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getVolumeDataByTime(params: any) {
  try {
    const response = await defHttp.get(
      {
        url: '/tradebook/snapshot_by_time',
        params: params,
      },
      {
        joinTime: false, // 禁用自动添加时间戳，避免干扰time参数
      },
    );
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching volumeDataByTime:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getLevelInfo(params: any) {
  try {
    const response = await defHttp.get({
      url: '/volume_queue/levelInfo',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching levelInfo:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getTradeInfo(params: any) {
  try {
    const response = await defHttp.get({
      url: '/volume_queue/tradeInfo',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching tradeInfo:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getSnapshotById(params: any) {
  try {
    const response = await defHttp.get({
      url: '/tradebook/snapshot_by_id',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching snapshot by id:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getSnapshotByIndex(params: any) {
  try {
    const response = await defHttp.get({
      url: '/tradebook/snapshot_by_index',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching snapshot by index:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getSnapshotByTime(params: any) {
  try {
    const response = await defHttp.get(
      {
        url: '/tradebook/snapshot_by_time',
        params: params,
      },
      {
        joinTime: false, // 禁用自动添加时间戳，避免干扰time参数
      },
    );
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching snapshot by time:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getPastTimeTradeInfo(params: any) {
  try {
    const response = await defHttp.get(
      {
        url: '/tradebook/pastTimeTradeInfo',
        params: params,
      },
      {
        joinTime: false, // 禁用自动添加时间戳，避免干扰time参数
      },
    );
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching past time trade info:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function initTradeBook(params: any) {
  try {
    const response = await defHttp.post(
      {
        url: '/tradebook/init_tradebook',
        params: params,
      },
      {
        joinParamsToUrl: true, // 将params作为查询参数添加到URL中
      },
    );
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error initializing tradebook:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getProgress(taskId: string) {
  try {
    const response = await defHttp.get({
      url: `/progress/${taskId}`,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error fetching progress:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function checkServerStatus() {
  try {
    // 使用现有的symList端点作为健康检查
    const response = await defHttp.get({
      url: '/tradebook/symList',
    });
    return processApiData(response.data);
  } catch (error) {
    console.error('Server health check failed:', error);
    throw error;
  }
}

export interface FindOrderParams {
  sym: string;
  date: string;
  order_time: string;
  order_price: number;
  order_size: number;
  order_side: number;
  tolerance_ms?: number;
}

export async function findOrder(params: FindOrderParams) {
  try {
    const response = await defHttp.get({
      url: '/tradebook/find_order',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    console.error('Error finding order:', error);
    throw error;
  }
}

/**
 * 获取相邻变化快照（A2）：指定时间之后(direction=1)或之前(-1)第一个有变化的快照
 * 替代 moveTimes 的串行轮询
 */
export async function getNextChange(params: {
  sym: string;
  date: string;
  time: string;
  direction?: number;
}) {
  try {
    const response = await defHttp.get(
      {
        url: '/tradebook/next_change',
        params: params,
      },
      {
        joinTime: false,
      },
    );
    return processApiData(response.data);
  } catch (error) {
    console.error('Error fetching next change:', error);
    throw error;
  }
}

/**
 * 获取时间窗口内买一/卖一流量序列（C2 图表数据）
 * 每桶同时返回撤单/成交的瞬时字段和 *_cumulative 日内累计字段
 */
export async function getTradeFlowSeries(params: {
  sym: string;
  date: string;
  time: string;
  window_ms: number;
  points?: number;
}) {
  try {
    const response = await defHttp.get(
      {
        url: '/tradebook/trade_flow_series',
        params: params,
      },
      {
        joinTime: false,
      },
    );
    return processApiData(response.data);
  } catch (error) {
    console.error('Error fetching trade flow series:', error);
    throw error;
  }
}

/**
 * 获取订单生命周期（B4）
 * order_id 为快照订单的 order_local_id（即 csord 的 orderid）
 */
export async function getOrderLifecycle(params: {
  sym: string;
  date: string;
  order_id: number | string;
}) {
  try {
    const response = await defHttp.get({
      url: '/tradebook/order_lifecycle',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    console.error('Error fetching order lifecycle:', error);
    throw error;
  }
}
