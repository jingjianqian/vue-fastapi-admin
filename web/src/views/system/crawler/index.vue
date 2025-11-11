<script setup>
import { h, ref } from 'vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NSelect, NSwitch, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import api from '@/api'

const tableRef = ref(null)

const sourceOptions = [
  { label: 'we123_miniprogram', value: 'we123_miniprogram' },
]

const queryItems = ref({ status: null, source: null })

const createVisible = ref(false)
const createLoading = ref(false)
const createForm = ref({
  name: '',
  source: 'we123_miniprogram',
  start_id: 1,
  is_loop: false,
  max_consecutive_404: 500,
  concurrency: 1,
  delay_ms: 0,
  max_retries: 1,
  proxy: '',
})

const editVisible = ref(false)
const editLoading = ref(false)
const editForm = ref({ id: 0, is_loop: false, max_consecutive_404: 500, concurrency: 1, delay_ms: 0, max_retries: 1, proxy: '' })

const columns = [
  { title: 'ID', key: 'id', width: 80, align: 'center' },
  { title: '名称', key: 'name', width: 180, align: 'center', ellipsis: { tooltip: true } },
  { title: '来源', key: 'source', width: 160, align: 'center' },
  { title: '状态', key: 'status', width: 120, align: 'center', render(row) {
    const map = { idle: 'default', running: 'success', stopped: 'warning', finished: 'info', error: 'error' }
    return h(NTag, { type: map[row.status] || 'default' }, { default: () => row.status })
  } },
  { title: '起始ID', key: 'start_id', width: 90, align: 'center' },
  { title: '下一ID', key: 'next_id', width: 90, align: 'center' },
  { title: '404计数', key: 'consecutive_404', width: 90, align: 'center' },
  { title: '404阈值', key: 'max_consecutive_404', width: 90, align: 'center' },
  { title: '并发', key: 'concurrency', width: 80, align: 'center' },
  { title: '延迟ms', key: 'delay_ms', width: 90, align: 'center' },
  { title: '重试', key: 'max_retries', width: 80, align: 'center' },
  { title: '代理', key: 'proxy', width: 180, align: 'center', ellipsis: { tooltip: true } },
  { title: '最后运行', key: 'last_run_at', width: 170, align: 'center' },
  { title: '操作', key: 'actions', width: 240, align: 'center', fixed: 'right', render(row) {
    return [
      h(NButton, { size: 'small', type: 'success', style: 'margin-right: 8px;', onClick: () => handleStart(row) }, { default: () => '启动', icon: () => h(TheIcon, { icon: 'mdi:play' }) }),
      h(NButton, { size: 'small', type: 'warning', style: 'margin-right: 8px;', onClick: () => handleStop(row) }, { default: () => '停止', icon: () => h(TheIcon, { icon: 'mdi:stop' }) }),
      h(NButton, { size: 'small', type: 'primary', onClick: () => openEdit(row) }, { default: () => '配置', icon: () => h(TheIcon, { icon: 'material-symbols:settings' }) }),
    ]
  }},
]

async function getList(params) {
  const res = await api.getCrawlerTasks(params)
  return res
}

function handleAdd() {
  createVisible.value = true
}

async function handleCreate() {
  try {
    createLoading.value = true
    const payload = { ...createForm.value }
    if (!payload.proxy) delete payload.proxy
    await api.createCrawlerTask(payload)
    window.$message.success('创建成功')
    createVisible.value = false
    tableRef.value?.handleSearch()
  } finally {
    createLoading.value = false
  }
}

async function handleStart(row) {
  await api.startCrawlerTask({ id: row.id })
  window.$message.success('已启动')
  tableRef.value?.handleSearch()
}

async function handleStop(row) {
  await api.stopCrawlerTask({ id: row.id })
  window.$message.success('已停止')
  tableRef.value?.handleSearch()
}

function openEdit(row) {
  editForm.value = {
    id: row.id,
    is_loop: row.is_loop,
    max_consecutive_404: row.max_consecutive_404,
    concurrency: row.concurrency,
    delay_ms: row.delay_ms,
    max_retries: row.max_retries,
    proxy: row.proxy || '',
  }
  editVisible.value = true
}

