<template>
  <Spin :spinning="loading">
    <div class="m-4 overflow-hidden bg-white">
      <div class="filter-mode security-filter-panel" :style="{ marginTop: '5px', marginBottom: '1px' }">
        <div class="filter-item" style="margin-bottom: 5px">
          <span
            :style="{
              marginTop: '5px',
              marginBottom: '5px',
              marginLeft: '1px',
              marginRight: '5px',
            }"
            >证券类型</span
          >
          <Select
            v-model:value="securityType"
            style="width: 90px"
            :options="securityTypeOptions"
            :allow-clear="false"
            @change="handleSecurityTypeChange"
          />
        </div>
        <div class="filter-item" style="margin-bottom: 5px">
          <span
            :style="{
              marginTop: '5px',
              marginBottom: '5px',
              marginLeft: '10px',
              marginRight: '5px',
            }"
            >证券代码</span
          >
          <Select
            v-model:value="selectSym"
            show-search
            :placeholder="`选择${securityType === 'fund' ? '基金' : '股票'}代码`"
            style="width: 120px"
            :options="filteredSymsData"
            :filter-option="symFilterOption"
            @change="selectSymItem"
          />
        </div>
        <div class="filter-item" style="margin-bottom: 5px">
          <span
            :style="{
              marginTop: '5px',
              marginBottom: '5px',
              marginLeft: '10px',
              marginRight: '5px',
            }"
            >日期</span
          >
          <Select
            v-model:value="selectDate"
            show-search
            placeholder="选择日期"
            style="width: 120px"
            :options="datesData"
            :filter-option="dateFilterOption"
            @change="selectDateItem"
          />
        </div>
        <div class="filter-item" style="margin-bottom: 5px">
          <span
            :style="{
              marginTop: '5px',
              marginBottom: '5px',
              marginLeft: '10px',
              marginRight: '5px',
            }"
            >开始时间</span
          >
          <Select
            v-model:value="startTime"
            show-search
            placeholder="选择开始时间"
            style="width: 120px"
            :options="timeList"
            :filter-option="startTimeFilterOption"
            @change="startTimeSelect"
          />
        </div>
        <div class="filter-item" style="margin-bottom: 5px">
          <span
            :style="{
              marginTop: '5px',
              marginBottom: '5px',
              marginLeft: '10px',
              marginRight: '5px',
            }"
            >结束时间</span
          >
          <Select
            v-model:value="endTime"
            show-search
            placeholder="选择结束时间"
            style="width: 120px"
            :options="timeList"
            :filter-option="endTimeFilterOption"
            @change="endTimeSelect"
          />
        </div>
        <div class="filter-item" style="margin-bottom: 5px">
          <Button type="primary" @click="create_task" :disabled="!hasSymbol || !hasDate"
            >创建任务</Button
          >
        </div>
      </div>
    </div>
    <div class="m-4 overflow-hidden bg-white">
      <div class="main-mode">
        <Table
          :columns="visibleColumns"
          bordered
          :scroll="{ x: '1200px', y: 'calc( 100vh - 380px )' }"
          :pagination="pagination"
          :dataSource="filteredData"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, text, record }">
            <template v-if="column.dataIndex === 'operation'">
              <Popconfirm
                v-if="tableData.length"
                title="Sure to delete?"
                @confirm="onDelete(record.sym, record.date, record.start_time, record.end_time)"
              >
                <a>Delete</a>
              </Popconfirm>
            </template>
          </template>
        </Table>
        <!-- <Empty class="empty-mode" v-if="!tableData.length" :description="false" /> -->
      </div>
    </div>
  </Spin>
