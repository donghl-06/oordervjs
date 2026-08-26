import { defHttp } from '/@/utils/http/axios';
import { processApiData } from '/@/utils/dataProcessor';

export async function getTasks(params: any) {
  try {
    const response = await defHttp.get({
      url: '/order_data_generate/get_tasks',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error getting tasks:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function createTask(params: any) {
  try {
    const response = await defHttp.get({
      url: '/order_data_generate/create_task',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error creating task:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function deleteTask(params: any) {
  try {
    const response = await defHttp.get({
      url: '/order_data_generate/delete_task',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error deleting task:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getSyms(params: any) {
  try {
    const response = await defHttp.get({
      url: '/order_data_generate/get_syms',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error getting syms_dates:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}

export async function getDates(params: any) {
  try {
    const response = await defHttp.get({
      url: '/order_data_generate/get_dates',
      params: params,
    });
    return processApiData(response.data);
  } catch (error) {
    // 处理错误
    console.error('Error getting syms_dates:', error);
    throw error; // 将错误向上抛出，以便调用者处理
  }
}
