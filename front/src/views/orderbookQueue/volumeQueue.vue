<template>
  <context-holder />
  <div class="m-2 overflow-hidden bg-white">
    <div class="main-mode" style="margin-bottom: 40px">
      <div class="data-ul-top">
        <div class="data-li">
          <div class="filter-mode compact-row primary-filter-row">
            <div class="filter-item">
              <span class="field-label">证券类型</span>
              <Select
                v-model:value="securityType"
                style="width: 90px; margin-left: 11px"
                :options="securityTypeOptions"
                :allow-clear="false"
                @change="handleSecurityTypeChange"
              />
            </div>
            <div class="filter-item">
              <span class="field-label">证券代码</span>
              <Select
                v-model:value="selectSym"
                show-search
                :placeholder="`选择${securityType === 'fund' ? '基金' : '股票'}代码`"
                style="width: 120px; margin-left: 11px"
                :options="filteredSymsData"
                :filter-option="symFilterOption"
                @change="selectSymItem"
                @search="handleSymSearch"
                @blur="handleSymBlur"
                @focus="handleSymFocus"
                @input="handleSymInput"
                :allow-clear="false"
              />
            </div>
            <div class="filter-item">
              <span class="field-label">日期</span>
              <Select
                v-model:value="selectDate"
                show-search
                placeholder="选择日期"
                style="width: 140px"
                :options="datesData"
                :filter-option="dateFilterOption"
                @change="selectDateItem"
                @search="handleDateSearch"
                @blur="handleDateBlur"
                :allow-clear="false"
              />
            </div>
            <div class="filter-item">
              <Button
                type="primary"
                @click="getOrderbookData"
                :disabled="!hasSymbol || !hasDate || loading"
              >
                <Spin v-if="loading" size="small" style="margin-right: 8px" />
                {{ loading ? '加载中...' : '开始' }}
              </Button>
            </div>
          </div>

          <div class="filter-mode compact-row navigation-row">
            <div class="filter-item">
              <span class="field-label">跳转时间</span>
              <Input
                v-model:value="displayTime"
                placeholder="输入跳转时间"
                style="width: 160px; margin-left: 11px"
                @change="handleTimeInputChange"
                @blur="handleTimeBlur"
              />
              <Button
                type="primary"
                @click="clickMoveTime"
                :disabled="isButtonDisabled"
                style="margin-left: 5px"
                >跳转到时间</Button
              >
            </div>
            <div class="filter-item info-item">
              <span class="info-label">当前快照ID: {{ changeIndex }}</span>
              <Tooltip title="移动订单会改变该值">
                <QuestionCircleOutlined style="margin-left: 5px; color: #1890ff; cursor: pointer" />
              </Tooltip>
              <!-- <span class="info-label" style="margin-left: 20px;">快照ID: {{ snapshotId }}</span>
                <Tooltip title="snapshot_id">
                  <QuestionCircleOutlined style="margin-left: 5px; color: #1890ff; cursor: pointer;" />
                </Tooltip> -->
            </div>
          </div>
          <div class="filter-mode compact-row lock-row">
            <div class="filter-item lock-controls">
              <span class="field-label">锁定订单</span>
              <Input
                v-model:value="lockByVolumeValue"
                placeholder="数量"
                style="width: 80px; margin-left: 8px"
              />
              <Button
                type="primary"
                size="small"
                @click="lockOrdersByVolume"
                style="margin-left: 3px"
                >按量</Button
              >
              <Input
                v-model:value="lockByIdValue"
                placeholder="订单ID"
                style="width: auto; min-width: 80px; max-width: 150px; margin-left: 8px"
              />
              <Button type="primary" size="small" @click="lockOrdersById(true)" style="margin-left: 3px"
                >按ID</Button
              >
              <Button size="small" @click="clearLockedOrders" style="margin-left: 8px">清除</Button>
            </div>
            <div class="filter-item info-item">
              <span class="info-label">已锁定: {{ lockedOrderIds.length }}个</span>
            </div>
          </div>
          <div class="filter-mode compact-row movement-row">
            <span class="section-label">时间快进</span>
            <div class="button-group">
              <Button
                type="primary"
                @click="moveTimes(50)"
                :disabled="isButtonDisabled"
                class="time-btn"
                >+50ms</Button
              >
              <Button
                type="primary"
                @click="moveTimes(500)"
                :disabled="isButtonDisabled"
                class="time-btn"
                >+500ms</Button
              >
              <Button
                type="primary"
                @click="moveTimes(3000)"
                :disabled="isButtonDisabled"
                class="time-btn"
                >+3s</Button
              >
              <Button
                type="primary"
                @click="moveTimes(60000)"
                :disabled="isButtonDisabled"
                class="time-btn"
                >+1min</Button
              >
            </div>
          </div>
          <div class="filter-mode compact-row movement-row">
            <span class="section-label">时间回退</span>
            <div class="button-group">
              <Button
                type="primary"
                @click="moveTimes(-50)"
                :disabled="isButtonDisabled"
                class="time-btn"
                >-50ms</Button
              >
              <Button
                type="primary"
                @click="moveTimes(-500)"
                :disabled="isButtonDisabled"
                class="time-btn"
                >-500ms</Button
              >
              <Button
                type="primary"
                @click="moveTimes(-3000)"
                :disabled="isButtonDisabled"
                class="time-btn"
                >-3s</Button
              >
              <Button
                type="primary"
                @click="moveTimes(-60000)"
                :disabled="isButtonDisabled"
                class="time-btn"
                >-1min</Button
              >
            </div>
          </div>
          <div class="filter-mode compact-row movement-row">
            <span class="section-label">订单快进</span>
            <div class="button-group">
              <Button
                type="primary"
                @click="moveticks(1)"
                :disabled="isButtonDisabled"
                class="order-btn"
                >+1 orders</Button
              >
              <Button
                type="primary"
                @click="moveticks(50)"
                :disabled="isButtonDisabled"
                class="order-btn"
                >+50 orders</Button
              >
              <Button
                type="primary"
                @click="moveticks(100)"
                :disabled="isButtonDisabled"
                class="order-btn"
                >+100 orders</Button
              >
              <Button
                type="primary"
                @click="moveticks(500)"
                :disabled="isButtonDisabled"
                class="order-btn"
                >+500 orders</Button
              >
            </div>
          </div>
          <div class="filter-mode compact-row movement-row">
            <span class="section-label">订单回退</span>
            <div class="button-group">
              <Button
                type="primary"
                @click="moveticks(-1)"
                :disabled="isButtonDisabled"
                class="order-btn"
                >-1 orders</Button
              >
              <Button
                type="primary"
                @click="moveticks(-50)"
                :disabled="isButtonDisabled"
                class="order-btn"
                >-50 orders</Button
              >
              <Button
                type="primary"
                @click="moveticks(-100)"
                :disabled="isButtonDisabled"
                class="order-btn"
                >-100 orders</Button
              >
              <Button
                type="primary"
                @click="moveticks(-500)"
                :disabled="isButtonDisabled"
                class="order-btn"
                >-500 orders</Button
              >
            </div>
          </div>
        </div>
        <div class="data-li">
          <Table
            :columns="level_columns"
            :dataSource="levelData"
            :scroll="{ y: 200 }"
            :pagination="false"
            :style="{ height: '250px' }"
            bordered
          />
        </div>
        <div class="data-li">
          <Table
            :columns="trader_columns"
            :dataSource="tradeData"
            :scroll="{ y: 200 }"
            :pagination="false"
            :style="{ height: '250px' }"
            bordered
          />
        </div>
      </div>
    </div>
    <div class="main-mode">
      <div class="data-ul">
        <div class="data-li" v-show="showAsk">
          <VolumeDataTable
            :data="volumeData['ask1']?.data?.[0]?.[0] || {}"
            :derection="
              volumeData['ask1_price']
                ? '  卖一价：' + (volumeData['ask1_price'] / 10000).toFixed(volumeData.is_ETF ? 3 : 2)
                : '  卖一价：'
            "
            :is-fullscreen="askIsFullscreen"
            :search-value="searchValue"
            :locked-order-ids="lockedOrderIds"
            @update-fullscreen="showHideTable"
          />
        </div>
        <div class="data-li" v-show="showBid">
          <VolumeDataTable
            :data="volumeData['bid1']?.data?.[0]?.[0] || {}"
            :derection="
              volumeData['bid1_price']
                ? '  买一价：' + (volumeData['bid1_price'] / 10000).toFixed(volumeData.is_ETF ? 3 : 2)
                : '  买一价：'
            "
            :is-fullscreen="bidIsFullscreen"
            :search-value="searchValue"
            :locked-order-ids="lockedOrderIds"
            :show-tooltip="true"
            @update-fullscreen="showHideTable"
          />
        </div>
      </div>
      <div class="data-ul">
        <div class="data-li" v-show="showAsk">
          <VolumeDataTable
            :data="volumeData['ask2']?.data?.[0]?.[0] || {}"
            :derection="
              volumeData['ask2_price']
                ? '  卖二价：' + (volumeData['ask2_price'] / 10000).toFixed(volumeData.is_ETF ? 3 : 2)
                : '  卖二价：'
            "
            :is-fullscreen="askIsFullscreen"
            :search-value="searchValue"
            :locked-order-ids="lockedOrderIds"
            @update-fullscreen="showHideTable"
          />
        </div>
        <div class="data-li" v-show="showBid">
          <VolumeDataTable
            :data="volumeData['bid2']?.data?.[0]?.[0] || {}"
            :derection="
              volumeData['bid2_price']
                ? '  买二价：' + (volumeData['bid2_price'] / 10000).toFixed(volumeData.is_ETF ? 3 : 2)
                : '  买二价：'
            "
            :is-fullscreen="bidIsFullscreen"
            :search-value="searchValue"
            :locked-order-ids="lockedOrderIds"
            @update-fullscreen="showHideTable"
          />
        </div>
      </div>
      <div class="data-ul">
        <div class="data-li" v-show="showAsk">
          <VolumeDataTable
            :data="volumeData['ask3']?.data?.[0]?.[0] || {}"
            :derection="
              volumeData['ask3_price']
                ? '  卖三价：' + (volumeData['ask3_price'] / 10000).toFixed(volumeData.is_ETF ? 3 : 2)
                : '  卖三价：'
            "
            :is-fullscreen="askIsFullscreen"
            :search-value="searchValue"
            :locked-order-ids="lockedOrderIds"
            @update-fullscreen="showHideTable"
          />
        </div>
        <div class="data-li" v-show="showBid">
          <VolumeDataTable
            :data="volumeData['bid3']?.data?.[0]?.[0] || {}"
            :derection="
              volumeData['bid3_price']
                ? '  买三价：' + (volumeData['bid3_price'] / 10000).toFixed(volumeData.is_ETF ? 3 : 2)
                : '  买三价：'
            "
            :is-fullscreen="bidIsFullscreen"
            :search-value="searchValue"
            :locked-order-ids="lockedOrderIds"
            @update-fullscreen="showHideTable"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="js" setup>
    import { ref, computed, onMounted, onUnmounted, watch, h, nextTick } from 'vue';
    import { useRoute, useRouter } from 'vue-router';
    import { uploadFile, getListObjectFile, getObjectDownloadFile } from '../../services/minioService';
    import { Table, Empty, Spin, Radio, Button, Select, Input, Tooltip, Progress  } from 'ant-design-vue';
  import { QuestionCircleOutlined } from '@ant-design/icons-vue';
    import { getSymList, getDateList, getVolumeData, getDatetimeList, getVolumeDataByTime, getSnapshotById, getSnapshotByIndex, getSnapshotByTime, getPastTimeTradeInfo, initTradeBook, getProgress, checkServerStatus } from '/@/api/orderbook/orderbook';
    import VolumeDataTable from './components/VolumeTable.vue'
    import { useMessage } from '/@/hooks/web/useMessage';
    import { createProgressListener } from '/@/utils/websocket';
    import { useOrderLockStore } from '/@/store/orderLock';
    import {
      getSecurityType,
      securityTypeOptions,
      toSymbolOption,
    } from '/@/utils/securityType';
    import { 
      validateOrderLockData, 
      withOrderLockErrorHandling, 
      showOrderLockFeedback, 
      handleOrderLockError,
      cleanLockParamsFromUrl,
      formatTimestamp 
    } from '/@/logics/orderLockUtils';

    const loading = ref(true);
    const messageText = ref('');
    const volumeData = ref({});
    const isETF = ref(false);
    const { createMessage } = useMessage();

    // 从localStorage恢复orderIndex，如果没有则默认为0
    const orderIndex = ref(parseInt(localStorage.getItem('volumeQueue_orderIndex')) || 0);

    // 存储API返回的change_index
    const changeIndex = ref(0);

    // 存储API返回的snapshot_id
    const snapshotId = ref(0);

    const securityType = ref(localStorage.getItem('volumeQueue_securityType') || 'stock');
    const selectSym = ref('');
    const symsData = ref([]);
    const hasSymbol = ref(false);

    const filteredSymsData = computed(() => {
      return symsData.value.filter((option) => option.securityType === securityType.value);
    });

    const selectDate = ref('');
    const datesData = ref([]);
    const hasDate = ref(false);

    // 初始化Pinia状态管理
    const orderLockStore = useOrderLockStore();
    
    // 获取路由实例
    const route = useRoute();
    const router = useRouter();
    
    console.log('🔧 [VolumeQueue] ========== 初始化 Pinia Store 监听 ==========');
    console.log('   - orderLockStore 已创建');
    console.log('   - 初始 hasLockData:', orderLockStore.hasLockData);
    console.log('   - 初始 lockData:', orderLockStore.lockData);
    
    // 监听 Pinia store 中的锁定数据变化
    watch(() => orderLockStore.hasLockData, async (hasData, oldValue) => {
      console.log('🔔 [VolumeQueue] ========== Pinia Store 变化检测 ==========');
      console.log('   - 旧值 (oldValue):', oldValue);
      console.log('   - 新值 (hasData):', hasData);
      console.log('   - lockData:', JSON.stringify(orderLockStore.lockData, null, 2));
      
      if (hasData) {
        console.log('✅ [VolumeQueue] 检测到 Pinia 中有新的锁定数据，开始处理');
        
        // 延迟一下确保数据完全写入
        await nextTick();
        
        // 使用统一的订单锁定处理器
        await withOrderLockErrorHandling(async () => {
          // 验证锁定数据
          const validationResult = validateOrderLockData(orderLockStore.lockData);
          if (!validationResult.success) {
            showOrderLockFeedback(validationResult);
            return;
          }
          
          console.log('🔄 [VolumeQueue] 使用 Pinia 数据处理订单锁定');
          
          // 调用统一的订单锁定处理器
          await unifiedOrderLockHandler(validationResult.data);
          
          // 清理 Pinia 状态中的锁定数据
          orderLockStore.clearLockData();
          
          console.log('✅ [VolumeQueue] Pinia 订单锁定处理完成');
        }, '订单锁定流程');
      }
    }, { immediate: true }); // 立即执行一次，检查是否已有数据
    
    console.log('✓ [VolumeQueue] Pinia Store 监听器已设置');
    
    // 处理来自 GlobalOrderSearch 的锁定请求（使用 sessionStorage，刷新后不保留）
    const handleGlobalSearchLockRequest = async () => {
      console.log('🔍 [VolumeQueue] ========== 检查 GlobalOrderSearch 锁定请求 ==========');
      
      // 检查是否有来自GlobalOrderSearch的单个订单锁定请求（只从 sessionStorage 读取）
      const isFromGlobalSearch = sessionStorage.getItem('volumeQueue_isFromGlobalSearch');
      const autoLock = sessionStorage.getItem('volumeQueue_autoLock');
      const lockTime = sessionStorage.getItem('volumeQueue_lockTimestamp'); // 用户输入的时间
      const lockOrderId = sessionStorage.getItem('volumeQueue_lockOrderId');
      const lockSym = sessionStorage.getItem('volumeQueue_lockSym');
      const lockDate = sessionStorage.getItem('volumeQueue_lockDate');
      
      console.log('🔍 [VolumeQueue] 检查 sessionStorage 中的锁定数据:');
      console.log('   - isFromGlobalSearch:', isFromGlobalSearch);
      console.log('   - autoLock:', autoLock);
      console.log('   - lockTime:', lockTime);
      console.log('   - lockOrderId:', lockOrderId);
      console.log('   - lockSym:', lockSym);
      console.log('   - lockDate:', lockDate);
      
      if (isFromGlobalSearch === 'true' && autoLock === 'true' && lockTime && lockOrderId) {
        console.log('✅ [VolumeQueue] 检测到来自 GlobalOrderSearch 的自动锁定请求');
        console.log('📋 [VolumeQueue] 锁定参数:');
        console.log('   - 订单ID:', lockOrderId);
        console.log('   - 用户输入的时间:', lockTime);
        console.log('   - 股票代码:', lockSym);
        console.log('   - 交易日期:', lockDate);
        
        // 延迟执行，确保页面数据已加载
        setTimeout(async () => {
          try {
            console.log('⏱️ [VolumeQueue] 开始自动处理流程...');
            
            // 第一步：设置股票代码和日期（如果提供）
            if (lockSym && lockDate) {
              console.log('📝 [VolumeQueue] 步骤1: 设置股票代码和日期');
              securityType.value = getSecurityType(lockSym);
              selectSym.value = lockSym;
              selectDate.value = lockDate;
              hasSymbol.value = true;
              hasDate.value = true;
              localStorage.setItem('volumeQueue_selectSym', lockSym);
              localStorage.setItem('volumeQueue_securityType', securityType.value);
              localStorage.setItem('volumeQueue_selectDate', lockDate);
              console.log('   ✓ 股票代码已设置:', selectSym.value);
              console.log('   ✓ 交易日期已设置:', selectDate.value);
              console.log('   ✓ hasSymbol:', hasSymbol.value);
              console.log('   ✓ hasDate:', hasDate.value);
            } else {
              console.warn('⚠️ [VolumeQueue] 缺少股票代码或日期');
            }
            
            // 第二步：填充跳转时间输入框
            console.log('📝 [VolumeQueue] 步骤2: 填充跳转时间');
            console.log('   - lockTime:', lockTime);
            
            // 直接使用用户输入的时间，不做任何处理
            selectTime.value = lockTime;
            console.log('   ✓ 跳转时间已填充:', selectTime.value);
            
            // 第三步：填充锁定订单ID输入框
            console.log('📝 [VolumeQueue] 步骤3: 填充订单ID到输入框');
            lockByIdValue.value = lockOrderId;
            console.log('   ✓ 订单ID已填充到输入框:', lockByIdValue.value);
            
            // 第四步：加载日期列表（如果需要）
            if (lockSym && !datesData.value.length) {
              console.log('📝 [VolumeQueue] 步骤4: 加载日期列表');
              loading.value = true;
              const params = { sym: lockSym };
              
              try {
                const res = await getDateList(params);
                loading.value = false;
                
                if (res.code == 0) {
                  datesData.value = res.data.map(item => ({ label: item, value: item }));
                  console.log('   ✓ 日期列表已加载，共', datesData.value.length, '个日期');
                } else {
                  console.error('   ❌ 加载日期列表失败:', res.message);
                }
              } catch (error) {
                loading.value = false;
                console.error('   ❌ 加载日期列表异常:', error);
              }
            }
            
            // 第五步：点击"开始"按钮加载数据
            console.log('📝 [VolumeQueue] 步骤5: 点击"开始"按钮加载数据');
            console.log('   - hasSymbol:', hasSymbol.value);
            console.log('   - hasDate:', hasDate.value);
            console.log('   - loading:', loading.value);
            
            if (hasSymbol.value && hasDate.value && !loading.value) {
              console.log('   ✓ 条件满足，开始加载订单数据');
              await getOrderbookData();
              console.log('   ✓ 订单数据加载完成');
              
              // 重要：getOrderbookData 会重置 selectTime.value 为 09:30:00.000
              // 需要重新设置为用户输入的时间
              selectTime.value = lockTime;
              console.log('   ✓ 重新设置跳转时间为:', selectTime.value);
            } else {
              console.warn('   ⚠️ 条件不满足，无法加载数据');
            }
            
            // 第六步：等待数据加载完成后，跳转到指定时间
            console.log('📝 [VolumeQueue] 步骤6: 等待数据加载，然后跳转到指定时间');
            setTimeout(() => {
              console.log('   🔄 执行时间跳转');
              console.log('   - 目标时间:', lockTime);
              clickMoveTime(lockTime); // 直接传入时间参数
              console.log('   ✓ 时间跳转命令已执行');
              
              // 第七步：等待时间跳转完成后，执行订单锁定
              console.log('📝 [VolumeQueue] 步骤7: 等待时间跳转完成，然后锁定订单');
              setTimeout(() => {
                console.log('   🔒 开始执行订单锁定');
                console.log('   - 订单ID:', lockByIdValue.value);
                console.log('   - volumeData 是否已加载:', Object.keys(volumeData.value).length > 0);
                
                const lockSuccess = lockOrdersById(true);
                
                if (lockSuccess) {
                  console.log('   ✅ 订单自动锁定成功');
                  createMessage.success('订单已自动锁定并定位');
                } else {
                  console.warn('   ⚠️ 订单锁定失败，可能数据未加载完成');
                  createMessage.warning('订单锁定失败，请手动点击"按ID"按钮');
                }
              }, 1000); // 等待时间跳转完成
            }, 2000); // 等待数据加载完成
            
            // 清除 sessionStorage 中的锁定标记，避免重复处理
            console.log('🧹 [VolumeQueue] 清除 sessionStorage 中的锁定标记');
            sessionStorage.removeItem('volumeQueue_isFromGlobalSearch');
            sessionStorage.removeItem('volumeQueue_autoLock');
            sessionStorage.removeItem('volumeQueue_lockTimestamp');
            sessionStorage.removeItem('volumeQueue_lockOrderId');
            sessionStorage.removeItem('volumeQueue_lockSym');
            sessionStorage.removeItem('volumeQueue_lockDate');
            console.log('   ✓ 锁定标记已清除');
            
            console.log('✅ [VolumeQueue] 自动处理流程设置完成');
            
          } catch (error) {
            console.error('❌ [VolumeQueue] 处理失败:', error);
            console.error('   错误堆栈:', error.stack);
            createMessage.error('处理订单锁定请求失败');
          }
        }, 1500); // 延迟1.5秒确保页面初始化完成
      } else {
        console.log('ℹ️ [VolumeQueue] 未检测到来自 GlobalOrderSearch 的锁定请求');
      }
      
      console.log('🔍 [VolumeQueue] ========== GlobalOrderSearch 锁定请求检查结束 ==========');
    };

    // 组件初始化
    onMounted(async () => {
      console.log('📱 [VolumeQueue] ========== 页面 onMounted 开始 ==========');
      
      // 清除所有 localStorage 数据（每次刷新都清空）
      console.log('🧹 [VolumeQueue] 清除所有 localStorage 数据');
      const keysToRemove = [
        'volumeQueue_selectSym',
        'volumeQueue_selectDate', 
        'volumeQueue_timestamp',
        'volumeQueue_lockOrderId',
        'volumeQueue_isFromGlobalSearch',
        'volumeQueue_autoLock',
        'volumeQueue_orderIndex',
        'volumeQueue_userInputTime'
      ];
      keysToRemove.forEach(key => {
        localStorage.removeItem(key);
        console.log(`   - 已清除: ${key}`);
      });
      console.log('   ✓ localStorage 已清空');
      
      // 清除 Pinia Store 中的锁定数据（防止刷新后自动执行）
      console.log('🧹 [VolumeQueue] 清除 Pinia Store 中的锁定数据');
      orderLockStore.clearLockData();
      console.log('   ✓ Pinia Store 已清除');
      
      // 检查是否有订单锁定数据需要处理（应该总是 false，因为刚清除了）
      const hasLockData = orderLockStore.hasLockData;
      
      if (hasLockData) {
        console.log('✅ [VolumeQueue] 检测到 Pinia 中的订单锁定数据');
        
        // 使用统一的订单锁定处理器和错误处理
        await withOrderLockErrorHandling(async () => {
          // 验证锁定数据
          const validationResult = validateOrderLockData(orderLockStore.lockData);
          if (!validationResult.success) {
            showOrderLockFeedback(validationResult);
            return;
          }
          
          console.log('🔄 [VolumeQueue] 使用Pinia状态管理处理订单锁定');
          
          // 调用统一的订单锁定处理器
          await unifiedOrderLockHandler(validationResult.data);
          
          // 清理Pinia状态中的锁定数据
          orderLockStore.clearLockData();
          
          console.log('✅ [VolumeQueue] 订单锁定处理完成');
        }, '订单锁定流程');
        
      } else {
        // 正常页面加载，恢复用户选择的数据
        console.log('ℹ️ [VolumeQueue] 正常页面加载，恢复用户数据');
        
        await initializePageData();
      }
      
      // 检查是否有来自GlobalOrderSearch的单个订单锁定请求
      await handleGlobalSearchLockRequest();
      
      // 解决aria-hidden警告
      nextTick(() => {
        const activeElement = document.activeElement;
        if (activeElement) {
          const closestAriaHidden = activeElement.closest('[aria-hidden="true"]');
          if (closestAriaHidden) {
            document.body.focus();
            console.log('✓ [VolumeQueue] 已解决焦点问题');
          }
        }
      });
      
      console.log('📱 [VolumeQueue] ========== 页面 onMounted 结束 ==========');
    });
    
    // 初始化页面数据的函数
    const initializePageData = async () => {
      try {
        // 恢复用户选择的数据
        const savedSym = localStorage.getItem('volumeQueue_selectSym');
        const savedDate = localStorage.getItem('volumeQueue_selectDate');
        const savedTime = localStorage.getItem('volumeQueue_timestamp');
        
        if (savedSym) {
          securityType.value = localStorage.getItem('volumeQueue_securityType') || getSecurityType(savedSym);
          selectSym.value = savedSym;
          hasSymbol.value = true;
          console.log('恢复股票代码:', savedSym);
          
          // 加载日期列表
          loading.value = true;
          const params = { sym: savedSym };
          
          const res = await getDateList(params);
          loading.value = false;
          
          if (res.code == 0) {
            datesData.value = res.data.map(item => ({ label: item, value: item }));
            
            // 设置日期和时间
            if (savedDate) {
              selectDate.value = savedDate;
              hasDate.value = true;
              console.log('恢复交易日期:', savedDate);
            }
            
            if (savedTime) {
              selectTime.value = savedTime;
              console.log('恢复时间:', savedTime);
            }
          }
        }
      } catch (error) {
        loading.value = false;
        console.error('初始化页面数据失败:', error);
        createMessage.error('加载页面数据失败，请检查网络连接');
      }
    };

    // 从localStorage恢复selectTime，只有在来自GlobalOrderSearch的跳转时才恢复
    // 否则默认为空字符串，确保用户关闭页面重新进入时时间为空
    const isFromGlobalSearch = localStorage.getItem('globalSearch_orderId') && localStorage.getItem('triggerLockOrder');
    const selectTime = ref(isFromGlobalSearch ? (localStorage.getItem('volumeQueue_timestamp') || '') : '');

    // 格式化时间戳，只显示时分秒
    const formatTimeDisplay = (timestamp) => {
      if (!timestamp) return '';
      // 如果时间戳包含日期部分，提取时分秒部分
      if (timestamp.includes(' ')) {
        return timestamp.split(' ')[1]; // 取空格后的时间部分
      }
      // 如果已经是时分秒格式，直接返回
      return timestamp;
    };

    // 计算属性：用于显示的时间戳（只显示时分秒）
    const displayTime = computed({
      get: () => formatTimeDisplay(selectTime.value),
      set: (value) => {
        // 放宽：输入时不做边界检测，直接存入原始值
        selectTime.value = value;
      }
    });

    // 处理时间输入变化
    
    // 时间格式验证函数
    const isValidTimeFormat = (timeStr) => {
      if (!timeStr) return false;
      
      // 支持多种时间格式：
      // HH:MM:SS.mmm (09:30:00.000)
      // HH:MM:SS (09:30:00)
      // H:MM:SS (9:30:00)
      const timeRegex = /^([0-1]?[0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])(\.\d{1,3})?$/;
      return timeRegex.test(timeStr);
    };
    
    // 时间边界检查函数（使用 Date 对象进行准确比较）
    const checkTimeBoundary = (timeStr) => {
      const minTime = '09:30:00.000';
      const maxTime = '15:00:00.000';
      
      // 先验证格式
      if (!isValidTimeFormat(timeStr)) {
        console.warn('⚠️ 时间格式无效:', timeStr);
        return { valid: false, corrected: minTime, reason: 'format' };
      }
      
      // 使用 Date 对象进行准确的时间比较
      const baseDate = '2000-01-01 ';
      try {
        const inputTime = new Date(baseDate + timeStr);
        const minDateTime = new Date(baseDate + minTime);
        const maxDateTime = new Date(baseDate + maxTime);
        
        // 检查是否为有效的 Date 对象
        if (isNaN(inputTime.getTime())) {
          console.warn('⚠️ 无法解析时间:', timeStr);
          return { valid: false, corrected: minTime, reason: 'parse' };
        }
        
        // 如果输入时间小于最早时间，返回最早时间
        if (inputTime < minDateTime) {
          console.warn('⚠️ 时间早于开盘时间:', timeStr);
          return { valid: false, corrected: minTime, reason: 'early' };
        }
        
        // 如果输入时间大于最晚时间，返回最晚时间
        if (inputTime > maxDateTime) {
          console.warn('⚠️ 时间晚于收盘时间:', timeStr);
          return { valid: false, corrected: maxTime, reason: 'late' };
        }
        
        // 时间在范围内，返回原时间
        return { valid: true, corrected: timeStr, reason: null };
      } catch (error) {
        console.error('❌ 时间边界检查异常:', error);
        return { valid: false, corrected: minTime, reason: 'error' };
      }
    };

    const handleTimeInputChange = (e) => {
      const inputValue = e.target.value;
      // 放宽：变更时不做边界检测，直接更新
      selectTime.value = inputValue;
    };

    // 失焦时再做边界检测与持久化
    const handleTimeBlur = (e) => {
      const raw = e?.target?.value ?? selectTime.value;
      
      // 如果输入为空，不做处理
      if (!raw || raw.trim() === '') {
        localStorage.setItem('volumeQueue_timestamp', '');
        return;
      }
      
      const checkResult = checkTimeBoundary(raw);
      
      if (!checkResult.valid) {
        // 时间无效或超出范围，自动修正并提示用户
        const oldValue = selectTime.value;
        selectTime.value = checkResult.corrected;
        
        // 根据不同的原因给出不同的提示
        let message = '';
        switch (checkResult.reason) {
          case 'format':
            message = `时间格式无效，已自动调整为 ${checkResult.corrected}`;
            break;
          case 'parse':
            message = `无法解析时间，已自动调整为 ${checkResult.corrected}`;
            break;
          case 'early':
            message = `时间早于开盘时间（09:30），已自动调整为 ${checkResult.corrected}`;
            break;
          case 'late':
            message = `时间晚于收盘时间（15:00），已自动调整为 ${checkResult.corrected}`;
            break;
          default:
            message = `时间已自动调整为 ${checkResult.corrected}`;
        }
        
        createMessage.warning(message);
        console.log(`📝 时间自动修正: "${oldValue}" → "${checkResult.corrected}" (原因: ${checkResult.reason})`);
      }
      
      localStorage.setItem('volumeQueue_timestamp', selectTime.value || '');
    };
    
    // 监听selectTime变化并持久化到localStorage
    watch(selectTime, (newValue) => {
      localStorage.setItem('volumeQueue_timestamp', newValue || '');
    });

    // 监听orderIndex变化并持久化到localStorage
    watch(orderIndex, (newValue) => {
      localStorage.setItem('volumeQueue_orderIndex', (newValue || '').toString());
    });
    
    const timesData = ref([]);

    const askIsFullscreen = ref(false);
    const bidIsFullscreen = ref(false);
    const showAsk = ref(true);
    const showBid = ref(true);

    // 搜索相关状态
    const searchValue = ref('');
    const lockByVolumeValue = ref('');
    const lockByIdValue = ref('');
    const lockedOrderIds = ref([]);
    
    // 订单锁定进度状态
    const lockProgress = ref({
      show: false,
      message: '准备锁定订单...',
      detail: '', // 详细信息，显示在进度条下方
      progress: 0,
      status: 'processing', // processing, completed, failed
      currentStep: 0,
      totalSteps: 7
    });
    
    // 订单锁定进度条通知实例
    let lockProgressMessageInstance = null;
    const LOCK_PROGRESS_MESSAGE_KEY = 'order-lock-progress-notification';

    // 初始化进度状态
    const initProgress = ref({
      show: false,
      message: '等待开始初始化...',
      taskId: null,
      progress: 0,
      status: 'initializing'
    });
    
    // 创建订单锁定进度条通知内容（带详细信息）
    const createLockProgressContent = () => {
      const children = [
        // 第一行：进度条和主要信息
        h('div', {
          style: 'display: flex; align-items: center; min-width: 320px;'
        }, [
          h(Progress, {
            percent: lockProgress.value.progress,
            strokeColor: getLockProgressColor(lockProgress.value.status),
            showInfo: false,
            strokeWidth: 6,
            style: 'width: 220px; margin-right: 12px;'
          }),
          h('span', {
            style: 'font-size: 12px; color: #666; white-space: nowrap; min-width: 80px;'
          }, `步骤 ${lockProgress.value.currentStep}/${lockProgress.value.totalSteps} | ${lockProgress.value.message}`)
        ])
      ];
      
      // 第二行：详细信息（如果有）
      if (lockProgress.value.detail) {
        children.push(
          h('div', {
            style: 'margin-top: 6px; font-size: 11px; color: #999; padding-left: 4px;'
          }, lockProgress.value.detail)
        );
      }
      
      return h('div', {
        style: 'display: flex; flex-direction: column;',
        key: `lock-progress-${lockProgress.value.progress}-${Date.now()}`
      }, children);
    };
    
    // 创建持久的订单锁定进度条通知
    const createLockProgressNotification = () => {
      if (lockProgressMessageInstance) {
        return;
      }
      
      createMessage.open({
        content: createLockProgressContent(),
        duration: 0,
        type: 'loading',
        key: LOCK_PROGRESS_MESSAGE_KEY,
        style: {
          marginTop: '10px'
        }
      });
      
      lockProgressMessageInstance = true;
    };
    
    // 更新订单锁定进度条通知内容
    const updateLockProgressNotification = () => {
      if (!lockProgressMessageInstance) {
        createLockProgressNotification();
        return;
      }
      
      const messageType = lockProgress.value.status === 'completed' ? 'success' :
                         lockProgress.value.status === 'failed' ? 'error' : 'loading';
      
      createMessage.open({
        content: createLockProgressContent(),
        duration: 0,
        type: messageType,
        key: LOCK_PROGRESS_MESSAGE_KEY,
        style: {
          marginTop: '10px'
        }
      });
    };
    
    // 关闭订单锁定进度条通知
    const closeLockProgressNotification = () => {
      if (lockProgressMessageInstance) {
        createMessage.destroy(LOCK_PROGRESS_MESSAGE_KEY);
        lockProgressMessageInstance = null;
      }
    };
    
    // 获取订单锁定进度条颜色
    const getLockProgressColor = (status) => {
      switch (status) {
        case 'processing':
          return '#1890ff'; // 蓝色
        case 'completed':
          return '#52c41a'; // 绿色
        case 'failed':
          return '#ff4d4f'; // 红色
        default:
          return '#1890ff';
      }
    };

    // 进度条通知实例状态
    let progressMessageInstance = null;
    const PROGRESS_MESSAGE_KEY = 'orderbook-progress-notification';

    // 创建进度条通知内容
    const createProgressContent = () => {
      return h('div', {
        style: 'display: flex; align-items: center; min-width: 320px;',
        key: `progress-${initProgress.value.progress}-${Date.now()}` // 添加key确保更新
      }, [
        h(Progress, {
          percent: initProgress.value.progress,
          strokeColor: getProgressColor(initProgress.value.status),
          showInfo: false,
          strokeWidth: 6,
          style: 'width: 220px; margin-right: 12px;'
        }),
        h('span', {
          style: 'font-size: 12px; color: #666; white-space: nowrap; min-width: 80px;'
        }, `${initProgress.value.progress}% | ${initProgress.value.message}`)
      ]);
    };

    // 创建持久的进度条通知
    const createProgressNotification = () => {
      // 如果已经有通知实例，直接返回
      if (progressMessageInstance) {
        return;
      }

      // 创建持久的进度通知，使用固定key确保唯一性
      createMessage.open({
        content: createProgressContent(),
        duration: 0, // 不自动关闭
        type: 'loading',
        key: PROGRESS_MESSAGE_KEY, // 使用固定key确保不被其他通知覆盖
        style: {
          marginTop: '10px'
        }
      });

      progressMessageInstance = true; // 标记已创建
    };

    // 更新进度条通知内容
    const updateProgressNotification = () => {
      if (!progressMessageInstance) {
        createProgressNotification();
        return;
      }

      // 使用相同的key更新通知内容，而不是创建新通知
      const messageType = initProgress.value.status === 'completed' ? 'success' :
                         initProgress.value.status === 'failed' ? 'error' : 'loading';

      createMessage.open({
        content: createProgressContent(),
        duration: 0,
        type: messageType,
        key: PROGRESS_MESSAGE_KEY, // 使用相同的key确保更新而不是创建新通知
        style: {
          marginTop: '10px'
        }
      });
    };

    // 关闭进度条通知
    const closeProgressNotification = () => {
      if (progressMessageInstance) {
        createMessage.destroy(PROGRESS_MESSAGE_KEY); // 使用key销毁特定通知
        progressMessageInstance = null;
      }
    };

    // WebSocket 连接实例
    let progressWebSocket = null;

    // 初始化默认的空数据，确保表格始终显示
    const levelData = ref([
      { level: '买一', volume: '', number: '' },
      { level: '买二', volume: '', number: '' },
      { level: '买三', volume: '', number: '' },
      { level: '卖一', volume: '', number: '' },
      { level: '卖二', volume: '', number: '' },
      { level: '卖三', volume: '', number: '' }
    ]);

    const tradeData = ref([
      { level: '买一新增撤单', last_1min: '', last_3s: '', last_500ms: '', last_50ms: '', last_10ms: '' },
      { level: '买一新增挂单', last_1min: '', last_3s: '', last_500ms: '', last_50ms: '', last_10ms: '' },
      { level: '买一新增成交', last_1min: '', last_3s: '', last_500ms: '', last_50ms: '', last_10ms: '' },
      { level: '卖一新增撤单', last_1min: '', last_3s: '', last_500ms: '', last_50ms: '', last_10ms: '' },
      { level: '卖一新增挂单', last_1min: '', last_3s: '', last_500ms: '', last_50ms: '', last_10ms: '' },
      { level: '卖一新增成交', last_1min: '', last_3s: '', last_500ms: '', last_50ms: '', last_10ms: '' }
    ]);

    // 市场数据相关变量
    const marketData = ref({
      bid_create_count: 0,
      bid_cancel_count: 0,
      bid_traded_count: 0,
      ask_create_count: 0,
      ask_cancel_count: 0,
      ask_traded_count: 0
    });

    const level_columns = [
      {
        title: '档位',
        dataIndex: 'level',
        key: 'level',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.level - b.level,
        align: 'center',
      },
      {
        title: '总数量',
        dataIndex: 'volume',
        key: 'volume',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.volume - b.volume,
        align: 'center',
      },
      {
        title: '总订单数',
        dataIndex: 'number',
        key: 'number',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.number - b.number,
        align: 'center',
      },
    ]

    const trader_columns = [
      {
        title: '档位',
        dataIndex: 'level',
        key: 'level',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.level - b.level,
        align: 'center',
      },
      {
        title: '过去一分钟',
        dataIndex: 'last_1min',
        key: 'last_1min',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.last_1min - b.last_1min,
        align: 'center',
      },
      {
        title: '过去3s',
        dataIndex: 'last_3s',
        key: 'last_3s',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.last_3s - b.last_3s,
        align: 'center',
      },
      {
        title: '过去500ms',
        dataIndex: 'last_500ms',
        key: 'last_500ms',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.last_500ms - b.last_500ms,
        align: 'center',
      },
      {
        title: '过去50ms',
        dataIndex: 'last_50ms',
        key: 'last_50ms',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.last_50ms - b.last_50ms,
        align: 'center',
      },
      {
        title: '过去10ms',
        dataIndex: 'last_10ms',
        key: 'last_10ms',
        width: 90,
        className: 'header-transaction-amount',
        sorter: (a, b) => a.last_10ms - b.last_10ms,
        align: 'center',
      },
    ]

    const isButtonDisabled = computed(() => {
      return Object.keys(volumeData.value).length === 0;
    });

    const handleSecurityTypeChange = (type) => {
      securityType.value = type;
      localStorage.setItem('volumeQueue_securityType', type);

      // 类型切换后清空旧代码及其关联日期，避免股票代码和基金代码混用。
      selectSym.value = '';
      hasSymbol.value = false;
      selectDate.value = '';
      datesData.value = [];
      hasDate.value = false;
      volumeData.value = {};
      isETF.value = type === 'fund';
      localStorage.removeItem('volumeQueue_selectSym');
      localStorage.removeItem('volumeQueue_selectDate');
      localStorage.removeItem('volumeQueue_timestamp');
    };

    const symFilterOption = (input, option) => {
      return option.value.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    };

    const selectSymItem = (item) => {
      selectSym.value = item
      securityType.value = getSecurityType(item)
      localStorage.setItem('volumeQueue_securityType', securityType.value)
      localStorage.setItem('volumeQueue_selectSym', item)
      hasSymbol.value = true
      loading.value = true
      let params = {
        sym: item,
      }
      getDateList(params).then((res) => {
        loading.value = false
        if (res.code == 0) {
          datesData.value = []
          res.data.forEach((item) => {
            datesData.value.push({ label: item, value: item })
          })
          if (res.message) {
            createMessage.success(res.message)
          }
        } else {
            messageText.value = res.msg
            createMessage.error(res.message || res.msg || '获取日期列表失败')
          }
      }).catch((error) => {
        loading.value = false
        createMessage.error('网络请求失败，请检查网络连接')
      })
    }

    const dateFilterOption = (input, option) => {
      return option.value.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    };

    const selectDateItem = async (item) => {
      selectDate.value = item
      localStorage.setItem('volumeQueue_selectDate', item)
      hasDate.value = true
    }

    // 存储用户输入的搜索内容
    const symSearchValue = ref('');
    const dateSearchValue = ref('');

    // 存储用户的最后有效输入
    const symLastValidInput = ref('');
    const dateLastValidInput = ref('');

    // 处理股票代码焦点事件
    const handleSymFocus = () => {
      // 焦点事件处理
    }

    // 处理股票代码输入事件
    const handleSymInput = (event) => {
      // 输入事件处理
    }

    // 处理股票代码搜索事件
    const handleSymSearch = (value) => {
      symSearchValue.value = value;

      // 如果有有效输入（非空），保存为最后有效输入
      if (value && value.trim() !== '') {
        symLastValidInput.value = value.trim();
      }
    }

    // 处理日期搜索事件
    const handleDateSearch = (value) => {
      dateSearchValue.value = value;

      // 如果有有效输入（非空），保存为最后有效输入
      if (value && value.trim() !== '') {
        dateLastValidInput.value = value.trim();
      }
    }

    // 处理股票代码失焦事件
    const handleSymBlur = () => {
      // 使用setTimeout确保在blur事件后执行，避免与Select组件内部逻辑冲突
      setTimeout(() => {
        // 优先使用最后有效输入，然后是当前搜索值，最后是选中值
        const searchInput = symLastValidInput.value || symSearchValue.value || selectSym.value;

        if (searchInput && searchInput.trim() !== '') {
          const currentValue = searchInput.trim();

          // 先查找完全匹配的选项
          let matchingOption = filteredSymsData.value.find(option =>
            option.value.toLowerCase() === currentValue.toLowerCase()
          );

          // 如果没有完全匹配，查找包含输入内容的选项
          if (!matchingOption) {
            matchingOption = filteredSymsData.value.find(option =>
              option.value.toLowerCase().includes(currentValue.toLowerCase())
            );
          }

          // 如果找到匹配项，则选择它
          if (matchingOption) {
            selectSym.value = matchingOption.value;
            if (!hasSymbol.value) {
              selectSymItem(matchingOption.value);
            }
          } else {
            // 如果没有找到匹配项，清空输入并提示用户
            selectSym.value = '';
            symSearchValue.value = '';
            symLastValidInput.value = '';
            createMessage.warning(`未找到匹配的${securityType.value === 'fund' ? '基金' : '股票'}代码: ${currentValue}`);
          }
        }

        // 清空搜索值和最后有效输入
        symSearchValue.value = '';
        symLastValidInput.value = '';
      }, 100);
    }

    // 处理日期失焦事件
    const handleDateBlur = () => {
      // 使用setTimeout确保在blur事件后执行，避免与Select组件内部逻辑冲突
      setTimeout(() => {
        // 优先使用最后有效输入，然后是当前搜索值，最后是选中值
        const searchInput = dateLastValidInput.value || dateSearchValue.value || selectDate.value;

        if (searchInput && searchInput.trim() !== '') {
          const currentValue = searchInput.trim();

          // 先查找完全匹配的选项
          let matchingOption = datesData.value.find(option =>
            option.value.toLowerCase() === currentValue.toLowerCase()
          );

          // 如果没有完全匹配，查找包含输入内容的选项
          if (!matchingOption) {
            matchingOption = datesData.value.find(option =>
              option.value.toLowerCase().includes(currentValue.toLowerCase())
            );
          }

          // 如果找到匹配项，则选择它
          if (matchingOption) {
            selectDate.value = matchingOption.value;
            if (!hasDate.value) {
              selectDateItem(matchingOption.value);
            }
          } else {
            // 如果没有找到匹配项，清空输入并提示用户
            selectDate.value = '';
            dateSearchValue.value = '';
            createMessage.warning(`未找到匹配的日期: ${currentValue}`);
          }
        }

        // 清空搜索值
        dateSearchValue.value = '';
      }, 100);
    }

    const timeFilterOption = (input, option) => {
      // return option.value.toLowerCase().indexOf(input.toLowerCase()) >= 0;
      return option.value.startsWith(input);
    }

    const clickMoveTime = (targetTime = null) => {
      // 从localStorage读取存储的单号和日期
      const savedSym = localStorage.getItem('volumeQueue_selectSym');
      const savedDate = localStorage.getItem('volumeQueue_selectDate');
      
      // 优先使用localStorage中的值
      const finalSym = savedSym || selectSym.value;
      const finalDate = savedDate || selectDate.value;
      
      // 如果有存储的单号和日期，更新当前选择
      if (finalSym && finalDate) {
        selectSym.value = finalSym;
        hasSymbol.value = true;
        selectDate.value = finalDate;
        hasDate.value = true;
      } else if (finalSym || finalDate) {
        // 如果只有其中一个值，提示用户需要完整选择
        createMessage.warning('请完整选择单号和日期');
        return;
      } else {
        // 如果没有存储的值，提示用户需要先选择
        createMessage.warning('请先选择单号和日期');
        return;
      }

      // 修复：检查 targetTime 是否为事件对象
      // 如果是事件对象（有 isTrusted 属性），则忽略它
      let inputTime;
      if (targetTime && typeof targetTime === 'object' && 'isTrusted' in targetTime) {
        // 这是一个事件对象，使用 selectTime.value
        inputTime = selectTime.value;
        console.log('clickMoveTime: 检测到事件对象，使用 selectTime.value:', inputTime);
      } else if (targetTime && typeof targetTime === 'string') {
        // 这是一个有效的时间字符串参数
        inputTime = targetTime;
        console.log('clickMoveTime: 使用传入的时间参数:', inputTime);
      } else {
        // 没有参数或参数无效，使用 selectTime.value
        inputTime = selectTime.value;
        console.log('clickMoveTime: 使用 selectTime.value:', inputTime);
      }
      
      // 验证时间是否为空
      if (!inputTime || inputTime.trim() === '') {
        createMessage.warning('请输入跳转时间');
        return;
      }
      
      // 不做边界检查，直接使用用户输入的时间
      // 执行完整的数据处理逻辑，传递第四个参数表示是时间跳转
      processVolumeData(inputTime, false, false, true);
    }

    const processVolumeData = (timeValue, skipProgressUpdate = false, isInitialLoad = false, isTimeJump = false) => {
      loading.value = true
      let params = {
        sym: selectSym.value,
        date: selectDate.value,
        time: timeValue
      }
      getVolumeDataByTime(params).then((res) => {
        if (res.code == 0 && res.data && res.data.snapshot) {
          // 更新 isETF 状态
          isETF.value = res.data.is_ETF || false;

          // 处理volumeData - 从snapshot中提取需要的数据
          const snapshot = res.data.snapshot;
          const levels = snapshot.levels || {};

          // 转换orders数组为表格数据格式的函数
          const transformOrdersToTableData = (orders, levelPrice) => {
            if (!orders || orders.length === 0) {
              return { orders: [], data: [[], []] };
            }

            // 创建包含所有订单数据的行，不限制数量
            const row = {};

            // 将订单数据填入对应的格子中，每个订单占用一个格子
            orders.forEach((order, index) => {
              const colKey = `v${index + 1}`;
              row[colKey] = order.remaining_volume || '';
              // 将订单详细信息作为属性存储
              row[`${colKey}_order_id`] = order.order_id || '';
              row[`${colKey}_order_local_id`] = order.order_local_id || '';
              row[`${colKey}_direction`] = order.direction || '';
              row[`${colKey}_price`] = levelPrice || order.price || '';
              row[`${colKey}_create_time`] = order.create_time || '';
            });

            const result = {
              orders: orders, // 保存原始订单数据用于搜索
              data: [[row], [row]] // VolumeDataTable期望的格式是二维数组，[0]用于普通模式，[1]用于全屏模式
            };
            return result;
          };

          // 构建volumeData格式
          volumeData.value = {
            datetime: res.data.time || '',
            is_ETF: isETF.value,
            ask1: transformOrdersToTableData(levels.ask1?.orders || [], levels.ask1?.price),
            ask1_price: levels.ask1?.price || 0,
            ask2: transformOrdersToTableData(levels.ask2?.orders || [], levels.ask2?.price),
            ask2_price: levels.ask2?.price || 0,
            ask3: transformOrdersToTableData(levels.ask3?.orders || [], levels.ask3?.price),
            ask3_price: levels.ask3?.price || 0,
            bid1: transformOrdersToTableData(levels.bid1?.orders || [], levels.bid1?.price),
            bid1_price: levels.bid1?.price || 0,
            bid2: transformOrdersToTableData(levels.bid2?.orders || [], levels.bid2?.price),
            bid2_price: levels.bid2?.price || 0,
            bid3: transformOrdersToTableData(levels.bid3?.orders || [], levels.bid3?.price),
            bid3_price: levels.bid3?.price || 0
          };

          // 处理levelDataArray
          const levelDataArray = [];
          Object.keys(levels).forEach(levelKey => {
            if (levels[levelKey]) {
              const levelData = levels[levelKey];
              const total_volume = levelData.total_volume || 0;
              const order_count = levelData.order_count || 0;

              // 将英文档位转换为中文
              let chineseLevel = levelKey;
              if (levelKey === 'bid1') chineseLevel = '买一';
              else if (levelKey === 'bid2') chineseLevel = '买二';
              else if (levelKey === 'bid3') chineseLevel = '买三';
              else if (levelKey === 'ask1') chineseLevel = '卖一';
              else if (levelKey === 'ask2') chineseLevel = '卖二';
              else if (levelKey === 'ask3') chineseLevel = '卖三';

              levelDataArray.push({
                level: chineseLevel,
                volume: total_volume,
                number: order_count
              });
            }
          });
          levelData.value = levelDataArray;

          // 保持 tradeData 的 level 列不变，不重新生成数组
          // tradeData 将通过 updateMarketData() 函数单独更新数据列，level 列保持固定值

          // 更新时间和订单索引 - 优先使用snapshot中的timestamp（确保时间格式为HH:mm:ss.SSS）
          const rawTime = snapshot.timestamp || res.data.time || timeValue;
          const extractedTime = extractTimeFromTimestamp(rawTime);

          // 只有当提取的时间有效时才更新selectTime，避免时间被清空
          if (extractedTime && extractedTime.trim() !== '') {
            let finalTime = extractedTime;

            if (isInitialLoad) {
              finalTime = timeValue;
            }

            // 应用边界检测
            const checkResult = checkTimeBoundary(finalTime);
            selectTime.value = checkResult.corrected;
            localStorage.setItem('volumeQueue_timestamp', checkResult.corrected);

            // 时间跳转时，若实际快照时间与输入时间不一致，提示用户
            if (isTimeJump && timeValue && extractedTime && extractedTime !== timeValue) {
              createMessage.warning(`目标时间 ${timeValue} 无对应快照，已跳转到 ${extractedTime}`);
            }
          }

          // 从snapshot中提取snapshot_id更新orderIndex
          orderIndex.value = snapshot.snapshot_id || res.data.orderindex || 0;
          // 从snapshot中提取change_index更新changeIndex
          changeIndex.value = snapshot.change_index || 0;
          // 从snapshot中提取snapshot_id更新snapshotId
          snapshotId.value = snapshot.snapshot_id || 0;
          localStorage.setItem('volumeQueue_orderIndex', (snapshot.snapshot_id || res.data.orderindex || 0).toString());
          messageText.value = '查询成功'
          
          // 如果订单锁定进度条正在显示，更新进度条信息；否则显示独立通知
          if (lockProgress.value.show) {
            lockProgress.value.detail = res.message || '快照数据加载成功';
            updateLockProgressNotification();
          } else {
            // 改进：显示实际跳转的时间，而不是后端返回的消息
            if (isTimeJump) {
              const displayTimeStr = selectTime.value || timeValue;
              createMessage.success(`已跳转到时间 ${displayTimeStr}`);
            } else {
              createMessage.success(res.message || '数据加载成功');
            }
          }

          // 更新市场数据
          updateMarketData();

          // 数据加载成功，停止WebSocket监听
          if (progressWebSocket) {
            progressWebSocket.stopListening();
            progressWebSocket = null;
          }

          // 更新进度条状态并隐藏（只有在显示进度时才执行）
          if (!skipProgressUpdate && initProgress.value.show) {
            initProgress.value.progress = 100;
            initProgress.value.message = '数据加载完成';
            initProgress.value.status = 'completed';

            // 更新为完成状态
            updateProgressNotification();

            setTimeout(() => {
              closeProgressNotification();
              initProgress.value.show = false;
            }, 1500);
          }

        } else {
          messageText.value = res.message || '查询失败'
          createMessage.error(res.message || '查询数据失败')

          // 数据加载失败，也停止WebSocket监听
          if (progressWebSocket) {
            progressWebSocket.stopListening();
            progressWebSocket = null;
          }

          // 隐藏进度条（只有在显示进度时才执行）
          if (!skipProgressUpdate && initProgress.value.show) {
            closeProgressNotification();
            initProgress.value.show = false;
          }
        }
        loading.value = false
      }).catch((error) => {
        loading.value = false
        createMessage.error('网络请求失败，请检查网络连接')

        // 网络请求失败，也停止WebSocket监听
        if (progressWebSocket) {
          progressWebSocket.stopListening();
          progressWebSocket = null;
        }

        // 隐藏进度条（只有在显示进度时才执行）
        if (!skipProgressUpdate && initProgress.value.show) {
          closeProgressNotification();
          initProgress.value.show = false;
        }
      })
    }

    const getOrderbookData = async () => {
      // 首先调用初始化任务API
      try {
        initProgress.value.show = true;
        initProgress.value.message = '正在初始化TradeBook...';
        initProgress.value.progress = 0;

        // 创建进度条通知
        createProgressNotification();

        const initParams = {
          sym: selectSym.value,
          date: selectDate.value
        };

        const initResult = await initTradeBook(initParams);

        if (initResult.code === 0) {
          if (initResult.data.status === 'ready') {
            // TradeBook已存在且可用，直接进行数据加载
            createMessage.success(initResult.data.message || 'TradeBook已准备就绪');
            closeProgressNotification();
            initProgress.value.show = false;

            // 直接开始数据加载，不显示初始化进度
            proceedWithDataLoading(true);
          } else if (initResult.data.status === 'initializing') {
            // 需要初始化，显示进度
            initProgress.value.taskId = initResult.data.task_id;
            initProgress.value.message = initResult.data.message || '正在初始化...';
            initProgress.value.progress = 0;
            initProgress.value.status = 'initializing';
            initProgress.value.show = true;

            // 更新进度条通知
            updateProgressNotification();

            createMessage.info('初始化任务已创建，正在监听进度...');

            // 启动WebSocket进度监听
            await startProgressListening(initResult.data.task_id);
          }
        } else {
          createMessage.error(initResult.message || '初始化任务失败');
          closeProgressNotification();
          initProgress.value.show = false;
          return; // 初始化失败时不继续执行后续逻辑
        }
      } catch (error) {
        console.error('❌ 初始化TradeBook错误详情:', {
          error: error.message || error,
          stack: error.stack,
          params: initParams,
          timestamp: new Date().toISOString()
        });

        let errorMessage = '初始化TradeBook失败';
        if (error.message?.includes('NetworkError') ||
            error.message?.includes('fetch') ||
            error.message?.includes('Connection refused')) {
          errorMessage = '无法连接到服务器，请检查服务器状态';
        } else if (error.message?.includes('timeout')) {
          errorMessage = '请求超时，服务器可能正在处理大量数据';
        } else if (error.message) {
          errorMessage = `初始化失败: ${error.message}`;
        }

        createMessage.error(errorMessage);
        closeProgressNotification();
        initProgress.value.show = false;
        return; // 初始化失败时不继续执行后续逻辑
      }
    };

    // 分离的数据加载逻辑
    const proceedWithDataLoading = (skipProgressUpdate = false) => {

      // 开始按钮默认使用9:30:00.000时间戳
      const defaultTime = '09:30:00.000';
      selectTime.value = defaultTime;

      // 持久化更新的默认时间
      localStorage.setItem('volumeQueue_timestamp', defaultTime);

      // 只有在需要时才更新进度条消息
      if (!skipProgressUpdate && initProgress.value.show) {
        initProgress.value.message = '正在加载数据...';
        updateProgressNotification();
      }

      processVolumeData(defaultTime, skipProgressUpdate, true); // 传递第三个参数表示是初始化调用

      // 市场数据将通过 processVolumeData() 中调用的 updateMarketData() 函数自动获取和更新
    }



    const getStaticData = () => {
      loading.value = true
      getSymList().then((res) => {
        loading.value = false
        if (res.code == 0) {
          symsData.value = []
          res.data.forEach(item => {
            symsData.value.push(toSymbolOption(item))
          })
          if (res.message) {
            createMessage.success(res.message)
          }
        } else {
            messageText.value = res.message
            createMessage.error(res.message || '获取股票列表失败')
          }
      }).catch((error) => {
        loading.value = false
        createMessage.error('网络请求失败，请检查网络连接')
      })
    }

    getStaticData()

    const moveTimes = async (intevel) => {
      // 解析当前时间
      const currentTime = selectTime.value;
      const [hours, minutes, seconds] = currentTime.split(':');
      const [sec, ms] = seconds.split('.');

      // 转换为毫秒
      let totalMs = parseInt(hours) * 3600000 + parseInt(minutes) * 60000 + parseInt(sec) * 1000 + parseInt(ms || 0);

      // 添加时间间隔
      totalMs += intevel;

      // 确保时间在交易时间范围内 (09:30:00.000 - 15:00:00.000)
      const minTime = 9 * 3600000 + 30 * 60000; // 09:30:00.000
      const maxTime = 15 * 3600000; // 15:00:00.000

      if (totalMs < minTime) totalMs = minTime;
      if (totalMs > maxTime) totalMs = maxTime;

      const formatTime = (msValue) => {
        const h = Math.floor(msValue / 3600000);
        const m = Math.floor((msValue % 3600000) / 60000);
        const s = Math.floor((msValue % 60000) / 1000);
        const mm = msValue % 1000;
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}.${mm.toString().padStart(3, '0')}`;
      };

      // 格式化时间字符串
      const newTime = formatTime(totalMs);

      // 更新时间
      selectTime.value = newTime;
      localStorage.setItem('volumeQueue_timestamp', newTime);

      loading.value = true;

      try {
        const stepMs = Math.abs(intevel) <= 50 ? intevel : (intevel > 0 ? 50 : -50);
        const maxSteps = 200; // 最多推进 200 * 50ms = 10s
        let attempt = 0;
        let queryMs = totalMs;
        let lastRes = null;

        while (attempt < maxSteps) {
          const queryTime = formatTime(queryMs);
          const params = { sym: selectSym.value, date: selectDate.value, time: queryTime };
          const res = await getVolumeDataByTime(params);
          lastRes = res;

          if (res.code == 0 && res.data && res.data.snapshot) {
            const snapshot = res.data.snapshot;
            const rawSnapshotTime = snapshot.timestamp || res.data.time || '';
            const returnedTime = extractTimeFromTimestamp(rawSnapshotTime);

            // 找到不同时间戳的快照，停止继续尝试
            if (returnedTime !== currentTime) {
              updateVolumeDataFromSnapshot(snapshot, res.data);
              updateMarketData();

              if (returnedTime !== queryTime) {
                createMessage.info(`目标时间 ${queryTime} 无新快照，已自动跳转到 ${returnedTime}`);
              } else {
                createMessage.success(`时间移动成功：${intevel > 0 ? '向前' : '向后'}移动${Math.abs(intevel) >= 1000 ? `${Math.abs(intevel) / 1000}秒` : `${Math.abs(intevel)}毫秒`}`);
              }

              loading.value = false;
              return;
            }
          } else {
            break;
          }

          queryMs += stepMs;
          if (queryMs < minTime || queryMs > maxTime) {
            break;
          }
          attempt += 1;
        }

        // 未能找到不同时间戳的快照
        if (lastRes && lastRes.code == 0 && lastRes.data && lastRes.data.snapshot) {
          updateVolumeDataFromSnapshot(lastRes.data.snapshot, lastRes.data);
          updateMarketData();
        }
        createMessage.warning('当前时间附近没有新的时间戳快照，已保持原快照');
      } catch (error) {
        createMessage.error('网络请求失败，请检查网络连接');
        selectTime.value = newTime;
        localStorage.setItem('volumeQueue_timestamp', newTime);
      } finally {
        loading.value = false;
      }
    }

    // 辅助函数：将时间字符串转换为毫秒
    const parseTimeToMs = (timeStr) => {
      if (!timeStr) return 0;
      const [hours, minutes, seconds] = timeStr.split(':');
      const [sec, ms] = seconds.split('.');
      return parseInt(hours) * 3600000 + parseInt(minutes) * 60000 + parseInt(sec) * 1000 + parseInt(ms || 0);
    }

    // 辅助函数：从完整时间戳中提取时间部分（HH:mm:ss.SSS格式）
    const extractTimeFromTimestamp = (timestamp) => {
      if (!timestamp) return '';
      // 如果已经是时间格式（HH:mm:ss.SSS），直接返回
      if (timestamp.match(/^\d{2}:\d{2}:\d{2}\.\d{3}$/)) {
        return timestamp;
      }
      // 如果包含日期（如：2025-08-01 09:30:00.050），提取时间部分
      if (timestamp.includes(' ')) {
        return timestamp.split(' ')[1] || '';
      }
      // 其他情况直接返回
      return timestamp;
    }

    // 辅助函数：将Date对象格式化为HH:mm:ss.SSS格式，保持毫秒精度
    const formatTimeWithMilliseconds = (date) => {
      const hours = date.getHours().toString().padStart(2, '0');
      const minutes = date.getMinutes().toString().padStart(2, '0');
      const seconds = date.getSeconds().toString().padStart(2, '0');
      const milliseconds = date.getMilliseconds().toString().padStart(3, '0');
      return `${hours}:${minutes}:${seconds}.${milliseconds}`;
    }



    // 辅助函数：从snapshot更新volumeData（提取公共逻辑）
    const updateVolumeDataFromSnapshot = (snapshot, responseData) => {
      const levels = snapshot.levels || {};

      // 转换orders数组为表格数据格式的函数
      const transformOrdersToTableData = (orders, levelPrice) => {
        if (!orders || orders.length === 0) {
          return { orders: [], data: [[], []] };
        }

        const row = {};
        orders.forEach((order, index) => {
          const colKey = `v${index + 1}`;
          row[colKey] = order.remaining_volume || '';
          row[`${colKey}_order_id`] = order.order_id || '';
          row[`${colKey}_order_local_id`] = order.order_local_id || '';
          row[`${colKey}_direction`] = order.direction || '';
          row[`${colKey}_price`] = levelPrice || order.price || '';
          row[`${colKey}_create_time`] = order.create_time || '';
        });

        return {
          orders: orders,
          data: [[row], [row]]
        };
      };

      // 构建volumeData格式
      volumeData.value = {
        datetime: snapshot.timestamp || responseData.time || '',
        is_ETF: responseData.is_ETF !== undefined ? responseData.is_ETF : isETF.value,
        ask1: transformOrdersToTableData(levels.ask1?.orders || [], levels.ask1?.price),
        ask1_price: levels.ask1?.price || 0,
        ask2: transformOrdersToTableData(levels.ask2?.orders || [], levels.ask2?.price),
        ask2_price: levels.ask2?.price || 0,
        ask3: transformOrdersToTableData(levels.ask3?.orders || [], levels.ask3?.price),
        ask3_price: levels.ask3?.price || 0,
        bid1: transformOrdersToTableData(levels.bid1?.orders || [], levels.bid1?.price),
        bid1_price: levels.bid1?.price || 0,
        bid2: transformOrdersToTableData(levels.bid2?.orders || [], levels.bid2?.price),
        bid2_price: levels.bid2?.price || 0,
        bid3: transformOrdersToTableData(levels.bid3?.orders || [], levels.bid3?.price),
        bid3_price: levels.bid3?.price || 0
      };

      // 处理levelDataArray
      const levelDataArray = [];
      Object.keys(levels).forEach(levelKey => {
        if (levels[levelKey]) {
          const levelData = levels[levelKey];
          const total_volume = levelData.total_volume || 0;
          const order_count = levelData.order_count || 0;

          let chineseLevel = levelKey;
          if (levelKey === 'bid1') chineseLevel = '买一';
          else if (levelKey === 'bid2') chineseLevel = '买二';
          else if (levelKey === 'bid3') chineseLevel = '买三';
          else if (levelKey === 'ask1') chineseLevel = '卖一';
          else if (levelKey === 'ask2') chineseLevel = '卖二';
          else if (levelKey === 'ask3') chineseLevel = '卖三';

          levelDataArray.push({
            level: chineseLevel,
            volume: total_volume,
            number: order_count
          });
        }
      });
      levelData.value = levelDataArray;

      // 保持 tradeData 的 level 列不变，不重新生成数组
      // tradeData 将通过 updateMarketData() 函数单独更新数据列，level 列保持固定值

      // 更新时间和订单索引（确保时间格式为HH:mm:ss.SSS）
      const rawTime = snapshot.timestamp || responseData.time || '';
      const extractedTime = extractTimeFromTimestamp(rawTime);

      // 只有当提取的时间有效时才更新selectTime，避免边界情况下时间被清空
      if (extractedTime && extractedTime.trim() !== '') {
        // 应用边界检测
        const checkResult = checkTimeBoundary(extractedTime);
        selectTime.value = checkResult.corrected;
        // 持久化更新的值
        localStorage.setItem('volumeQueue_timestamp', checkResult.corrected);
      }

      orderIndex.value = snapshot.snapshot_id || responseData.orderindex || 0;
      changeIndex.value = snapshot.change_index || 0;
      snapshotId.value = snapshot.snapshot_id || 0;

      localStorage.setItem('volumeQueue_orderIndex', orderIndex.value.toString());
    }

    const moveticks = (intevel) => {
      let newChangeIndex = changeIndex.value + intevel
      loading.value = true
      let params = {
        sym: selectSym.value,
        date: selectDate.value,
        index: newChangeIndex  // 使用index参数传递change_index
      }

      getSnapshotByIndex(params).then((res) => {
        if (res.code == 0 && res.data && res.data.snapshot) {
          // 使用与processVolumeData相同的数据处理逻辑
          const snapshot = res.data.snapshot;
          const levels = snapshot.levels || {};

          // 转换orders数组为表格数据格式的函数（与processVolumeData中的函数相同）
          const transformOrdersToTableData = (orders, levelPrice) => {
            if (!orders || orders.length === 0) {
              return { orders: [], data: [[], []] };
            }

            // 创建包含所有订单数据的行，不限制数量
            const row = {};

            // 将订单数据填入对应的格子中，每个订单占用一个格子
            orders.forEach((order, index) => {
              const colKey = `v${index + 1}`;
              row[colKey] = order.remaining_volume || '';
              // 将订单详细信息作为属性存储
              row[`${colKey}_order_id`] = order.order_id || '';
              row[`${colKey}_order_local_id`] = order.order_local_id || '';
              row[`${colKey}_direction`] = order.direction || '';
              row[`${colKey}_price`] = levelPrice || order.price || '';
              row[`${colKey}_create_time`] = order.create_time || '';
            });

            const result = {
              orders: orders, // 保存原始订单数据用于搜索
              data: [[row], [row]] // VolumeDataTable期望的格式是二维数组，[0]用于普通模式，[1]用于全屏模式
            };
            return result;
          };

          // 构建volumeData格式（与processVolumeData相同）
          volumeData.value = {
            datetime: snapshot.timestamp || res.data.time || '',
            is_ETF: res.data.is_ETF !== undefined ? res.data.is_ETF : isETF.value,
            ask1: transformOrdersToTableData(levels.ask1?.orders || [], levels.ask1?.price),
            ask1_price: levels.ask1?.price || 0,
            ask2: transformOrdersToTableData(levels.ask2?.orders || [], levels.ask2?.price),
            ask2_price: levels.ask2?.price || 0,
            ask3: transformOrdersToTableData(levels.ask3?.orders || [], levels.ask3?.price),
            ask3_price: levels.ask3?.price || 0,
            bid1: transformOrdersToTableData(levels.bid1?.orders || [], levels.bid1?.price),
            bid1_price: levels.bid1?.price || 0,
            bid2: transformOrdersToTableData(levels.bid2?.orders || [], levels.bid2?.price),
            bid2_price: levels.bid2?.price || 0,
            bid3: transformOrdersToTableData(levels.bid3?.orders || [], levels.bid3?.price),
            bid3_price: levels.bid3?.price || 0
          };

          // 处理levelDataArray
          const levelDataArray = [];
          Object.keys(levels).forEach(levelKey => {
            if (levels[levelKey]) {
              const levelData = levels[levelKey];
              const total_volume = levelData.total_volume || 0;
              const order_count = levelData.order_count || 0;

              // 将英文档位转换为中文
              let chineseLevel = levelKey;
              if (levelKey === 'bid1') chineseLevel = '买一';
              else if (levelKey === 'bid2') chineseLevel = '买二';
              else if (levelKey === 'bid3') chineseLevel = '买三';
              else if (levelKey === 'ask1') chineseLevel = '卖一';
              else if (levelKey === 'ask2') chineseLevel = '卖二';
              else if (levelKey === 'ask3') chineseLevel = '卖三';

              levelDataArray.push({
                level: chineseLevel,
                volume: total_volume,
                number: order_count
              });
            }
          });
          levelData.value = levelDataArray;

          // 保持 tradeData 的 level 列不变，不重新生成数组
          // tradeData 将通过 updateMarketData() 函数单独更新数据列，level 列保持固定值

          // 更新时间和订单索引 - 优先使用snapshot中的timestamp（确保时间格式为HH:mm:ss.SSS）
          const rawTime = snapshot.timestamp || res.data.time || '';
          const extractedTime = extractTimeFromTimestamp(rawTime);

          // 只有当提取的时间有效时才更新selectTime，避免时间被清空
          if (extractedTime && extractedTime.trim() !== '') {
            // 应用边界检测
            const checkResult = checkTimeBoundary(extractedTime);
            selectTime.value = checkResult.corrected;
            localStorage.setItem('volumeQueue_timestamp', checkResult.corrected);
          }

          // 更新change_index为新的值
          changeIndex.value = newChangeIndex;
          // 从snapshot中提取orderIndex和snapshotId
          orderIndex.value = snapshot.snapshot_id || res.data.orderindex || 0;
          snapshotId.value = snapshot.snapshot_id || 0;
          localStorage.setItem('volumeQueue_orderIndex', orderIndex.value.toString());

          // 计算移动方向和数量
          const direction = intevel > 0 ? '向前' : '向后';
          const count = Math.abs(intevel);
          createMessage.success(`订单移动成功：${direction}移动${count}个订单`);

          // 更新市场数据
          updateMarketData();
        } else {
          createMessage.error(res.message || '移动订单失败');
        }
        loading.value = false;
      }).catch((error) => {
        loading.value = false;
        createMessage.error('网络请求失败，请检查网络连接');
      });
    }

    const showHideTable = (detection) => {
      if (detection == 'ask') {
        if (askIsFullscreen.value) {
          askIsFullscreen.value = false
          showAsk.value = true
          showBid.value = true
        } else {
          askIsFullscreen.value = true
          showAsk.value = true
          showBid.value = false
        }
      } else {
        if (bidIsFullscreen.value) {
          bidIsFullscreen.value = false
          showAsk.value = true
          showBid.value = true
        } else {
          bidIsFullscreen.value = true
          showAsk.value = false
          showBid.value = true
        }
      }
    }

    // 按数量锁定订单逻辑函数
     const lockOrdersByVolume = () => {
       if (!lockByVolumeValue.value.trim()) {
         createMessage.warning('请输入remaining volume数值');
         return;
       }

       const searchNum = parseFloat(lockByVolumeValue.value.trim());
       if (isNaN(searchNum)) {
         createMessage.warning('请输入有效的数字');
         return;
       }

       const foundOrderIds = [];

       // 遍历所有volumeData中的订单数据
       Object.keys(volumeData.value).forEach(key => {
         if (key.includes('ask') || key.includes('bid')) {
           const data = volumeData.value[key];
           if (data && data.data && data.data[0] && data.data[0][0]) {
             const rowData = data.data[0][0];
             // 遍历所有v1, v2, v3...列
              for (let i = 1; i <= 10000; i++) {
                const volumeKey = `v${i}`;
                const orderLocalIdKey = `${volumeKey}_order_local_id`;
                if (rowData[volumeKey] === searchNum && rowData[orderLocalIdKey]) {
                  foundOrderIds.push(rowData[orderLocalIdKey]);
                }
              }
           }
         }
       });

       if (foundOrderIds.length > 0) {
          lockedOrderIds.value = [...new Set([...lockedOrderIds.value, ...foundOrderIds])]; // 去重并合并
          createMessage.success(`成功锁定 ${foundOrderIds.length} 个订单`);
        } else {
          createMessage.info('未找到匹配的订单');
        }
      };

     // 按ID锁定订单逻辑函数（增强版，支持自动导航）
      const lockOrdersById = (enableAutoScroll = false) => {
        console.log('🔒 [lockOrdersById] ========== 开始执行 ==========');
        console.log('   📋 参数信息:');
        console.log('      - 输入框值 (lockByIdValue.value):', lockByIdValue.value);
        console.log('      - 自动导航 (enableAutoScroll):', enableAutoScroll);
        console.log('      - volumeData 键数量:', Object.keys(volumeData.value).length);
        console.log('      - 当前已锁定订单数:', lockedOrderIds.value.length);
        
        const searchId = lockByIdValue.value;
        
        if (!searchId || !searchId.trim()) {
          console.log('❌ [lockOrdersById] 订单ID为空，无法执行锁定');
          createMessage.warning('请输入订单ID');
          return false;
        }

        const finalSearchId = searchId.trim();
        console.log('🔍 [lockOrdersById] 开始搜索订单ID:', finalSearchId);
        console.log('   📊 volumeData 结构:');
        Object.keys(volumeData.value).forEach(key => {
          if (key.includes('ask') || key.includes('bid')) {
            const data = volumeData.value[key];
            const hasData = data && data.data && data.data[0] && data.data[0][0];
            console.log(`      - ${key}: ${hasData ? '有数据' : '无数据'}`);
          }
        });
        
        let found = false;
        let foundInTable = null;
        let foundInColumn = null;

        // 遍历所有volumeData中的订单数据
        outerLoop: for (const key of Object.keys(volumeData.value)) {
          if (key.includes('ask') || key.includes('bid')) {
            const data = volumeData.value[key];
            if (data && data.data && data.data[0] && data.data[0][0]) {
              const rowData = data.data[0][0];
              console.log(`   🔎 检查表格: ${key}`);
              
              // 遍历所有v1, v2, v3...列
               for (let i = 1; i <= 10000; i++) {
                 const orderLocalIdKey = `v${i}_order_local_id`;
                 const orderLocalId = rowData[orderLocalIdKey];
                 
                 // 只在前10列输出详细日志，避免日志过多
                 if (i <= 10 && orderLocalId) {
                   console.log(`      - 列 ${i}: order_local_id = ${orderLocalId}`);
                 }
                 
                 if (orderLocalId === finalSearchId) {
                   console.log('✅ [lockOrdersById] 找到匹配的订单!');
                   console.log(`   📍 位置信息:`);
                   console.log(`      - 表格: ${key}`);
                   console.log(`      - 列索引: ${i}`);
                   console.log(`      - order_local_id: ${orderLocalId}`);
                   console.log(`      - remaining_volume: ${rowData[`v${i}`]}`);
                   
                   foundInTable = key;
                   foundInColumn = i;
                   
                   // 直接锁定匹配的order_local_id
                   if (!lockedOrderIds.value.includes(finalSearchId)) {
                     lockedOrderIds.value.push(finalSearchId);
                     console.log('   ✓ 订单已添加到锁定列表');
                     console.log('   📋 当前锁定列表:', lockedOrderIds.value);
                   } else {
                     console.log('   ℹ️ 订单已在锁定列表中');
                   }
                   found = true;
                   break outerLoop;
                 }
               }
            } else {
              console.log(`   ⚠️ 表格 ${key} 无数据或结构不正确`);
            }
          }
        }

        if (found) {
          console.log('✅ [lockOrdersById] 订单锁定成功');
          console.log(`   📊 锁定结果:`);
          console.log(`      - 找到位置: ${foundInTable} 列 ${foundInColumn}`);
          console.log(`      - 已锁定订单总数: ${lockedOrderIds.value.length}`);
          createMessage.success('成功锁定订单');
          
          // 如果启用自动导航，则滚动到订单位置
          if (enableAutoScroll) {
            console.log('📍 [lockOrdersById] 启用自动导航，准备滚动到订单位置');
            setTimeout(() => {
              scrollToLockedOrder(finalSearchId);
            }, 300);
          } else {
            console.log('ℹ️ [lockOrdersById] 未启用自动导航');
          }
        } else {
          console.log('❌ [lockOrdersById] 未找到匹配的订单');
          console.log('   🔍 搜索的订单ID:', finalSearchId);
          console.log('   📊 已搜索的表格:', Object.keys(volumeData.value).filter(k => k.includes('ask') || k.includes('bid')));
          createMessage.info('未找到匹配的订单ID');
        }
        
        console.log('🔒 [lockOrdersById] ========== 执行结束 ==========');
        console.log('   📊 最终状态:');
        console.log('      - 是否找到: ', found);
        console.log('      - 已锁定订单数:', lockedOrderIds.value.length);
        
        return found;
       };

     // 清除锁定订单
     const clearLockedOrders = () => {
       lockedOrderIds.value = [];
       createMessage.success('已清除所有锁定订单');
     };

     // 从GlobalOrderSearch跳转时的滚动到锁定订单位置（增强版）
     const scrollToLockedOrderFromGlobalSearch = (orderId) => {
       console.log('scrollToLockedOrderFromGlobalSearch called with orderId:', orderId);
       
       if (!orderId) {
         console.warn('orderId is empty');
         return;
       }

       // 查找包含该订单的VolumeDataTable组件中的单元格
       let targetCell = null;
       let targetTableContainer = null;
       
       // 遍历所有可能的表格容器（ask1, ask2, ask3, bid1, bid2, bid3）
       const tableKeys = ['ask1', 'ask2', 'ask3', 'bid1', 'bid2', 'bid3'];
       
       for (const key of tableKeys) {
         const data = volumeData.value[key];
         if (data && data.data && data.data[0] && data.data[0][0]) {
           const rowData = data.data[0][0];
           
           // 查找包含该订单ID的单元格
           for (let i = 1; i <= 10000; i++) {
             const orderLocalIdKey = `v${i}_order_local_id`;
             if (rowData[orderLocalIdKey] === orderId) {
               console.log('Found order in', key, 'at column index:', i);
               
               // 找到对应的DOM元素
               // VolumeDataTable中的单元格通常有data-order-id属性或包含订单ID的内容
               const allCells = document.querySelectorAll('[data-order-id], .volume-cell');
               
               for (const cell of allCells) {
                 // 检查单元格是否包含该订单ID
                 if (cell.textContent && cell.textContent.includes(orderId)) {
                   targetCell = cell;
                   break;
                 }
               }
               
               if (targetCell) break;
             }
           }
           
           if (targetCell) break;
         }
       }
       
       // 如果没有找到单元格，尝试通过其他方式查找
       if (!targetCell) {
         console.log('Searching for cell by orderId content');
         const allCells = document.querySelectorAll('.volume-cell, [data-order-id]');
         
         for (const cell of allCells) {
           if (cell.textContent && cell.textContent.trim() === orderId) {
             targetCell = cell;
             break;
           }
         }
       }
       
       if (!targetCell) {
         console.warn('Could not find cell for orderId:', orderId);
         createMessage.warning('未找到订单在表格中的位置');
         return;
       }
       
       console.log('Found target cell, starting scroll process');
       
       // 找到表格容器（向上查找）
       let parent = targetCell.parentElement;
       for (let i = 0; i < 10 && parent; i++) {
         const style = window.getComputedStyle(parent);
         if (style.overflow === 'auto' || style.overflow === 'scroll' || 
             style.overflowY === 'auto' || style.overflowY === 'scroll') {
           targetTableContainer = parent;
           console.log('Found scrollable table container at level:', i);
           break;
         }
         parent = parent.parentElement;
       }
       
       // 第一步：滚动表格容器
       if (targetTableContainer) {
         const cellRect = targetCell.getBoundingClientRect();
         const containerRect = targetTableContainer.getBoundingClientRect();
         
         // 计算表格内的滚动距离
         const scrollTop = cellRect.top - containerRect.top + targetTableContainer.scrollTop - (containerRect.height / 2);
         
         targetTableContainer.scrollTo({
           top: Math.max(0, scrollTop),
           behavior: 'smooth'
         });
         
         console.log('Scrolling table container to position:', scrollTop);
       }
       
       // 第二步：滚动页面，确保表格容器在视野中
       setTimeout(() => {
         const cellRect = targetCell.getBoundingClientRect();
         
         // 如果单元格不在视野中，滚动页面
         if (cellRect.top < 0 || cellRect.top > window.innerHeight) {
           const scrollTop = window.pageYOffset + cellRect.top - (window.innerHeight / 2);
           
           window.scrollTo({
             top: Math.max(0, scrollTop),
             behavior: 'smooth'
           });
           
           console.log('Scrolling page to position:', scrollTop);
         }
         
         // 第三步：添加闪烁效果突出显示
         targetCell.classList.add('highlight-flash');
         setTimeout(() => {
           targetCell.classList.remove('highlight-flash');
         }, 3000);
         
         createMessage.success('已定位到订单位置');
       }, 300);
     };

     // 滚动到锁定订单位置（通用版本，支持手动和自动导航）
     const scrollToLockedOrder = (orderId) => {
       const finalOrderId = orderId;
       
       console.log('📍 [scrollToLockedOrder] 开始导航到订单');
       console.log('   订单ID:', finalOrderId);
       
       if (!finalOrderId) {
         console.warn('❌ [scrollToLockedOrder] 订单ID为空');
         return;
       }
       
       // 第一步：在 volumeData 中查找订单的位置
       console.log('🔍 [scrollToLockedOrder] 第一步：在 volumeData 中查找订单位置');
       let foundTable = null;
       let foundColumn = null;
       
       for (const key of ['ask1', 'ask2', 'ask3', 'bid1', 'bid2', 'bid3']) {
         const data = volumeData.value[key];
         if (data && data.data && data.data[0] && data.data[0][0]) {
           const rowData = data.data[0][0];
           // 遍历所有列（最多10000列）
           for (let i = 1; i <= 10000; i++) {
             const orderLocalIdKey = `v${i}_order_local_id`;
             if (rowData[orderLocalIdKey] === finalOrderId) {
               foundTable = key;
               foundColumn = i;
               console.log(`   ✓ 在 volumeData 中找到订单: 表格=${key}, 列=${i}`);
               break;
             }
           }
           if (foundTable) break;
         }
       }
       
       if (!foundTable || !foundColumn) {
         console.warn('❌ [scrollToLockedOrder] 在 volumeData 中未找到订单');
         console.log('   - 搜索的订单ID:', finalOrderId);
         console.log('   - 已锁定的订单ID列表:', lockedOrderIds.value);
         createMessage.warning('未找到订单在数据中的位置');
         return;
       }
       
       // 第二步：使用 CSS 选择器定位到具体的单元格
       console.log('🔍 [scrollToLockedOrder] 第二步：在 DOM 中定位单元格');
       
       // 尝试多种选择器策略
       let targetCell = null;
       
       // 策略1: 通过表格容器和列索引查找
       // VolumeDataTable 组件可能有特定的类名或结构
       const tableSelectors = [
         `.volume-table-${foundTable}`,
         `[data-table="${foundTable}"]`,
         `.data-li:has(.volume-table) .volume-cell:nth-child(${foundColumn})`,
       ];
       
       for (const selector of tableSelectors) {
         try {
           const cells = document.querySelectorAll(selector);
           if (cells.length > 0) {
             targetCell = cells[0];
             console.log(`   ✓ 通过选择器找到单元格: ${selector}`);
             break;
           }
         } catch (e) {
           // 选择器可能无效，继续尝试下一个
         }
       }
       
       // 策略2: 等待 Vue 渲染后查找高亮单元格（最可靠的方法）
       console.log('   等待 Vue 渲染后查找高亮单元格...');
       
       // 定义滚动执行函数
       const performScrollToCell = (cell) => {
         console.log('📜 [scrollToLockedOrder] 开始执行滚动');
         
         // 第二步：找到表格容器（向上查找）
         console.log('🔍 查找表格容器');
         let tableContainer = null;
         let parent = cell.parentElement;
         
         for (let i = 0; i < 15 && parent; i++) {
           const style = window.getComputedStyle(parent);
           if (style.overflow === 'auto' || style.overflow === 'scroll' || 
               style.overflowY === 'auto' || style.overflowY === 'scroll') {
             tableContainer = parent;
             console.log(`   ✓ 找到表格容器，层级: ${i}`);
             break;
           }
           parent = parent.parentElement;
         }
         
         if (!tableContainer) {
           console.log('   ℹ️ 未找到表格容器，使用窗口滚动');
         }
         
         // 第三步：滚动表格容器
         if (tableContainer) {
           console.log('📜 滚动表格容器');
           const cellRect = cell.getBoundingClientRect();
           const containerRect = tableContainer.getBoundingClientRect();
           
           const scrollLeft = cellRect.left - containerRect.left + tableContainer.scrollLeft - (containerRect.width / 2);
           const scrollTop = cellRect.top - containerRect.top + tableContainer.scrollTop - (containerRect.height / 2);
           
           console.log(`   单元格位置: left=${cellRect.left}, top=${cellRect.top}`);
           console.log(`   容器位置: left=${containerRect.left}, top=${containerRect.top}`);
           console.log(`   计算滚动距离: left=${scrollLeft}, top=${scrollTop}`);
           
           tableContainer.scrollTo({
             left: Math.max(0, scrollLeft),
             top: Math.max(0, scrollTop),
             behavior: 'smooth'
           });
           
           console.log('   ✓ 表格容器滚动完成');
         }
         
         // 第四步：滚动页面
         setTimeout(() => {
           console.log('📜 滚动页面');
           const cellRect = cell.getBoundingClientRect();
           
           console.log(`   单元格距离顶部: ${cellRect.top}`);
           console.log(`   窗口高度: ${window.innerHeight}`);
           
           if (cellRect.top < 0 || cellRect.top > window.innerHeight) {
             const scrollTop = window.pageYOffset + cellRect.top - (window.innerHeight / 2);
             
             console.log(`   计算页面滚动距离: ${scrollTop}`);
             
             window.scrollTo({
               top: Math.max(0, scrollTop),
               behavior: 'smooth'
             });
             
             console.log('   ✓ 页面滚动完成');
           } else {
             console.log('   ℹ️ 单元格已在视野中，无需滚动页面');
           }
           
           // 第五步：添加闪烁效果
           console.log('✨ 添加闪烁效果');
           cell.classList.add('highlight-flash');
           console.log('   ✓ 闪烁效果已添加，持续3秒');
           
           setTimeout(() => {
             cell.classList.remove('highlight-flash');
             console.log('   ✓ 闪烁效果已移除');
           }, 3000);
           
           // 如果进度条正在显示，更新进度条信息；否则显示独立通知
           if (lockProgress.value.show) {
             lockProgress.value.detail = '已定位到订单位置，订单高亮显示中';
             updateLockProgressNotification();
           } else {
             createMessage.success('已定位到订单位置');
           }
           console.log('✅ [scrollToLockedOrder] 导航完成');
         }, 300);
       };
       
       // 使用 nextTick 确保 Vue 已经更新 DOM
       nextTick(() => {
         const highlightedCells = document.querySelectorAll('.volume-cell.highlighted');
         console.log(`   找到 ${highlightedCells.length} 个高亮单元格`);
         
         if (highlightedCells.length > 0) {
           // 找到包含我们订单的那个单元格
           // 由于我们刚刚锁定了这个订单，它应该是最后一个被高亮的
           targetCell = highlightedCells[highlightedCells.length - 1];
           console.log('   ✓ 找到高亮单元格');
           
           // 执行滚动
           performScrollToCell(targetCell);
         } else {
           console.warn('   ❌ 未找到高亮单元格，可能 Vue 还未渲染');
           // 如果进度条正在显示，更新进度条信息；否则显示独立通知
           if (lockProgress.value.show) {
             lockProgress.value.detail = `找到订单位置（${foundTable} 列${foundColumn}），但单元格未高亮显示`;
             updateLockProgressNotification();
           } else {
             createMessage.warning(`找到订单位置（${foundTable} 列${foundColumn}），但单元格未高亮显示`);
           }
         }
       });
     };
     
     // 查找包含锁定订单的表格单元格（旧版本，保留用于兼容）
     const scrollToLockedOrderOld = (orderId) => {
       const highlightedCells = document.querySelectorAll('.volume-cell.highlighted');
       console.log('Found highlighted cells:', highlightedCells.length);
       
       // 查找表格容器的多种可能选择器
       const possibleTableContainers = [
         '.ant-table-body',
         '.ant-table-content',
         '.table-container',
         '.volume-table-container',
         '.data-table-container'
       ];
       
       let tableContainer = null;
       
       // 尝试找到表格容器
       for (const selector of possibleTableContainers) {
         tableContainer = document.querySelector(selector);
         if (tableContainer) {
           console.log('Found table container with selector:', selector);
           break;
         }
       }
       
       // 如果仍然没有找到，尝试从高亮单元格的父元素中查找
       if (!tableContainer && highlightedCells.length > 0) {
         const firstCell = highlightedCells[0];
         let parent = firstCell.parentElement;
         
         // 向上查找5层，寻找有滚动条的容器
         for (let i = 0; i < 5 && parent; i++) {
           const style = window.getComputedStyle(parent);
           if (style.overflow === 'auto' || style.overflow === 'scroll' || 
               style.overflowY === 'auto' || style.overflowY === 'scroll') {
             tableContainer = parent;
             console.log('Found scrollable parent container');
             break;
           }
           parent = parent.parentElement;
         }
       }
       
       // 如果还是没有找到，使用窗口作为滚动容器
       if (!tableContainer) {
         console.log('No table container found, will use window');
         tableContainer = document.documentElement;
       }
       
       if (highlightedCells.length > 0) {
         console.log('Using highlighted cells for scrolling');
         // 找到第一个高亮单元格
         const firstCell = highlightedCells[0];
         
         if (tableContainer) {
           // 计算单元格在容器中的位置
           const cellRect = firstCell.getBoundingClientRect();
           const containerRect = tableContainer.getBoundingClientRect();
           
           // 计算需要滚动的位置
           let scrollTop;
           if (tableContainer === document.documentElement) {
             // 使用窗口滚动
             scrollTop = window.pageYOffset + cellRect.top - (window.innerHeight / 2);
             window.scrollTo({
               top: scrollTop,
               behavior: 'smooth'
             });
           } else {
             // 使用容器滚动
             scrollTop = cellRect.top - containerRect.top + tableContainer.scrollTop - (containerRect.height / 2);
             tableContainer.scrollTo({
               top: scrollTop,
               behavior: 'smooth'
             });
           }
           console.log('Scrolling to position:', scrollTop);
         }
         
         // 添加闪烁效果以突出显示
         firstCell.classList.add('highlight-flash');
         setTimeout(() => {
           firstCell.classList.remove('highlight-flash');
         }, 2000);
       } else {
         console.log('No highlighted cells found, searching by orderId');
         // 如果没有找到高亮单元格，尝试查找包含订单ID的单元格
         const allCells = document.querySelectorAll('.volume-cell');
         console.log('Found total cells:', allCells.length);
         let targetCell = null;
         
         for (const cell of allCells) {
           if (cell.textContent && cell.textContent.includes(finalOrderId)) {
             targetCell = cell;
             console.log('Found cell containing orderId:', finalOrderId);
             break;
           }
         }
         
         if (targetCell) {
           console.log('Using target cell for scrolling');
           
           if (tableContainer) {
             // 计算单元格在容器中的位置
             const cellRect = targetCell.getBoundingClientRect();
             const containerRect = tableContainer.getBoundingClientRect();
             
             // 计算需要滚动的位置
             let scrollTop;
             if (tableContainer === document.documentElement) {
               // 使用窗口滚动
               scrollTop = window.pageYOffset + cellRect.top - (window.innerHeight / 2);
               window.scrollTo({
                 top: scrollTop,
                 behavior: 'smooth'
               });
             } else {
               // 使用容器滚动
               scrollTop = cellRect.top - containerRect.top + tableContainer.scrollTop - (containerRect.height / 2);
               tableContainer.scrollTo({
                 top: scrollTop,
                 behavior: 'smooth'
               });
             }
             console.log('Scrolling to position:', scrollTop);
           }
           
           // 添加闪烁效果以突出显示
           targetCell.classList.add('highlight-flash');
           setTimeout(() => {
             targetCell.classList.remove('highlight-flash');
           }, 2000);
         } else {
           console.error('Could not find cell containing orderId:', finalOrderId);
           createMessage.warning('未找到锁定订单在表格中的位置');
         }
       }
     };

    // 旧版获取市场数据并计算差值的函数 - 已注释掉，使用新的API替代
    /*
    const updateMarketData = async () => {
      if (!selectSym.value || !selectDate.value || !selectTime.value) {
        return;
      }

      try {
        // 获取当前时间戳的数据
        const currentParams = {
          sym: selectSym.value,
          date: selectDate.value,
          time: selectTime.value
        };

        const currentRes = await getSnapshotByTime(currentParams);

        if (currentRes.code === 0 && currentRes.data?.snapshot?.market_data) {
          const currentMarketData = currentRes.data.snapshot.market_data;

          // 使用API返回的timestamp作为当前时间基准
          const apiTimestamp = currentRes.data.snapshot.timestamp || currentRes.data.time || selectTime.value;
          const extractedTime = extractTimeFromTimestamp(apiTimestamp);

          // 定义时间间隔（毫秒）
          const timeIntervals = {
            last_1min: 60000,    // 1分钟
            last_3s: 3000,      // 3秒
            last_500ms: 500,    // 500毫秒
            last_50ms: 50,      // 50毫秒
            last_10ms: 10       // 10毫秒
          };

          // 存储各时间段的差值数据
          const marketDiffs = {};

          // 为每个时间间隔计算差值
          for (const [key, interval] of Object.entries(timeIntervals)) {
            // 直接基于API返回的真实timestamp计算过去时间
            const apiTime = new Date(`${selectDate.value} ${extractedTime}`);
            const pastTime = new Date(apiTime.getTime() - interval);
            const pastTimeStr = formatTimeWithMilliseconds(pastTime);

            const pastParams = {
              sym: selectSym.value,
              date: selectDate.value,
              time: pastTimeStr
            };

            try {
              const pastRes = await getSnapshotByTime(pastParams);

              let diff = {
                bid_create_count: currentMarketData.bid_create_count || 0,
                bid_cancel_count: currentMarketData.bid_cancel_count || 0,
                bid_traded_count: currentMarketData.bid_traded_count || 0,
                ask_create_count: currentMarketData.ask_create_count || 0,
                ask_cancel_count: currentMarketData.ask_cancel_count || 0,
                ask_traded_count: currentMarketData.ask_traded_count || 0
              };

              // 如果成功获取到过去时间的数据，计算差值
              if (pastRes.code === 0 && pastRes.data?.snapshot?.market_data) {
                const pastMarketData = pastRes.data.snapshot.market_data;
                diff = {
                  bid_create_count: (currentMarketData.bid_create_count || 0) - (pastMarketData.bid_create_count || 0),
                  bid_cancel_count: (currentMarketData.bid_cancel_count || 0) - (pastMarketData.bid_cancel_count || 0),
                  bid_traded_count: (currentMarketData.bid_traded_count || 0) - (pastMarketData.bid_traded_count || 0),
                  ask_create_count: (currentMarketData.ask_create_count || 0) - (pastMarketData.ask_create_count || 0),
                  ask_cancel_count: (currentMarketData.ask_cancel_count || 0) - (pastMarketData.ask_cancel_count || 0),
                  ask_traded_count: (currentMarketData.ask_traded_count || 0) - (pastMarketData.ask_traded_count || 0)
                };
              }

              marketDiffs[key] = diff;
            } catch (error) {
              console.error(`获取${key}数据失败:`, error);
              // 如果获取失败，使用当前数据作为差值
              marketDiffs[key] = {
                bid_create_count: currentMarketData.bid_create_count || 0,
                bid_cancel_count: currentMarketData.bid_cancel_count || 0,
                bid_traded_count: currentMarketData.bid_traded_count || 0,
                ask_create_count: currentMarketData.ask_create_count || 0,
                ask_cancel_count: currentMarketData.ask_cancel_count || 0,
                ask_traded_count: currentMarketData.ask_traded_count || 0
              };
            }
          }

          // 更新marketData（保持向后兼容，使用1分钟数据）
          marketData.value = marketDiffs.last_1min || {};

          // 更新tradeData显示
          const tradeDataArray = [
            {
              level: '买一新增挂单',
              last_1min: marketDiffs.last_1min?.bid_create_count || 0,
              last_3s: marketDiffs.last_3s?.bid_create_count || 0,
              last_500ms: marketDiffs.last_500ms?.bid_create_count || 0,
              last_50ms: marketDiffs.last_50ms?.bid_create_count || 0,
              last_10ms: marketDiffs.last_10ms?.bid_create_count || 0
            },
            {
              level: '买一新增撤单',
              last_1min: marketDiffs.last_1min?.bid_cancel_count || 0,
              last_3s: marketDiffs.last_3s?.bid_cancel_count || 0,
              last_500ms: marketDiffs.last_500ms?.bid_cancel_count || 0,
              last_50ms: marketDiffs.last_50ms?.bid_cancel_count || 0,
              last_10ms: marketDiffs.last_10ms?.bid_cancel_count || 0
            },
            {
              level: '买一新增成交',
              last_1min: marketDiffs.last_1min?.bid_traded_count || 0,
              last_3s: marketDiffs.last_3s?.bid_traded_count || 0,
              last_500ms: marketDiffs.last_500ms?.bid_traded_count || 0,
              last_50ms: marketDiffs.last_50ms?.bid_traded_count || 0,
              last_10ms: marketDiffs.last_10ms?.bid_traded_count || 0
            },
            {
              level: '卖一新增挂单',
              last_1min: marketDiffs.last_1min?.ask_create_count || 0,
              last_3s: marketDiffs.last_3s?.ask_create_count || 0,
              last_500ms: marketDiffs.last_500ms?.ask_create_count || 0,
              last_50ms: marketDiffs.last_50ms?.ask_create_count || 0,
              last_10ms: marketDiffs.last_10ms?.ask_create_count || 0
            },
            {
              level: '卖一新增撤单',
              last_1min: marketDiffs.last_1min?.ask_cancel_count || 0,
              last_3s: marketDiffs.last_3s?.ask_cancel_count || 0,
              last_500ms: marketDiffs.last_500ms?.ask_cancel_count || 0,
              last_50ms: marketDiffs.last_50ms?.ask_cancel_count || 0,
              last_10ms: marketDiffs.last_10ms?.ask_cancel_count || 0
            },
            {
              level: '卖一新增成交',
              last_1min: marketDiffs.last_1min?.ask_traded_count || 0,
              last_3s: marketDiffs.last_3s?.ask_traded_count || 0,
              last_500ms: marketDiffs.last_500ms?.ask_traded_count || 0,
              last_50ms: marketDiffs.last_50ms?.ask_traded_count || 0,
              last_10ms: marketDiffs.last_10ms?.ask_traded_count || 0
            }
          ];

          tradeData.value = tradeDataArray;
        }
      } catch (error) {
        console.error('获取市场数据失败:', error);
      }
    };
    */

    // 新版使用单一API获取订单统计信息
    const updateMarketData = async () => {
      if (!selectSym.value || !selectDate.value || !selectTime.value) {
        return;
      }

      try {
        const params = {
          sym: selectSym.value,
          date: selectDate.value,
          time: selectTime.value
        };

        const response = await getPastTimeTradeInfo(params);

        if (response.code === 0 && response.data) {
          // 只更新数据字段，保持固定的 level 列不变
          if (response.data.length > 0 && tradeData.value.length > 0) {
            // 根据 level 值匹配并更新对应的数据
            response.data.forEach((apiItem, index) => {
              if (index < tradeData.value.length) {
                // 保持原有的 level 值，只更新数据字段，空白值用 0 填充
                tradeData.value[index] = {
                  ...tradeData.value[index], // 保持原有的 level
                  last_1min: apiItem.last_1min || 0,
                  last_3s: apiItem.last_3s || 0,
                  last_500ms: apiItem.last_500ms || 0,
                  last_50ms: apiItem.last_50ms || 0,
                  last_10ms: apiItem.last_10ms || 0
                };
              }
            });
          }

          // 为了保持向后兼容，从第一个数据项提取marketData（1分钟数据）
          if (response.data.length > 0) {
            const firstItem = response.data[0]; // 买一新增挂单
            marketData.value = {
              bid_create_count: firstItem.last_1min || 0,
              bid_cancel_count: response.data[1]?.last_1min || 0, // 买一新增撤单
              bid_traded_count: response.data[2]?.last_1min || 0, // 买一新增成交
              ask_create_count: response.data[3]?.last_1min || 0, // 卖一新增挂单
              ask_cancel_count: response.data[4]?.last_1min || 0, // 卖一新增撤单
              ask_traded_count: response.data[5]?.last_1min || 0  // 卖一新增成交
            };
          }

        } else {
          createMessage.error(response.message || '获取订单统计信息失败');
        }
      } catch (error) {
        createMessage.error('网络请求失败，请检查网络连接');
      }
    };

    // 已删除getOrderIndexLevelInfo和getSelectTimeTradeInfo函数
    // 这些功能已合并到getOrderbookData中

    // WebSocket进度监听相关方法
    const startProgressListening = async (taskId) => {
      try {
        // 关闭之前的连接
        if (progressWebSocket) {
          progressWebSocket.close();
        }

        // 创建新的WebSocket连接
        progressWebSocket = createProgressListener(taskId);

        // 设置事件监听器
        progressWebSocket
          .onProgress((data) => {
            console.log('🎯 Vue组件收到进度更新:', data);
            console.log('📊 更新前的进度状态:', JSON.stringify(initProgress.value, null, 2));

            // 更新进度状态
            initProgress.value.progress = data.progress;
            initProgress.value.message = data.message;
            initProgress.value.status = data.status;

            // 更新进度条通知
            updateProgressNotification();

            console.log('📈 更新后的进度状态:', JSON.stringify(initProgress.value, null, 2));
            console.log('🎨 UI是否显示进度条:', initProgress.value.show);
          })
          .onComplete((data) => {
            console.log('✅ Vue组件收到初始化完成:', data);
            initProgress.value.progress = 100;
            initProgress.value.message = '初始化完成，开始加载数据...';
            initProgress.value.status = 'completed';

            // 更新进度条通知为完成状态
            updateProgressNotification();

            console.log('🎉 初始化完成，最终状态:', JSON.stringify(initProgress.value, null, 2));

            // 初始化完成后立即开始数据加载
            console.log('🚀 初始化完成，立即开始数据加载');
            proceedWithDataLoading();

            createMessage.success('初始化完成，正在加载数据...');

            // 注意：WebSocket监听会在数据加载完成时自动停止
          })
          .onErrorOccurred((error) => {
            console.error('❌ Vue组件收到WebSocket错误:', error);
            initProgress.value.status = 'failed';
            initProgress.value.message = `错误: ${error}`;

            // 更新进度条通知为错误状态
            updateProgressNotification();

            // 根据错误类型显示不同的错误信息
            let errorMessage = `初始化失败: ${error}`;
            let isServerCrash = false;

            if (error.includes('std::bad_alloc')) {
              errorMessage = '服务器内存不足: 当前数据集过大，服务器无法处理。建议：1）选择较小的数据集 2）联系管理员增加服务器内存';
              isServerCrash = true;
            } else if (error.includes('任务执行失败')) {
              errorMessage = '任务执行失败: 服务器在处理过程中出现错误';
              isServerCrash = true;
            } else if (error.includes('网络连接错误') || error.includes('服务器已断开') || error.includes('Connection refused')) {
              errorMessage = '服务器连接中断: 服务器可能在处理大型数据时崩溃。请检查服务器状态或稍后重试';
              isServerCrash = true;
            } else if (error.includes('连接失败：已达到最大重连次数') || error.includes('查询重试次数过多')) {
              errorMessage = '连接失败: 多次尝试连接服务器失败，服务器可能不可用';
              isServerCrash = true;
            } else if (error.includes('timeout') || error.includes('超时')) {
              errorMessage = '连接超时: 服务器响应超时，可能正在处理其他任务或负载过高';
            }

            // 如果是服务器崩溃，添加特殊提示
            if (isServerCrash) {
              errorMessage += '\n\n💡 建议操作：\n1. 检查服务器状态（点击"🩺检查服务器"按钮）\n2. 尝试处理较小的数据集\n3. 联系管理员查看服务器日志';
            }

            createMessage.error(errorMessage);

            // 失败后关闭进度条通知
            setTimeout(() => {
              closeProgressNotification();
              initProgress.value.show = false;
              console.log('🔒 错误后进度条已隐藏');
            }, 8000); // 延长显示时间让用户看到完整错误信息
          })
          .onConnect(() => {
            console.log('🔗 Vue组件：WebSocket连接成功');
            console.log('🎯 当前任务信息:', {
              taskId: initProgress.value.taskId,
              symbol: selectSym.value,
              date: selectDate.value,
              wsUrl: `ws://10.1.228.20:18080/ws/progress/${initProgress.value.taskId}`
            });
          })
          .onDisconnect(() => {
            console.log('🔌 Vue组件：WebSocket连接断开');
          });

        // 开始连接
        await progressWebSocket.connect();

        console.log('🚀 WebSocket连接已建立，taskId:', taskId);

      } catch (error) {
        console.error('❌ 启动WebSocket进度监听失败:', error);
        createMessage.error('无法连接进度服务，请检查网络连接');
        initProgress.value.show = false;
      }
    };





    // 获取进度条颜色
    const getProgressColor = (status) => {
      switch (status) {
        case 'initializing':
          return '#1890ff'; // 蓝色
        case 'completed':
          return '#52c41a'; // 绿色
        case 'failed':
          return '#ff4d4f'; // 红色
        default:
          return '#1890ff';
      }
    };

    // 组件销毁时清理WebSocket连接和进度条通知
    onUnmounted(() => {
      if (progressWebSocket) {
        progressWebSocket.close();
        progressWebSocket = null;
      }
      // 关闭进度条通知
      closeProgressNotification();
      
      // 清空 localStorage 中的选择数据（关闭标签页时清空）
      console.log('🧹 [VolumeQueue] 组件卸载，清空 localStorage 数据');
      localStorage.removeItem('volumeQueue_selectSym');
      localStorage.removeItem('volumeQueue_selectDate');
      localStorage.removeItem('volumeQueue_timestamp');
      localStorage.removeItem('volumeQueue_orderIndex');
      console.log('   ✓ 已清空股票代码、日期、时间戳和订单索引');
    });
    
    // 处理从GlobalOrderSearch跳转到订单快照并锁定订单
    const handleGoToOrderSnapshotAndLock = (orderId) => {
      // 检查是否已选择股票代码和日期
      if (!selectSym.value || !selectDate.value) {
        createMessage.warning('请先选择股票代码和日期，然后再尝试跳转到订单快照');
        return;
      }
      
      // 使用订单ID查询快照
      const params = {
        sym: selectSym.value,
        date: selectDate.value,
        orderid: parseInt(orderId)
      };
      
      loading.value = true;
      createMessage.loading('正在查找订单快照...', 0);
      
      getSnapshotById(params).then((res) => {
        createMessage.destroy(); // 关闭loading消息
        
        if (res.code === 0 && res.data && res.data.snapshot) {
          const snapshot = res.data.snapshot;
          
          // 更新快照数据
          updateVolumeDataFromSnapshot(snapshot, res.data);
          
          // 更新市场数据
          updateMarketData();
          
          // 锁定订单
          lockOrderById(orderId);
          
          createMessage.success(`已跳转到订单 ${orderId} 的快照并锁定该订单`);
        } else {
          createMessage.error(res.message || `未找到订单 ${orderId} 的快照`);
        }
      }).catch((error) => {
        createMessage.destroy(); // 关闭loading消息
        createMessage.error('查询订单快照失败，请检查网络连接');
        console.error('查询订单快照失败:', error);
      }).finally(() => {
        loading.value = false;
      });
    };
    
    // 统一的订单锁定处理器 - 整合所有锁定相关逻辑（带进度条）
    const unifiedOrderLockHandler = async (lockData) => {
      // 提取并格式化时间（在函数开头声明，避免重复声明）
      let timeOnly = lockData.timestamp;
      if (timeOnly.includes(' ')) {
        timeOnly = timeOnly.split(' ')[1];
      }
      if (timeOnly.includes('.')) {
        const [timePart, msPart] = timeOnly.split('.');
        timeOnly = `${timePart}.${msPart.substring(0, 3)}`;
      }
      
      // 初始化进度状态
      lockProgress.value = {
        show: true,
        message: '准备锁定订单...',
        detail: `订单ID: ${lockData.orderId} | ${lockData.sym} | ${lockData.date}`,
        progress: 0,
        status: 'processing',
        currentStep: 0,
        totalSteps: 7
      };
      
      // 创建进度条通知
      createLockProgressNotification();
      
      try {
        // 步骤1: 设置股票代码和日期 (14%)
        lockProgress.value.currentStep = 1;
        lockProgress.value.progress = 14;
        lockProgress.value.message = '设置股票代码和日期...';
        lockProgress.value.detail = `股票代码: ${lockData.sym} | 交易日期: ${lockData.date}`;
        updateLockProgressNotification();
        
        selectSym.value = lockData.sym;
        securityType.value = getSecurityType(lockData.sym);
        selectDate.value = lockData.date;
        hasSymbol.value = true;
        hasDate.value = true;
        localStorage.setItem('volumeQueue_selectSym', lockData.sym);
        localStorage.setItem('volumeQueue_securityType', securityType.value);
        localStorage.setItem('volumeQueue_selectDate', lockData.date);
        
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // 步骤2: 设置时间 (28%)
        lockProgress.value.currentStep = 2;
        lockProgress.value.progress = 28;
        lockProgress.value.message = '设置跳转时间...';
        updateLockProgressNotification();
        
        selectTime.value = timeOnly;
        localStorage.setItem('volumeQueue_timestamp', timeOnly);
        lockProgress.value.detail = `跳转时间: ${timeOnly}`;
        
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // 步骤3: 填充订单ID (42%)
        lockProgress.value.currentStep = 3;
        lockProgress.value.progress = 42;
        lockProgress.value.message = '填充订单ID...';
        lockProgress.value.detail = `订单ID: ${lockData.orderId}`;
        updateLockProgressNotification();
        
        lockByIdValue.value = lockData.orderId;
        
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // 步骤4: 加载日期列表 (56%)
        lockProgress.value.currentStep = 4;
        lockProgress.value.progress = 56;
        lockProgress.value.message = '加载日期列表...';
        updateLockProgressNotification();
        
        if (!datesData.value.length) {
          loading.value = true;
          const params = { sym: lockData.sym };
          
          try {
            const res = await getDateList(params);
            loading.value = false;
            
            if (res.code == 0) {
              datesData.value = res.data.map(item => ({ label: item, value: item }));
              lockProgress.value.detail = `已加载 ${datesData.value.length} 个交易日期`;
              updateLockProgressNotification();
            }
          } catch (error) {
            loading.value = false;
            lockProgress.value.detail = '加载日期列表失败';
            updateLockProgressNotification();
            console.error('加载日期列表失败:', error);
          }
        } else {
          lockProgress.value.detail = `日期列表已存在 (${datesData.value.length} 个)`;
          updateLockProgressNotification();
        }
        
        // 步骤5: 加载订单数据 (70%)
        lockProgress.value.currentStep = 5;
        lockProgress.value.progress = 70;
        lockProgress.value.message = '加载订单数据...';
        lockProgress.value.detail = '正在初始化 TradeBook...';
        updateLockProgressNotification();
        
        if (hasSymbol.value && hasDate.value && !loading.value) {
          await getOrderbookData();
          
          // 重要：getOrderbookData 会重置 selectTime.value 为 09:30:00.000
          // 需要重新设置为用户输入的时间（使用函数开头提取的 timeOnly）
          selectTime.value = timeOnly;
          console.log('   ✓ [unifiedOrderLockHandler] 重新设置跳转时间为:', selectTime.value);
          
          lockProgress.value.detail = '订单数据加载完成';
          updateLockProgressNotification();
        }
        
        // 步骤6: 跳转到指定时间 (84%)
        lockProgress.value.currentStep = 6;
        lockProgress.value.progress = 84;
        lockProgress.value.message = '跳转到指定时间...';
        lockProgress.value.detail = `目标时间: ${timeOnly}`;
        updateLockProgressNotification();
        
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 调用前再次确认时间
        console.log('   ✓ [步骤6] 调用 clickMoveTime，传入时间参数:', timeOnly);
        clickMoveTime(timeOnly); // 直接传入时间参数，不依赖 selectTime.value
        lockProgress.value.detail = '时间跳转完成';
        updateLockProgressNotification();
        
        // 步骤7: 锁定订单并滚动 (100%)
        lockProgress.value.currentStep = 7;
        lockProgress.value.progress = 98;
        lockProgress.value.message = '锁定订单并定位...';
        lockProgress.value.detail = `正在查找订单 ${lockData.orderId}...`;
        updateLockProgressNotification();
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const lockSuccess = lockOrdersById(true);
        
        if (lockSuccess) {
          // 成功完成
          lockProgress.value.progress = 100;
          lockProgress.value.status = 'completed';
          lockProgress.value.message = '订单锁定成功！';
          lockProgress.value.detail = `订单 ${lockData.orderId} 已锁定并定位到页面`;
          updateLockProgressNotification();
          
          // 延迟关闭进度条
          setTimeout(() => {
            closeLockProgressNotification();
            lockProgress.value.show = false;
          }, 2500);
          
        } else {
          // 锁定失败
          lockProgress.value.status = 'failed';
          lockProgress.value.message = '订单锁定失败';
          lockProgress.value.detail = `未找到订单 ${lockData.orderId}，请检查数据是否已加载`;
          updateLockProgressNotification();
          
          // 延迟关闭进度条
          setTimeout(() => {
            closeLockProgressNotification();
            lockProgress.value.show = false;
          }, 4000);
        }
        
      } catch (error) {
        console.error('订单锁定流程失败:', error);
        
        // 失败状态
        lockProgress.value.status = 'failed';
        lockProgress.value.message = '订单锁定流程失败';
        lockProgress.value.detail = `错误: ${error.message || '未知错误'}`;
        updateLockProgressNotification();
        
        // 延迟关闭进度条
        setTimeout(() => {
          closeLockProgressNotification();
          lockProgress.value.show = false;
        }, 4000);
      }
    };

    // 跳转到指定时间并锁定订单
    const jumpToTimeWithLock = async (timestamp, orderId) => {
      console.log('开始跳转到时间:', timestamp, '订单ID:', orderId);
            // 边界检测
        const checkResult = checkTimeBoundary(timestamp);
        selectTime.value = checkResult.corrected;
        localStorage.setItem('volumeQueue_timestamp', checkResult.corrected);
        console.log('   ✓ 时间已设置并保存:', checkResult.corrected);

      // 延迟执行，确保数据加载完成
      return new Promise((resolve, reject) => {
        setTimeout(async () => {
          try {
            // 加载该时间点的数据
            await clickMoveTime();
            
            // 等待一段时间确保DOM更新
            setTimeout(() => {
              // 锁定订单
              const lockResult = lockOrderById(orderId);
              
              if (lockResult) {
                // 滚动到锁定订单位置
                scrollToLockedOrder(orderId);
                
                // 清除localStorage中的锁定标记
                clearLockDataFromStorage();
                
                const formattedTime = formatTimestamp(timestamp);
                createMessage.success(`订单 ${orderId} 锁定成功 (${formattedTime})`);
                resolve(true);
              } else {
                const error = new Error(`未找到匹配的订单ID: ${orderId}`);
                const result = handleOrderLockError(error);
                showOrderLockFeedback(result);
                reject(error);
              }
            }, 1000); // 等待1秒确保DOM更新完成
            
          } catch (error) {
            console.error('跳转时间并锁定订单失败:', error);
            const result = handleOrderLockError(error);
            showOrderLockFeedback(result);
            reject(error);
          }
        }, 500); // 延迟500ms执行
      });
    };

    // 清除localStorage中的锁定数据
    const clearLockDataFromStorage = () => {
      const lockKeys = [
        'volumeQueue_lockOrderId',
        'volumeQueue_lockSym', 
        'volumeQueue_lockDate',
        'volumeQueue_lockTimestamp',
        'volumeQueue_isFromGlobalSearch'
      ];
      
      lockKeys.forEach(key => {
        localStorage.removeItem(key);
      });
      
      console.log('已清除localStorage中的锁定数据');
    };

    // 根据订单ID锁定订单（返回布尔值表示是否成功）
    const lockOrderById = (orderId) => {
      let found = false;

      // 遍历所有volumeData中的订单数据
      outerLoop: for (const key of Object.keys(volumeData.value)) {
        if (key.includes('ask') || key.includes('bid')) {
          const data = volumeData.value[key];
          if (data && data.data && data.data[0] && data.data[0][0]) {
            const rowData = data.data[0][0];
            // 遍历所有v1, v2, v3...列
             for (let i = 1; i <= 10000; i++) {
               const orderLocalIdKey = `v${i}_order_local_id`;
               if (rowData[orderLocalIdKey] === orderId) {
                 // 直接锁定匹配的order_local_id
                 if (!lockedOrderIds.value.includes(orderId)) {
                   lockedOrderIds.value.push(orderId);
                   console.log('成功锁定订单ID:', orderId);
                 }
                 found = true;
                 break outerLoop; // 找到后立即退出所有遍历
               }
             }
          }
        }
      }

      if (!found) {
        console.log('未找到匹配的订单ID:', orderId);
        createMessage.info(`未找到匹配的订单ID: ${orderId}`);
      }
      
      return found;
    };
