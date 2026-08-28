<template>
  <div class="global-order-search-trigger">
    <Button type="primary" @click="openModal" class="search-trigger-button">
      <SearchOutlined class="search-icon" />
      <span class="search-text">查询订单并跳转到时间</span>
    </Button>
  </div>

  <BasicModal
    v-model:visible="visible"
    title="订单查询"
    width="800px"
    :height="650"
    wrapClassName="global-order-search-modal"
    :show-cancel="true"
    :show-ok-btn="false"
    :can-fullscreen="false"
    :keyboard="true"
    cancel-text="取消"
    @cancel="handleModalCancel"
    centered
  >
    <template #insertFooter>
      <Button 
        type="primary" 
        @click="handleLockOrder" 
        :disabled="!searchResult || !searchResult.success"
        class="lock-button"
      >
        跳转至快照并锁定订单
      </Button>
    </template>
    <div class="global-order-search-form">
      <!-- 显示从volumeQueue页面读取的证券代码和日期 -->
      <div class="fixed-values-display">
        <div class="value-item">
          <span class="value-label">{{ securityLabel }}代码:</span>
          <span class="value-content">{{ form.sym || '请在主界面选择证券代码' }}</span>
        </div>
        <div class="value-item">
          <span class="value-label">交易日期:</span>
          <span class="value-content">{{ form.date || '请在主界面选择日期' }}</span>
        </div>
      </div>
      
      <!-- 表单字段区域 -->
      <div class="form-fields-container">
        <div class="form-field">
          <label class="field-label">订单时间</label>
          <Input
            v-model:value="form.order_time"
            placeholder="输入时间 (HH:mm:ss.SSS)"
            class="field-input"
            @change="handleTimeInputChange"
            @blur="handleTimeBlur"
          />
        </div>

        <div class="form-field">
          <label class="field-label">订单价格</label>
          <InputNumber
            v-model:value="form.order_price"
            class="field-input"
            :precision="pricePrecision"
            :step="priceStep"
            :placeholder="`订单价格（${securityLabel}，${pricePrecision}位小数）`"
          />
        </div>

        <div class="form-field">
          <label class="field-label">订单数量</label>
          <InputNumber 
            v-model:value="form.order_size" 
            class="field-input"
            :step="100"
            placeholder="订单数量"
          />
        </div>

        <div class="form-field">
          <label class="field-label">订单方向</label>
          <RadioGroup v-model:value="form.order_side" class="field-radio">
            <Radio :value="1">买入</Radio>
            <Radio :value="-1">卖出</Radio>
          </RadioGroup>
        </div>

        <div class="form-field">
          <label class="field-label">时间容差(毫秒)</label>
          <InputNumber 
            v-model:value="form.tolerance_ms" 
            class="field-input"
            :min="0"
            :max="10000"
            :step="10"
            placeholder="容差时间(毫秒)"
          />
        </div>
      </div>
      
      <!-- 查询按钮区域 -->
      <div class="search-button-container">
        <Button type="primary" @click="handleSearch" :loading="loading" class="search-button">
          查询订单
        </Button>
      </div>

      <!-- 查询结果区域 -->
      <div v-if="searchResult" class="search-result">
        <Divider>查询结果</Divider>
        <div v-if="searchResult.success" class="result-success">
          <div class="result-header">
            <span class="result-title">找到前向订单: {{ searchResult.orderid }}</span>
          </div>
          <div class="result-detail">
            <div class="detail-row">
              <span class="detail-label">订单ID:</span>
              <span class="detail-value">{{ searchResult.orderid }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">交易时间:</span>
              <span class="detail-value">{{ searchResult.datetime }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">价格:</span>
              <span class="detail-value">{{ formatPrice(searchResult.price) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">数量:</span>
              <span class="detail-value">{{ searchResult.size }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">方向:</span>
              <span class="detail-value">{{ searchResult.side === 1 ? '买入' : '卖出' }}</span>
            </div>
          </div>
        </div>
        <div v-else class="result-error">
          <div class="result-header">
            <span class="result-title">❌ 未找到匹配的订单</span>
          </div>
          <div class="result-detail">
            <div class="detail-row">
              <span class="detail-label">查询条件:</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">  - {{ securityLabel }}代码:</span>
              <span class="detail-value">{{ form.sym }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">  - 交易日期:</span>
              <span class="detail-value">{{ form.date }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">  - 订单时间:</span>
              <span class="detail-value">{{ form.order_time }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">  - 价格:</span>
              <span class="detail-value">{{ form.order_price }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">  - 数量:</span>
              <span class="detail-value">{{ form.order_size }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">  - 方向:</span>
              <span class="detail-value">{{ form.order_side === 1 ? '买入' : '卖出' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">  - 容差:</span>
              <span class="detail-value">{{ form.tolerance_ms }}ms</span>
            </div>
            <div class="detail-row error-message">
              <span class="detail-label">提示:</span>
              <span class="detail-value">{{ searchResult.message || '请检查查询条件是否正确，或尝试增加容差时间' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts">
  import { defineComponent, reactive, ref, computed, onUnmounted, nextTick } from 'vue';
  import { Tooltip, Input, InputNumber, Radio, RadioGroup, Button, Divider } from 'ant-design-vue';
  import { SearchOutlined } from '@ant-design/icons-vue';
  import { BasicModal } from '/@/components/Modal';
  import { findOrder, type FindOrderParams } from '/@/api/orderbook/orderbook';
  import { getSecurityType } from '/@/utils/securityType';
  import { useI18n } from '/@/hooks/web/useI18n';
  import { useRouter } from 'vue-router';
  import { useOrderLockStore } from '/@/store/orderLock';

  interface SearchResult {
    success: boolean;
    orderid?: number;
    datetime?: string;
    price?: number;
    size?: number;
    side?: number;
    message?: string;
  }

  export default defineComponent({
    name: 'GlobalOrderSearch',
    inheritAttrs: false,
    components: {
      Tooltip,
      SearchOutlined,
      BasicModal,
      Input,
      InputNumber,
      Radio,
      RadioGroup,
      Button,
      Divider,
    },

    setup() {
      const { t } = useI18n();
      const router = useRouter();
      const visible = ref(false);
      const loading = ref(false);
      const searchResult = ref<SearchResult | null>(null);
      const message = (window as any).$message;

      const form = reactive<FindOrderParams & { order_time: string }>({
        sym: '',
        date: '',
        order_time: '',
        order_price: 0,
        order_size: 0,
        order_side: 1,
        tolerance_ms: 100,
      });
      
      // 从localStorage读取volumeQueue页面的股票代码和日期
      const loadSavedValues = () => {
        form.sym = localStorage.getItem('volumeQueue_selectSym') || '';
        form.date = localStorage.getItem('volumeQueue_selectDate') || '';
      };

      loadSavedValues();

      // 证券类型相关：价格精度（股票2位/基金3位）与文案
      const currentSecurityType = computed(() => {
        const saved = localStorage.getItem('volumeQueue_securityType');
        if (saved === 'fund' || saved === 'stock') return saved;
        return form.sym ? getSecurityType(form.sym) : 'stock';
      });
      const securityLabel = computed(() => (currentSecurityType.value === 'fund' ? '基金' : '股票'));
      const pricePrecision = computed(() => (currentSecurityType.value === 'fund' ? 3 : 2));
      const priceStep = computed(() => (currentSecurityType.value === 'fund' ? 0.001 : 0.01));
      const formatPrice = (price?: number) => {
        if (price === undefined || price === null) return '';
        return Number(price).toFixed(pricePrecision.value);
      };

      

      const handleModalCancel = () => {
        visible.value = false;
      };

      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === 'Escape' && visible.value) {
          handleModalCancel();
        }
      };

      // 添加ESC键监听
      document.addEventListener('keydown', handleKeyDown);

      // 组件卸载时移除监听
      onUnmounted(() => {
        document.removeEventListener('keydown', handleKeyDown);
      });

      

      

      const checkTimeBoundary = (timeStr: string) => {
        const minTime = '09:30:00.000';
        const maxTime = '15:00:00.000';
        if (timeStr < minTime) return minTime;
        if (timeStr > maxTime) return maxTime;
        return timeStr;
      };

      const handleTimeInputChange = (e: any) => {
        const inputValue = e.target.value;
        form.order_time = inputValue;
        // 用户输入时间时，直接存储到 sessionStorage
        if (inputValue) {
          sessionStorage.setItem('volumeQueue_userInputTime', inputValue);
          console.log('💾 [GlobalOrderSearch] 用户输入时间已存储:', inputValue);
        }
      };

      const handleTimeBlur = (e: any) => {
        const raw = e?.target?.value ?? form.order_time;
        // 不做边界检查，直接使用用户输入的值
        form.order_time = raw;
        // 存储到 sessionStorage
        if (raw) {
          sessionStorage.setItem('volumeQueue_userInputTime', raw);
          console.log('💾 [GlobalOrderSearch] 用户输入时间已存储（blur）:', raw);
        }
      };

      

      function openModal() {
        // 加载存储的值
        loadSavedValues();
        // 直接打开弹窗
        visible.value = true;
        
        // 使用nextTick确保在弹窗完全打开后检查并显示通知
        nextTick(() => {
          // 检查是否有股票代码和日期
          if (!form.sym || !form.date) {
            message.warning('请先在VolumeQueue页面选择股票代码和日期');
          }
        });
      }

      function closeModal() {
        visible.value = false;
        // 重置表单
        Object.assign(form, {
          sym: '',
          date: '',
          order_time: '',
          order_price: 0,
          order_size: 0,
          order_side: 1,
          tolerance_ms: 100,
        });
        searchResult.value = null;
      }

      async function handleSearch() {
        // 检查从localStorage读取的股票代码和日期是否存在
        const currentSym = localStorage.getItem('volumeQueue_selectSym') || form.sym;
        const currentDate = localStorage.getItem('volumeQueue_selectDate') || form.date;
        
        // 首先检查股票代码和日期是否存在
        if (!currentSym || !currentDate) {
          message.warning('请先在VolumeQueue页面选择股票代码和日期');
          return;
        }
        
        // 检查其他必填字段
        if (!form.order_time || !form.order_price || !form.order_size) {
          message.warning('请填写完整的订单信息');
          return;
        }
        
        // 更新form中的值
        form.sym = currentSym;
        form.date = currentDate;

        loading.value = true;
        searchResult.value = null;

        try {
          const params: FindOrderParams = {
            sym: form.sym,
            date: form.date,
            order_time: form.order_time,
            order_price: form.order_price,
            order_size: form.order_size,
            order_side: form.order_side,
            tolerance_ms: form.tolerance_ms,
          };

          const result = await findOrder(params);
          
          if (result?.code === 0 && result?.data?.result) {
            // 使用后端返回的 success 字段
            if (result.data.result.success) {
              searchResult.value = {
                success: true,
                orderid: result.data.result.orderid,
                datetime: result.data.result.datetime,
                price: result.data.result.price,
                size: result.data.result.size,
                side: result.data.result.side,
                message: result.data.result.message,
              };
            } else {
              searchResult.value = {
                success: false,
                message: result.data.result.message || '没有找到匹配的订单',
              };
            }
          } else {
            searchResult.value = {
              success: false,
              message: result?.message || '查询失败',
            };
          }
        } catch (error) {
          console.error('查询订单失败:', error);
          searchResult.value = {
            success: false,
            message: '查询失败，请检查网络连接和参数',
          };
        } finally {
          loading.value = false;
        }
      }

      // 跳转到快照并锁定订单（使用Pinia状态管理）
      const handleLockOrder = () => {
        console.log('🚀 [GlobalOrderSearch] handleLockOrder 开始执行');
        
        // 安全检查 searchResult
        const result = searchResult.value;
        if (!result || typeof result !== 'object') {
          console.error('❌ [GlobalOrderSearch] No search result available');
          if (message && typeof message.error === 'function') {
            message.error('请先搜索订单');
          }
          return;
        }
        
        console.log('✓ [GlobalOrderSearch] searchResult:', JSON.stringify(result, null, 2));
        
        // 安全检查 success 属性
        if (!result.success) {
          console.error('❌ [GlobalOrderSearch] Search failed:', result.message || 'Unknown error');
          if (message && typeof message.error === 'function') {
            message.error('搜索订单失败，请重试');
          }
          return;
        }

        // 安全提取所有需要的数据
        const currentSym = (form.sym || '').toString();
        const currentDate = (form.date || '').toString();
        const orderId = (result.orderid || '').toString();
        const timestamp = (result.datetime || '').toString();
        
        console.log('📝 [GlobalOrderSearch] 提取的数据:');
        console.log('   - 股票代码:', currentSym);
        console.log('   - 交易日期:', currentDate);
        console.log('   - 订单ID:', orderId);
        console.log('   - 时间戳:', timestamp);
        
        if (!currentSym || !currentDate || !orderId || !timestamp) {
          console.error('❌ [GlobalOrderSearch] 缺少必要参数');
          if (message && typeof message.error === 'function') {
            message.error('缺少必要参数，无法锁定订单');
          }
          return;
        }
        
        try {
          console.log('💾 [GlobalOrderSearch] 开始存储数据到 sessionStorage（仅当前会话有效）');
          
          // 获取用户输入的时间（直接使用，不做任何处理）
          const userInputTime = form.order_time || sessionStorage.getItem('volumeQueue_userInputTime') || '';
          console.log('   - 用户输入的时间:', userInputTime);
          
          // 存储数据到 sessionStorage（刷新后不保留）
          sessionStorage.setItem('volumeQueue_lockTimestamp', userInputTime); // 直接使用用户输入的时间
          sessionStorage.setItem('volumeQueue_lockOrderId', orderId);
          sessionStorage.setItem('volumeQueue_lockSym', currentSym);
          sessionStorage.setItem('volumeQueue_lockDate', currentDate);
          sessionStorage.setItem('volumeQueue_isFromGlobalSearch', 'true');
          sessionStorage.setItem('volumeQueue_autoLock', 'true');
          
          // 不存储任何数据到 localStorage（每次刷新都清空）
          // 清除所有 localStorage 数据
          localStorage.removeItem('volumeQueue_selectSym');
          localStorage.removeItem('volumeQueue_selectDate');
          localStorage.removeItem('volumeQueue_timestamp');
          localStorage.removeItem('volumeQueue_lockOrderId');
          localStorage.removeItem('volumeQueue_isFromGlobalSearch');
          localStorage.removeItem('volumeQueue_autoLock');
          
          console.log('✓ [GlobalOrderSearch] 数据已存储到 sessionStorage');
          console.log('   sessionStorage 内容验证:');
          console.log('   - volumeQueue_lockTimestamp:', sessionStorage.getItem('volumeQueue_lockTimestamp'));
          console.log('   - volumeQueue_lockOrderId:', sessionStorage.getItem('volumeQueue_lockOrderId'));
          console.log('   - volumeQueue_lockSym:', sessionStorage.getItem('volumeQueue_lockSym'));
          console.log('   - volumeQueue_lockDate:', sessionStorage.getItem('volumeQueue_lockDate'));
          console.log('   - volumeQueue_isFromGlobalSearch:', sessionStorage.getItem('volumeQueue_isFromGlobalSearch'));
          console.log('   - volumeQueue_autoLock:', sessionStorage.getItem('volumeQueue_autoLock'));
          
          // 存储数据到 Pinia store
          console.log('📦 [GlobalOrderSearch] 准备存储到 Pinia store');
          const orderLockStore = useOrderLockStore();
          console.log('   - store 实例已获取');
          console.log('   - 存储前 hasLockData:', orderLockStore.hasLockData);
          console.log('   - 存储前 lockData:', orderLockStore.lockData);
          
          orderLockStore.setLockData({
            orderId,
            sym: currentSym,
            date: currentDate,
            timestamp,
            fromGlobalSearch: true
          });
          
          console.log('✓ [GlobalOrderSearch] 数据已存储到 Pinia store');
          console.log('   - 存储后 hasLockData:', orderLockStore.hasLockData);
          console.log('   - 存储后 lockData:', JSON.stringify(orderLockStore.lockData, null, 2));
          
          // 显示成功消息
          if (message && typeof message.success === 'function') {
            message.success('正在跳转并锁定订单...');
          }
          
          console.log('🔄 [GlobalOrderSearch] 准备跳转到 volumeQueue 页面');
          
          // 关闭弹窗
          visible.value = false;
          console.log('✓ [GlobalOrderSearch] 弹窗已关闭');
          
          // 跳转到 volumeQueue 页面
          router.push('/orderbookQueue/volumeQueue').then(() => {
            console.log('✅ [GlobalOrderSearch] 路由跳转成功');
          }).catch((err) => {
            console.error('❌ [GlobalOrderSearch] 路由跳转失败:', err);
          });
          
          console.log('✅ [GlobalOrderSearch] handleLockOrder 执行完成');
          
        } catch (err) {
          console.error('❌ [GlobalOrderSearch] 操作失败:', err);
          console.error('   错误堆栈:', err.stack);
          if (message && typeof message.error === 'function') {
            message.error('操作失败，请重试');
          }
        }
      };

      return {
        visible,
        loading,
        form,
        searchResult,
        securityLabel,
        pricePrecision,
        priceStep,
        formatPrice,
        handleTimeInputChange,
        handleTimeBlur,
        openModal,
        closeModal,
        handleSearch,
        handleModalCancel,
        handleLockOrder,
        t,
      };
    },
  });
</script>

<style lang="less" scoped>
.global-order-search-trigger {
  display: flex;
  align-items: center;
  height: 100%;
  
  .search-trigger-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 100%;
    min-height: 40px;
    padding: 0 16px;
    font-size: 14px;
    font-weight: 500;
    border-radius: 4px;
    transition: all 0.3s ease;
    
    .search-icon {
      font-size: 16px;
    }
    
    .search-text {
      white-space: nowrap;
    }
    
    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 2px 8px rgba(255, 255, 255, 0.3);
    }
    
    &:active {
      transform: translateY(0);
    }
  }
}

.global-order-search-form {
  max-height: 70vh;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
}

.fixed-values-display {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-radius: 6px;
  border: 1px solid #e0e0e0;

  .value-item {
    display: flex;
    align-items: center;
    
    .value-label {
      font-weight: 500;
      color: #595959;
      margin-right: 6px;
      white-space: nowrap;
      min-width: 80px;
    }
    
    .value-content {
      font-weight: 600;
      color: #1890ff;
      background-color: white;
      padding: 2px 6px;
      border-radius: 3px;
      border: 1px solid #d9d9d9;
      font-size: 13px;
    }
  }
}

.form-fields-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px 20px;
  margin-bottom: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  
  .field-label {
    font-weight: 500;
    color: #595959;
    margin-bottom: 4px;
    font-size: 14px;
  }
  
  .field-input {
    width: 100%;
    height: 32px;
  }
  
  .field-radio {
    display: flex;
    align-items: center;
    gap: 16px;
    height: 32px;
  }
}

.search-button-container {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 12px;
  
  .search-button {
    min-width: 120px;
    height: 32px;
  }
}

.search-result {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.result-header {
  margin-bottom: 12px;
}

.result-title {
  font-size: 16px;
  font-weight: 500;
  color: #1890ff;
}

.result-success,
.result-error {
  padding: 0;
}

.result-detail {
  .detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
    padding: 4px 8px;
    background-color: #fafafa;
    border-radius: 4px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .detail-label {
    font-weight: 500;
    color: #595959;
    flex-shrink: 0;
    font-size: 13px;
  }
  
  .detail-value {
    color: #262626;
    font-weight: 400;
    font-size: 13px;
  }
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #e0e0e0;
  
  .action-button {
    min-width: 100px;
  }
}

.lock-button {
  margin-right: 8px;
}

.result-error {
  .result-header {
    background-color: #fff2f0;
    border-left: 3px solid #ff4d4f;
    
    .result-title {
      color: #cf1322;
    }
  }
  
  .error-message {
    background-color: #fff7e6;
    border-left: 2px solid #faad14;
    margin-top: 8px;
    
    .detail-value {
      color: #d46b08;
      font-weight: 500;
    }
  }
}
</style>

<style lang="less">
// 全局样式，用于控制弹窗位置
.global-order-search-modal {
  .ant-modal {
    top: -10vh !important;
  }
}
</style>