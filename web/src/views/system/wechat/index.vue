<script setup>
import { h, onMounted, ref, watch, nextTick } from 'vue'
import { NButton, NForm, NFormItem, NInput, NPopconfirm, NSelect, NImage, NSwitch, NTag, NUpload, NSpace } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { renderIcon, formatDateTime } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

const tableRef = ref(null)

const publishStatusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '审核中', value: 'review' },
  { label: '已发布', value: 'published' },
  { label: '禁用', value: 'disabled' },
]

const deleteStatusOptions = [
  { label: '未删除', value: 'not_deleted' },
  { label: '已删除', value: 'deleted' },
  { label: '全部', value: 'all' },
]

const queryItems = ref({ 
  name: null, 
  appid: null, 
  publish_status: null,
  // 删除状态查询改为下拉：not_deleted | deleted | all
  delete_status: 'not_deleted',
  // 兼容后端参数，由 getList 内部转换
  include_deleted: false,
  only_deleted: false,
  order_by: 'id',
  order_direction: 'asc'
})

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '小程序',
  initForm: { publish_status: 'draft' },
  doCreate: api.createWechat,
  doDelete: api.deleteWechat,
  doUpdate: api.updateWechat,
  refresh: () => tableRef.value?.handleSearch(),
})

// 上传功能
const handleUpload = (kind) => {
  return async ({ file, onFinish, onError }) => {
    try {
      const formData = new FormData()
      formData.append('file', file.file)
      formData.append('kind', kind)
      const res = await api.uploadWechatFile(formData)
      if (res && res.data) {
        if (kind === 'logo') {
          modalForm.value.logo_url = res.data.url
        } else if (kind === 'qrcode') {
          modalForm.value.qrcode_url = res.data.url
        }
        window.$message.success('上传成功')
      }
      onFinish()
    } catch (error) {
      window.$message.error('上传失败: ' + (error.message || '未知错误'))
      onError()
    }
  }
}

// 恢复功能
const handleRestore = async (row) => {
  try {
    await api.restoreWechat({ id: row.id })
    window.$message.success('恢复成功')
    tableRef.value?.handleSearch()
  } catch (error) {
    window.$message.error('恢复失败: ' + (error.message || '未知错误'))
  }
}

onMounted(() => {
  console.log('[Wechat] onMounted 触发', { tableRef: tableRef.value })
  if (tableRef.value) {
    console.log('[Wechat] 调用 handleSearch')
    tableRef.value.handleSearch()
  } else {
    console.error('[Wechat] tableRef.value 为 null，延迟调用')
    nextTick(() => {
      console.log('[Wechat] nextTick 后的 tableRef:', tableRef.value)
      tableRef.value?.handleSearch()
    })
  }
})

// 下拉选择后自动触发查询
watch(() => queryItems.value.publish_status, () => {
  tableRef.value?.handleSearch()
})
watch(() => queryItems.value.delete_status, () => {
  tableRef.value?.handleSearch()
})

const columns = [
  { 
    title: 'ID', 
    key: 'id', 
    width: 60, 
    align: 'center',
    sorter: true,
    sortOrder: 'ascend',
    defaultSortOrder: 'ascend'
  },
  { title: '名称', key: 'name', width: 140, align: 'center', ellipsis: { tooltip: true } },
  { title: 'AppID', key: 'appid', width: 200, align: 'center', ellipsis: { tooltip: true } },
  { title: 'Secret', key: 'secret', width: 220, align: 'center', ellipsis: { tooltip: true } },
  { title: '版本', key: 'version', width: 100, align: 'center', ellipsis: { tooltip: true } },
  {
    title: '描述',
    key: 'description',
    width: 220,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: 'Logo',
    key: 'logo_url',
    width: 100,
    align: 'center',
    render(row) {
      return row.logo_url ? h(NImage, { src: row.logo_url, width: 40, height: 40, objectFit: 'cover' }) : null
    },
  },
  {
    title: '二维码',
    key: 'qrcode_url',
    width: 100,
    align: 'center',
    render(row) {
      return row.qrcode_url ? h(NImage, { src: row.qrcode_url, width: 40, height: 40, objectFit: 'cover' }) : null
    },
  },
  {
    title: '状态',
    key: 'publish_status',
    width: 110,
    align: 'center',
    render(row) {
      const map = {
        draft: { type: 'default', label: '草稿' },
        review: { type: 'warning', label: '审核中' },
        published: { type: 'success', label: '已发布' },
        disabled: { type: 'error', label: '禁用' },
      }
      const info = map[row.publish_status] || map.draft
      return h(NTag, { type: info.type }, { default: () => info.label })
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160,
    align: 'center',
    render: (row) => h('span', formatDateTime(row.created_at)),
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 160,
    align: 'center',
    render: (row) => h('span', formatDateTime(row.updated_at)),
  },
  {
    title: '删除',
    key: 'is_deleted',
    width: 80,
    align: 'center',
    render(row) {
      return h(NTag, { type: row.is_deleted ? 'error' : 'success' }, { default: () => (row.is_deleted ? '是' : '否') })
    },
  },
  {
    title: '上线',
    key: 'publish_toggle',
    width: 90,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        value: row.publish_status === 'published',
        onUpdateValue: async (val) => {
          await api.updateWechatStatus({ id: row.id, publish_status: val ? 'published' : 'disabled' })
          $message.success('状态已更新')
          tableRef.value?.handleSearch()
        },
      })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    align: 'center',
    fixed: 'right',
    render(row) {
      const buttons = []
      
      // 编辑按钮（始终显示）
      if (!row.is_deleted) {
        buttons.push(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => handleEdit(row),
            },
            { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }
          )
        )
      }
      
      // 根据 is_deleted 显示删除或恢复按钮
      if (row.is_deleted) {
        // 恢复按钮
        buttons.push(
          h(
            NPopconfirm,
            { 
              onPositiveClick: () => handleRestore(row),
              positiveText: '确定',
              negativeText: '取消'
            },
            {
              default: () => '确认要恢复该小程序吗？',
              trigger: () =>
                h(
                  NButton,
                  { size: 'small', type: 'success', style: 'margin-right: 8px;' },
                  { default: () => '恢复', icon: renderIcon('material-symbols:restore', { size: 16 }) }
                )
            }
          )
        )
      } else {
        // 删除按钮
        buttons.push(
          h(
            NPopconfirm,
            { 
              onPositiveClick: () => handleDelete({ id: row.id }, false),
              positiveText: '确定',
              negativeText: '取消'
            },
            {
              default: () => '确认要删除该小程序吗？',
              trigger: () =>
                h(
                  NButton,
                  { size: 'small', type: 'error', style: 'margin-right: 8px;' },
                  { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }
                )
            }
          )
        )
      }
      
      return buttons
    },
  },
]

