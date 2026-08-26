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
