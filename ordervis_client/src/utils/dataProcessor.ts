/**
 * 数据处理工具函数
 * 对API返回的数值进行标准化处理
 */

/**
 * 处理数值字段，对除了价格之外的数值进行除以100并四舍五入
 * @param value 原始数值
 * @param fieldName 字段名称
 * @returns 处理后的数值
 */
export function processNumericValue(value: any, fieldName: string): any {
  if (typeof value !== 'number' || isNaN(value)) {
    return value;
  }

  // 价格相关字段不处理
  const priceFields = [
    'price',
    'px',
    'ask_px',
    'bid_px',
    'last_px',
    'open_px',
    'high_px',
    'low_px',
    'close_px',
  ];
  const isPrice = priceFields.some((field) =>
    fieldName.toLowerCase().includes(field.toLowerCase()),
  );

  if (isPrice) {
    return value;
  }

  // 对指定的字段进行精确匹配处理
  const numericFields = ['total_volume', 'remaining_volume'];
  const shouldProcess = numericFields.includes(fieldName.toLowerCase());

  // 特殊处理：getPastTimeTradeInfo API中的时间间隔统计字段
  const timeIntervalFields = ['last_1min', 'last_3s', 'last_500ms', 'last_50ms', 'last_10ms'];
  const isTimeIntervalField = timeIntervalFields.includes(fieldName.toLowerCase());

  if (shouldProcess || isTimeIntervalField) {
    return Math.round(value / 100);
  }

  return value;
}

/**
 * 递归处理对象中的所有数值字段
 * @param data 待处理的数据对象
 * @returns 处理后的数据对象
 */
export function processApiData(data: any): any {
  if (data === null || data === undefined) {
    return data;
  }

  if (Array.isArray(data)) {
    return data.map((item) => processApiData(item));
  }

  if (typeof data === 'object') {
    const processedData: any = {};
    for (const [key, value] of Object.entries(data)) {
      if (typeof value === 'number') {
        processedData[key] = processNumericValue(value, key);
      } else if (typeof value === 'object') {
        processedData[key] = processApiData(value);
      } else {
        processedData[key] = value;
      }
    }
    return processedData;
  }

  return data;
}