async function getList(params) {
  console.log('[Wechat] getList 被调用', params)
  try {
    // 将 delete_status 转换为后端需要的 include_deleted / only_deleted
    const { delete_status, ...rest } = params || {}
    let include_deleted = false
    let only_deleted = false
    if (delete_status === 'deleted') {
      only_deleted = true
    } else if (delete_status === 'all') {
      include_deleted = true
    }
    const result = await api.getWechatList({
      ...rest,
      include_deleted,
      only_deleted,
    })
    console.log('[Wechat] getList 返回数据:', result)
    return result
  } catch (error) {
    console.error('[Wechat] getList 错误:', error)
    throw error
  }
}

const rules = {
  name: [{ required: true, message: '请输入小程序名称', trigger: ['input', 'blur'] }],
  appid: [{ required: true, message: '请输入 AppID', trigger: ['input', 'blur'] }],
  secret: [{ required: true, message: '请输入 AppSecret', trigger: ['input', 'blur'] }],
}
</script>

<template>
  <CommonPage show-footer title="小程序管理">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建小程序
      </NButton>
    </template>

<CrudTable ref="tableRef" :columns="columns" :query-items="queryItems" :get-data="getList" :scroll-x="1600">
      <template #queryBar>
        <QueryBarItem label="名称">
          <NInput v-model:value="queryItems.name" placeholder="按名称搜索" />
        </QueryBarItem>
        <QueryBarItem label="AppID">
          <NInput v-model:value="queryItems.appid" placeholder="按AppID搜索" />
        </QueryBarItem>
        <QueryBarItem label="状态">
<NSelect v-model:value="queryItems.publish_status" :options="publishStatusOptions" clearable :to="'body'" />
        </QueryBarItem>
        <QueryBarItem label="删除状态">
<NSelect v-model:value="queryItems.delete_status" :options="deleteStatusOptions" :to="'body'" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>

<CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave" width="700px">
    <NForm ref="modalFormRef" :model="modalForm" :rules="rules" label-placement="left" :label-width="110">
      <NFormItem label="名称" path="name">
        <NInput v-model:value="modalForm.name" placeholder="请输入小程序名称" />
      </NFormItem>
      <NFormItem label="AppID" path="appid">
        <NInput v-model:value="modalForm.appid" placeholder="请输入 AppID" />
      </NFormItem>
      <NFormItem label="AppSecret" path="secret">
        <NInput v-model:value="modalForm.secret" type="password" show-password-on="click" placeholder="请输入 AppSecret" />
      </NFormItem>
      
      <!-- Logo 上传 -->
      <NFormItem label="Logo" path="logo_url">
        <NSpace vertical style="width: 100%">
<NUpload
            :max="1"
            :custom-request="handleUpload('logo')"
            accept="image/png,image/jpeg,image/jpg,image/webp"
            list-type="image-card"
            :show-file-list="true"
          />
          <NInput v-model:value="modalForm.logo_url" placeholder="或手动输入 URL" />
        </NSpace>
      </NFormItem>
      
      <!-- 二维码上传 -->
      <NFormItem label="二维码" path="qrcode_url">
        <NSpace vertical style="width: 100%">
<NUpload
            :max="1"
            :custom-request="handleUpload('qrcode')"
            accept="image/png,image/jpeg,image/jpg,image/webp"
            list-type="image-card"
            :show-file-list="true"
          />
          <NInput v-model:value="modalForm.qrcode_url" placeholder="或手动输入 URL" />
        </NSpace>
      </NFormItem>
      
      <NFormItem label="版本" path="version">
        <NInput v-model:value="modalForm.version" placeholder="如 1.0.0" disabled />
      </NFormItem>
      <NFormItem label="状态" path="publish_status">
<NSelect v-model:value="modalForm.publish_status" :options="publishStatusOptions" :to="'body'" />
      </NFormItem>
      <NFormItem label="描述" path="description">
        <NInput v-model:value="modalForm.description" type="textarea" :autosize="{ minRows: 3 }" placeholder="请输入小程序描述" />
      </NFormItem>
    </NForm>
  </CrudModal>
</template>