</template>
<script lang="js" setup>
  import { ref, computed, onMounted, onUnmounted } from 'vue';
  import { uploadFile, getListObjectFile, getObjectDownloadFile } from '../../services/minioService';
  import { Table, Empty, Spin, Radio, Button, Select, Popconfirm  } from 'ant-design-vue';
  import { getTasks, createTask, deleteTask, getSyms, getDates } from '/@/api/orderbook/orderDataGenerate'
  import { useMessage } from '/@/hooks/web/useMessage';
  import { getSecurityType, securityTypeOptions, toSymbolOption } from '/@/utils/securityType';

  const tableData = ref([]);
  const loading = ref(true);
  const defaultWidth = 120;
  const { createMessage } = useMessage();

  const securityType = ref('stock')
  const selectSym = ref('')
  const symsData = ref([])
  const hasSymbol = ref(false)

  const filteredSymsData = computed(() => {
    return symsData.value.filter((option) => option.securityType === securityType.value);
  });

  const selectDate = ref('')
  const datesData = ref([])
  const hasDate = ref(false)

  const filteredInfo = ref({});
  const timeList = ref([])
  const startTime = ref('09:30:00')
  const endTime = ref('15:00:00')

  // 分页相关变量
  const pagination = ref({
    current: 1,
    pageSize: 20,
    total: 0,
  });

  const columns = [
    {
      title: '创建时间',
      dataIndex: 'createtime',
      key: 'createtime',
      width: defaultWidth,
      className: 'header-transaction-amount',
      align: 'center',
      sorter: (a, b) => a.createtime.localeCompare(b.createtime)
    },
    {
      title: '股票代码',
      dataIndex: 'sym',
      key: 'sym',
      width: defaultWidth,
      className: 'header-transaction-amount',
      align: 'center',
      sorter: (a, b) => a.sym.localeCompare(b.sym)
    },
    {
      title: '交易日期',
      dataIndex: 'date',
      key: 'date',
      width: defaultWidth,
      className: 'header-transaction-amount',
      align: 'center',
      sorter: (a, b) => a.date.localeCompare(b.date)
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: defaultWidth,
      className: 'header-transaction-amount',
      align: 'center',
      sorter: (a, b) => a.startTime.localeCompare(b.startTime)
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      width: defaultWidth,
      className: 'header-transaction-amount',
      align: 'center',
      sorter: (a, b) => a.endTime.localeCompare(b.endTime)
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: defaultWidth,
      className: 'header-transaction-amount',
      align: 'center',
      sorter: (a, b) => a.status - b.status,
      customRender: ({ text }) => getStatusText(text)
    },
    {
      title: '操作',
      dataIndex: 'operation',
      key: 'operation',
      width: defaultWidth,
      className: 'header-transaction-amount',
      align: 'center',
    }
  ]

  const visibleColumns = computed(() => {
    let filtered = filteredInfo.value || {};
    return columns.map(column => {
      if (filtered[column.dataIndex]) {
        return {
          ...column,
          filteredValue: filtered[column.dataIndex],
        };
      }
      return column;
    });
  });

  const filteredData = computed(() => {
    return tableData.value
  });

    // 处理表格变化
  const handleTableChange = (newPagination, newFilters, sorter) => {
    // 更新分页配置
    pagination.value = newPagination;

    // 更新filters状态
    filteredInfo.value = newFilters;

    pagination.value.total = filteredData.value.length;
  };

  const getStatusText = (status) => {
    switch (status) {
      case 0:
        return '任务创建完成';
      case 1:
        return '等待执行';
      case 2:
        return '执行中';
      case 3:
        return '执行完成';
      case 4:
        return '执行失败';
      default:
        return '未知状态';
    }
  };

  const symFilterOption = (input, option) => {
    return option.value.toLowerCase().indexOf(input.toLowerCase()) >= 0;
  };

  const handleSecurityTypeChange = (type) => {
    securityType.value = type;
    selectSym.value = '';
    hasSymbol.value = false;
    selectDate.value = '';
    hasDate.value = false;
  };

  const selectSymItem = async (item) => {
    securityType.value = getSecurityType(item)
    hasSymbol.value = true
  };

  const dateFilterOption = (input, option) => {
    // return option.value.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    return option.value.startsWith(input);
  };

  const selectDateItem = async (item) => {
    hasDate.value = true
  };

  const startTimeFilterOption = (input, option) => {
    // return option.value.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    return option.value.startsWith(input);
  };

  const endTimeFilterOption = (input, option) => {
    // return option.value.toLowerCase().indexOf(input.toLowerCase()) >= 0;
    return option.value.startsWith(input);
  };

  const startTimeSelect = (item) => {
    if (item > endTime.value) {
      createMessage.info('开始时间不能大于结束时间');
      startTime.value = '09:30:00';
      return;
    }
    startTime.value = item;
  };

  const endTimeSelect = (item) => {
    console.log(item, startTime.value)
    if (item < startTime.value) {
      createMessage.info('结束时间不能小于开始时间');
      endTime.value = '15:00:00';
      return;
    }
    endTime.value = item;
  };
  const onDelete = (sym, date, startTime, endTime) => {
    let params = {
      sym: sym,
      date: date,
      start: startTime,
      end: endTime
    }
    deleteTask(params).then((res) => {
      if (res.code == 0) {
        createMessage.success('删除成功');
        getTasks().then((res) => {
          if (res.code == 0) {
            tableData.value = res.data
          }
        })
      } else {
        createMessage.info('删除失败');
      }
    })
  }

  const create_task = () => {
    let params = {
      sym: selectSym.value,
      date: selectDate.value,
      start: startTime.value,
      end: endTime.value
    }

    createTask(params).then((res) => {
      if (res.code == 0) {
        createMessage.success('创建成功');
        getTasks().then((res) => {
          if (res.code == 0) {
            tableData.value = res.data
          }
        })
      } else {
        createMessage.info('创建失败');
      }
    })
  }

  const get_tasks_data = () => {
    loading.value = true
    getSyms().then((res) => {
      res.data.forEach(item => {
          symsData.value.push(toSymbolOption(item))
        })
    }).catch((err) => {
      console.log(err)
    })

    getDates().then((res) => {
      res.data.forEach(item => {
          datesData.value.push({
            value: item,
            label: item
          })
        })
    }).catch((err) => {
      console.log(err)
    }).finally(() => {
      loading.value = false
    })

    getTasks().then((res) => {
      if (res.code == 0) {
        tableData.value = res.data.sort((a, b) => b.createtime.localeCompare(a.createtime))
      } else {
        createMessage.info('获取数据失败');
      }
    })
  }

  get_tasks_data();

  function generateTimeList(start, end) {
    let startTime = new Date(`1970-01-01T${start}Z`);
    let endTime = new Date(`1970-01-01T${end}Z`);
    let timeList = [];

    while (startTime <= endTime) {
      timeList.push(new Date(startTime).toISOString().substr(11, 8));
      startTime.setSeconds(startTime.getSeconds() + 1);
    }

    return timeList;
  }

  let intervalId; // 用于存储定时器ID
  onMounted(() => {
    let am_time_list = generateTimeList('09:30', '11:30');
    am_time_list.forEach(item => {
      timeList.value.push({
        value: item,
        label: item
      })
    })
    let pm_time_list = generateTimeList('13:00', '15:00');
    pm_time_list.forEach(item => {
      timeList.value.push({
        value: item,
        label: item
      })
    })

    intervalId = setInterval(() => {
      getTasks().then((res) => {
        if (res.code == 0) {
          tableData.value = res.data.sort((a, b) => b.createtime.localeCompare(a.createtime))
        } else {
          createMessage.info('获取数据失败');
        }
      })
    }, 5000); // 30秒
  })

  onUnmounted(() => {
    clearInterval(intervalId);
  });
