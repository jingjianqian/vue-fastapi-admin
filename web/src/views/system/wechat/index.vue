<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import { NButton, NForm, NFormItem, NInput, NPopconfirm, NSelect, NImage, NSwitch, NTag } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { renderIcon, formatDateTime } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

const $table = ref(null)
const vPermission = resolveDirective('permission')

const publishStatusOptions = [
  { label: '草稿', value: 'draft' },
  { label: '审核中', value: 'review' },
  { label: '已发布', value: 'published' },
  { label: '禁用', value: 'disabled' },
]

const queryItems = ref({ name: null, appid: null, publish_status: null })

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
  refresh: () => $table.value?.handleSearch(),
})

onMounted(() => {
  $table.value?.handleSearch()
})

const columns = [
  { title: 'ID', key: 'id', width: 60, align: 'center' },
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
          $table.value?.handleSearch()
        },
      })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
        withDirectives(
          h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              style: 'margin-right: 8px;',
              onClick: () => handleEdit(row),
            },
            { default: () => '编辑', icon: renderIcon('material-symbols:edit', { size: 16 }) }
          ),
          [[vPermission, 'post/api/v1/wechat/update']]
        ),
        h(
          NPopconfirm,
          { onPositiveClick: () => handleDelete({ id: row.id }, false) },
          {
            trigger: () =>
              withDirectives(
                h(
                  NButton,
                  { size: 'small', type: 'error', style: 'margin-right: 8px;' },
                  { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }
                ),
                [[vPermission, 'delete/api/v1/wechat/delete']]
              ),
          }
        ),
      ]
    },
  },
]

async function getList(params) {
  return api.getWechatList(params)
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
      <NButton v-permission="'post/api/v1/wechat/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建小程序
      </NButton>
    </template>

    <template #content>
      <CrudTable ref="$table" :columns="columns" :query-items="queryItems" :get-data="getList" :scroll-x="1400">
        <template #queryBar>
          <QueryBarItem label="名称">
            <NInput v-model:value="queryItems.name" placeholder="按名称搜索" />
          </QueryBarItem>
          <QueryBarItem label="AppID">
            <NInput v-model:value="queryItems.appid" placeholder="按AppID搜索" />
          </QueryBarItem>
          <QueryBarItem label="状态">
            <NSelect v-model:value="queryItems.publish_status" :options="publishStatusOptions" clearable />
          </QueryBarItem>
        </template>
      </CrudTable>
    </template>
  </CommonPage>

  <CrudModal :visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave">
    <NForm ref="modalFormRef" :model="modalForm" :rules="rules" label-placement="left" :label-width="100">
      <NFormItem label="名称" path="name">
        <NInput v-model:value="modalForm.name" placeholder="请输入小程序名称" />
      </NFormItem>
      <NFormItem label="AppID" path="appid">
        <NInput v-model:value="modalForm.appid" placeholder="请输入 AppID" />
      </NFormItem>
      <NFormItem label="AppSecret" path="secret">
        <NInput v-model:value="modalForm.secret" placeholder="请输入 AppSecret" />
      </NFormItem>
      <NFormItem label="Logo URL" path="logo_url">
        <NInput v-model:value="modalForm.logo_url" placeholder="https://..." />
      </NFormItem>
      <NFormItem label="二维码 URL" path="qrcode_url">
        <NInput v-model:value="modalForm.qrcode_url" placeholder="https://..." />
      </NFormItem>
      <NFormItem label="版本" path="version">
        <NInput v-model:value="modalForm.version" placeholder="如 1.0.0" />
      </NFormItem>
      <NFormItem label="状态" path="publish_status">
        <NSelect v-model:value="modalForm.publish_status" :options="publishStatusOptions" />
      </NFormItem>
      <NFormItem label="描述" path="description">
        <NInput v-model:value="modalForm.description" type="textarea" :autosize="{ minRows: 3 }" />
      </NFormItem>
    </NForm>
  </CrudModal>
</template>