async function handleUpdate() {
  try {
    editLoading.value = true
    const payload = { ...editForm.value }
    if (!payload.proxy) payload.proxy = null
    await api.updateCrawlerTask(payload)
    window.$message.success('已更新')
    editVisible.value = false
    tableRef.value?.handleSearch()
  } finally {
    editLoading.value = false
  }
}

async function handleSync() {
  await api.syncOdsToWechat({ only_new: true, overwrite: false, include_no_appid: false, limit: 500 })
  window.$message.success('ODS 同步完成')
}
</script>

<template>
  <CommonPage show-footer title="爬虫管理">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建任务
      </NButton>
      <NButton class="ml-10" @click="handleSync">
        <TheIcon icon="mdi:database-sync-outline" :size="18" class="mr-5" />ODS→小程序 同步
      </NButton>
    </template>

    <CrudTable ref="tableRef" :columns="columns" :query-items="queryItems" :get-data="getList" :scroll-x="1700">
      <template #queryBar>
        <QueryBarItem label="来源">
          <NSelect v-model:value="queryItems.source" :options="sourceOptions" clearable :to="'body'" />
        </QueryBarItem>
        <QueryBarItem label="状态">
          <NSelect v-model:value="queryItems.status" :options="[
            { label: 'idle', value: 'idle' },
            { label: 'running', value: 'running' },
            { label: 'stopped', value: 'stopped' },
            { label: 'finished', value: 'finished' },
            { label: 'error', value: 'error' },
          ]" clearable :to="'body'" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>

  <!-- 创建 -->
  <CrudModal v-model:visible="createVisible" title="创建任务" :loading="createLoading" @save="handleCreate" width="700px">
    <NForm :model="createForm" label-placement="left" :label-width="130">
      <NFormItem label="任务名称"><NInput v-model:value="createForm.name" placeholder="例如：we123全量" /></NFormItem>
      <NFormItem label="来源"><NSelect v-model:value="createForm.source" :options="sourceOptions" :to="'body'" /></NFormItem>
      <NFormItem label="起始ID"><NInputNumber v-model:value="createForm.start_id" :min="1" /></NFormItem>
      <NFormItem label="循环"><NSwitch v-model:value="createForm.is_loop" /></NFormItem>
      <NFormItem label="404阈值"><NInputNumber v-model:value="createForm.max_consecutive_404" :min="1" :max="10000" /></NFormItem>
      <NFormItem label="并发"><NInputNumber v-model:value="createForm.concurrency" :min="1" :max="8" /></NFormItem>
      <NFormItem label="延迟(ms)"><NInputNumber v-model:value="createForm.delay_ms" :min="0" :max="60000" /></NFormItem>
      <NFormItem label="重试次数"><NInputNumber v-model:value="createForm.max_retries" :min="1" :max="5" /></NFormItem>
      <NFormItem label="代理"><NInput v-model:value="createForm.proxy" placeholder="http://host:port，可留空" /></NFormItem>
    </NForm>
  </CrudModal>

  <!-- 配置 -->
  <CrudModal v-model:visible="editVisible" title="编辑配置" :loading="editLoading" @save="handleUpdate" width="700px">
    <NForm :model="editForm" label-placement="left" :label-width="130">
      <NFormItem label="循环"><NSwitch v-model:value="editForm.is_loop" /></NFormItem>
      <NFormItem label="404阈值"><NInputNumber v-model:value="editForm.max_consecutive_404" :min="1" :max="10000" /></NFormItem>
      <NFormItem label="并发"><NInputNumber v-model:value="editForm.concurrency" :min="1" :max="8" /></NFormItem>
      <NFormItem label="延迟(ms)"><NInputNumber v-model:value="editForm.delay_ms" :min="0" :max="60000" /></NFormItem>
      <NFormItem label="重试次数"><NInputNumber v-model:value="editForm.max_retries" :min="1" :max="5" /></NFormItem>
      <NFormItem label="代理"><NInput v-model:value="editForm.proxy" placeholder="http://host:port，可留空" /></NFormItem>
    </NForm>
  </CrudModal>
</template>
