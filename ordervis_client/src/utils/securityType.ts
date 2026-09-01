export type SecurityType = 'stock' | 'fund';

export const securityTypeOptions = [
  { value: 'stock' as SecurityType, label: '股票' },
  { value: 'fund' as SecurityType, label: '基金（仅场内 ETF/LOF）' },
];

// 上海/深圳市场常见的场内基金、ETF、LOF代码段。
// 后端如果返回了明确的类型字段，会优先使用后端字段；这些前缀用于兼容当前仅返回代码字符串的 symList 接口。
const FUND_CODE_PREFIXES = ['15', '16', '50', '51', '52', '56', '58', '59'];

function explicitSecurityType(item: any): SecurityType | undefined {
  if (!item || typeof item !== 'object') return undefined;

  // 后端 symList 自 2026-08-28 起返回 { code, type: 'stock' | 'fund' | 'unknown' }
  const type =
    item.type ?? item.securityType ?? item.security_type ?? item.asset_type ?? item.instrument_type;
  if (typeof type === 'string') {
    const normalized = type.toLowerCase();
    // unknown 表示后端两张表里都没查到，落回代码段启发式判断
    if (normalized === 'unknown') return undefined;
    if (
      normalized.includes('fund') ||
      normalized.includes('etf') ||
      normalized.includes('lof') ||
      normalized.includes('基金')
    ) {
      return 'fund';
    }
    if (
      normalized.includes('stock') ||
      normalized.includes('equity') ||
      normalized.includes('股票')
    ) {
      return 'stock';
    }
  }

  if (typeof item.is_ETF === 'boolean') {
    return item.is_ETF ? 'fund' : 'stock';
  }
  if (typeof item.isETF === 'boolean') {
    return item.isETF ? 'fund' : 'stock';
  }

  return undefined;
}

export function getSymbolValue(item: any): string {
  if (typeof item === 'string' || typeof item === 'number') return String(item);
  return String(item?.value ?? item?.sym ?? item?.symbol ?? item?.code ?? '').trim();
}

export function getSecurityType(item: any): SecurityType {
  const explicit = explicitSecurityType(item);
  if (explicit) return explicit;

  const symbol = getSymbolValue(item).toUpperCase();
  const [code, market] = symbol.split('.');

  // .OF 是场外基金代码，虽然不一定提供订单簿，但仍应归入基金分类。
  if (market === 'OF') return 'fund';

  const normalizedCode = code.replace(/!.*/, '');
  return FUND_CODE_PREFIXES.some((prefix) => normalizedCode.startsWith(prefix)) ? 'fund' : 'stock';
}

export function toSymbolOption(item: any) {
  const value = getSymbolValue(item);
  return {
    value,
    label: value,
    securityType: getSecurityType(item),
  };
}