</script>
<style lang="less" scoped>
  .filter-mode {
    padding: 4px 8px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    min-height: 34px;

    &.compact-row {
      padding: 3px 8px;
      margin-bottom: 3px;
    }

    .filter-item {
      margin-top: 0px;
      margin-right: 8px;
      margin-bottom: 0px;
      display: flex;
      align-items: center;
      min-width: 0;

      &.info-item {
        margin-right: 15px;
      }

      &.locked-orders-info {
        background-color: #f0f8ff;
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid #d1ecf1;
      }

      &.lock-controls {
        display: flex;
        align-items: center;
        gap: 0;
        flex-wrap: wrap;
        row-gap: 6px;

        .field-label {
          margin-right: 8px;
          white-space: nowrap;
        }
      }

      .item-name {
        padding: 0 8px;
      }
    }

    .field-label {
      margin-right: 5px;
      font-size: 13px;
      white-space: nowrap;
    }

    .info-label {
      font-size: 12px;
      color: #666;
      white-space: nowrap;
    }

    .section-label {
      margin-right: 8px;
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
      min-width: 68px;
    }

    .button-group {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }

    .time-btn,
    .order-btn {
      width: 78px;
      height: 27px;
      font-size: 12px;
      padding: 0 5px;
    }
  }

  .primary-filter-row {
    display: grid;
    grid-template-columns: minmax(150px, 1fr) minmax(180px, 1.35fr) minmax(180px, 1.2fr) auto;
    gap: 8px;
    padding-top: 2px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e1e6ed;

    .filter-item {
      margin-right: 0;
      min-width: 0;
    }

    :deep(.ant-select) {
      width: 100% !important;
      margin-left: 0 !important;
    }

    :deep(.ant-btn) {
      min-width: 64px;
    }
  }

  .navigation-row,
  .lock-row {
    padding-top: 8px;
    padding-bottom: 4px;
  }

  .navigation-row {
    justify-content: space-between;

    .filter-item {
      margin-right: 0;
    }
  }

  .lock-row {
    border-bottom: 1px solid #e1e6ed;
    padding-bottom: 8px;

    .lock-controls {
      width: 100%;
      margin-right: 0;
    }

    :deep(.ant-input) {
      max-width: 150px;
    }
  }

  .movement-row {
    padding-top: 4px;
    padding-bottom: 2px;

    .button-group {
      flex: 1;
    }
  }

  .echart-ul {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    width: 100%;
    .echart-li {
      width: 530px;
      flex-shrink: 1;
    }
  }
  .main-mode {
    .data-ul {
      display: flex;
      justify-content: flex-start;
      width: 100%;
      align-items: flex-start;
      .data-li {
        flex: 1;
        margin-top: 5px;
        margin-right: 5px;
        background: #e9e7e7;
      }
    }
    .data-ul-top {
      display: grid;
      grid-template-columns: minmax(620px, 3fr) minmax(280px, 2fr) minmax(360px, 4fr);
      gap: 8px;
      width: 100%;
      min-height: 280px;
      height: auto;
      align-items: stretch;
      .data-li:nth-child(1) {
        min-width: 0;
        margin: 0;
        padding: 10px 12px;
        background: #f5f7fa;
        border: 1px solid #e1e6ed;
        border-radius: 6px;
        box-sizing: border-box;
      }

      .data-li:nth-child(2) {
        min-width: 0;
        margin: 0;
        background: #f5f7fa;
        border: 1px solid #e1e6ed;
        border-radius: 6px;
        overflow: hidden;
      }

      .data-li:nth-child(3) {
        min-width: 0;
        margin: 0;
        background: #f5f7fa;
        border: 1px solid #e1e6ed;
        border-radius: 6px;
        overflow: hidden;
      }
    }

    .empty-mode {
      height: calc(100vh - 300px);
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }

  @media (max-width: 1280px) {
    .main-mode .data-ul-top {
      grid-template-columns: minmax(560px, 3fr) minmax(260px, 2fr);

      .data-li:nth-child(3) {
        grid-column: 1 / -1;
      }
    }
  }

  @media (max-width: 900px) {
    .main-mode .data-ul-top {
      grid-template-columns: minmax(0, 1fr);

      .data-li:nth-child(3) {
        grid-column: auto;
      }
    }
  }

  @media (max-width: 760px) {
    .primary-filter-row {
      grid-template-columns: 1fr 1fr;
    }

    .primary-filter-row .filter-item:last-child {
      justify-content: flex-start;
    }
  }

  .dropdown-list {
    max-height: 200px; /* 设置一个合适的最大高度 */
    overflow-y: auto; /* 当内容超过最大高度时显示滚动条 */
    position: absolute; /* 设置绝对定位 */
    z-index: 1000; /* 确保下拉列表在其他元素之上 */
    background-color: white;
  }
  :deep(.ant-table-thead) {
    .header-transaction-amount {
      background-color: #e9e7e7;
    }
  }

  // 第二个表格的表头高度减少
  .data-li:nth-child(2) {
    :deep(.ant-table-thead > tr > th) {
      height: 75px !important;
      padding: 8px 8px !important;
      font-size: 12px;
      line-height: 1.2;
    }
  }

  // 第三个表格的表头高度减少
  .data-li:nth-child(3) {
    :deep(.ant-table-thead > tr > th) {
      height: 75px !important;
      padding: 4px 8px !important;
      font-size: 12px;
      line-height: 1.2;
    }
  }
  :deep(.ant-table-tbody > tr) {
    height: 30px; // 设置所有行的固定高度
    font-size: 13px; // 确保字体大小一致
    td {
      padding: 0px; // 确保内边距一致
      vertical-align: middle; // 设置垂直对齐方式
      text-align: center; // 设置水平对齐方式
    }
  }
  
  // 高亮闪烁效果
  :deep(.volume-cell.highlight-flash) {
    animation: highlightFlash 2s ease-in-out;
  }
  
  @keyframes highlightFlash {
    0% {
      background-color: rgba(24, 144, 255, 0.2);
      box-shadow: 0 0 8px rgba(24, 144, 255, 0.8);
    }
    50% {
      background-color: rgba(24, 144, 255, 0.6);
      box-shadow: 0 0 12px rgba(24, 144, 255, 1);
    }
    100% {
      background-color: rgba(24, 144, 255, 0.2);
      box-shadow: 0 0 8px rgba(24, 144, 255, 0.8);
    }
  }
</style>
