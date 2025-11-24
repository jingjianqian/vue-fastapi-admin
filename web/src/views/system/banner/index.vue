<script setup>
import { h, ref } from 'vue'
import { NButton, NForm, NFormItem, NInput, NImage, NSwitch, NInputNumber, NUpload, NSpace } from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { renderIcon, formatDateTime } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'

const tableRef = ref(null)

const queryItems = ref({ 
  title: null,
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
  name: 'Banner',
  initForm: { sort: 0, is_online: true },
  doCreate: api.createBanner,
  doDelete: api.deleteBanner,
  doUpdate: api.updateBanner,
  refresh: () => tableRef.value?.handleSearch(),
})

// 上传功能
const handleUpload = async ({ file, onFinish, onError }) => {
  try {
    const formData = new FormData()
    formData.append('file', file.file)
    const res = await api.uploadBannerFile(formData)
    if (res && res.data) {
      // 数据库存相对路径
      modalForm.value.image_url = res.data.path
      window.$message.success('上传成功')
    }
    onFinish()
  } catch (error) {
    window.$message.error('上传失败: ' + (error.message || '未知错误'))
    onError()
  }
}

const columns = [
  { 
    title: 'ID', 
    key: 'id', 
    width: 60, 
    align: 'center',
    sorter: true,
  },
  { title: '标题', key: 'title', width: 180, align: 'center', ellipsis: { tooltip: true } },
  {
    title: '图片',
    key: 'image_url',
    width: 160,
    align: 'center',
    render(row) {
      const src = row.image_url_public || row.image_url
      return src ? h(NImage, { src, width: 120, height: 60, objectFit: 'cover' }) : null
    },
  },
  { title: '排序', key: 'sort', width: 80, align: 'center' },
  {
    title: '上线',
    key: 'is_online',
    width: 90,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        value: row.is_online,
        onUpdateValue: async (val) => {
          const formData = new FormData()
          formData.append('id', row.id)
          formData.append('title', row.title)
          formData.append('image_url', row.image_url)
          formData.append('sort', row.sort)
          formData.append('is_online', val)
          if (row.app_id) formData.append('app_id', row.app_id)
          if (row.jump_appid) formData.append('jump_appid', row.jump_appid)
          if (row.jump_path) formData.append('jump_path', row.jump_path)
          
          await api.updateBanner(formData)
          $message.success('状态已更新')
          tableRef.value?.handleSearch()
        },
      })
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
    title: '操作',
    key: 'actions',
    width: 180,
    align: 'center',
    fixed: 'right',
    render(row) {
      return [
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
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            onClick: () => handleDelete({ id: row.id }, false),
          },
          { default: () => '删除', icon: renderIcon('material-symbols:delete-outline', { size: 16 }) }
        ),
      ]
    },
  },
]

async function getList(params) {
  return await api.getBannerList(params)
}

const rules = {
  title: [{ required: true, message: '请输入标题', trigger: ['input', 'blur'] }],
  image_url: [{ required: true, message: '请上传图片', trigger: ['input', 'blur'] }],
}
</script>

<template>
  <CommonPage show-footer title="Banner管理">
    <template #action>
      <NButton type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建Banner
      </NButton>
    </template>

    <CrudTable ref="tableRef" :columns="columns" :query-items="queryItems" :get-data="getList" :scroll-x="1200">
      <template #queryBar>
        <QueryBarItem label="标题">
          <NInput v-model:value="queryItems.title" placeholder="按标题搜索" />
        </QueryBarItem>
      </template>
    </CrudTable>
  </CommonPage>

  <CrudModal v-model:visible="modalVisible" :title="modalTitle" :loading="modalLoading" @save="handleSave" width="700px">
    <NForm ref="modalFormRef" :model="modalForm" :rules="rules" label-placement="left" :label-width="110">
      <NFormItem label="标题" path="title">
        <NInput v-model:value="modalForm.title" placeholder="请输入Banner标题" />
      </NFormItem>
      
      <!-- 图片上传 -->
      <NFormItem label="图片" path="image_url">
        <NSpace vertical style="width: 100%">
          <NUpload
            :max="1"
            :custom-request="handleUpload"
            accept="image/png,image/jpeg,image/jpg,image/webp"
            list-type="image-card"
            :show-file-list="true"
          />
          <NInput v-model:value="modalForm.image_url" placeholder="或手动输入相对路径（如：uploads/banners/banner1.jpg）" />
        </NSpace>
      </NFormItem>
      
      <NFormItem label="排序" path="sort">
        <NInputNumber v-model:value="modalForm.sort" placeholder="数字越小越靠前" :min="0" style="width: 100%" />
      </NFormItem>

      <NFormItem label="跳转AppID" path="jump_appid">
        <NInput v-model:value="modalForm.jump_appid" placeholder="可选，点击跳转的小程序AppID" />
      </NFormItem>

      <NFormItem label="跳转路径" path="jump_path">
        <NInput v-model:value="modalForm.jump_path" placeholder="可选，点击跳转的小程序页面路径" />
      </NFormItem>
      
      <NFormItem label="上线状态" path="is_online">
        <NSwitch v-model:value="modalForm.is_online" />
      </NFormItem>
    </NForm>
  </CrudModal>
</template>