</script>
<style lang="less" scoped>
  .filter-mode {
    padding: 12px 14px;
    display: grid;
    grid-template-columns: repeat(6, minmax(130px, 1fr));
    gap: 10px;
    align-items: end;

    .filter-item {
      min-width: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      align-items: stretch;
      gap: 5px;

      :deep(.ant-select) {
        width: 100% !important;
      }

      :deep(.ant-btn) {
        width: 100%;
      }

      .item-name {
        padding: 0 10px;
      }
    }
  }

  .security-filter-panel {
    background: #f5f7fa;
    border: 1px solid #e1e6ed;
    border-radius: 6px;
    box-sizing: border-box;
  }

  @media (max-width: 1200px) {
    .filter-mode {
      grid-template-columns: repeat(3, minmax(150px, 1fr));
    }
  }

  @media (max-width: 680px) {
    .filter-mode {
      grid-template-columns: minmax(0, 1fr);
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
    .empty-mode {
      height: calc(100vh - 300px);
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
  :deep(.ant-table-thead) {
    .header-transaction-amount {
      background-color: rgba(255, 241, 220, 0.4); /* 淡米色 */
    }
    .header-transaction-OIR {
      background-color: rgba(228, 255, 228, 0.4); /* 淡灰绿 */
    }
    .header-transaction-TIR {
      background-color: rgba(207, 244, 244, 0.4); /* 浅灰橙 */
    }
    .header-transaction-OCR {
      background-color: rgba(209, 236, 245, 0.4); /* 浅灰蓝 */
    }
    .header-transaction-ACR {
      background-color: rgba(246, 228, 246, 0.4); /* 浅灰紫 */
    }
    .header-transaction-AIT {
      background-color: rgba(233, 254, 254, 0.4); /* 浅灰蓝绿 */
    }
    .header-transaction-impact {
      background-color: rgba(253, 226, 230, 0.4); /* 淡灰粉 */
    }
    .header-transaction-fluc {
      background-color: rgba(252, 239, 222, 0.4); /* 淡灰棕 */
    }
    .header-transaction-pnl {
      background-color: rgba(225, 254, 245, 0.4);
    }
    .header-transaction-vwap {
      background-color: #c9adf80c;
    }
  }
</style>
