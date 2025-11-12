<script setup>
import { h, ref, onMounted, onUnmounted } from 'vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NList, NListItem, NCard, NModal, NTag, NSpin, NDivider, NSwitch } from 'naive-ui'
import CommonPage from '@/components/page/CommonPage.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'

const tableRef = ref(null)
const scripts = ref([])
const total = ref(0)
const pagination = ref({ page: 1, pageSize: 10 })

const current = ref(null)
const editor = ref({ id: 0, name: '', desc: '', code: "print('hello world')\n", requirements: '', enabled: true })
const editVisible = ref(false)
const editLoading = ref(false)

const runLoading = ref(false)
const lastRun = ref(null)
const logs = ref({ stdout: '', stderr: '' })

const settings = ref({ retention_days: 30, default_timeout_sec: 600, max_log_bytes: 1048576 })

// we123
const we123Cfg = ref({ start_id: 1, loop: false, max_404_span: 500, delay_sec: 3, ua: '', proxy: '' })
const we123Status = ref(null)
const we123XpathsText = ref('')
const we123Loading = ref(false)

// pip
const pipList = ref([])
const pipQuery = ref('')
const pipInfo = ref(null)
const pipLoading = ref(false)

async function fetchList () {
  if (tableRef.value?.handleSearch) {
    await tableRef.value.handleSearch()
  }
}

let we123Timer = null
onMounted(async () => {
  await fetchList()
  const s = await api.crawlerSettingsGet()
  settings.value = s.data
  await refreshPip()
  // we123 init
  try { await fetchWe123Status(); } catch (e) {}
  try { await fetchWe123Xpaths(); } catch (e) {}
  we123Timer = setInterval(() => {
    fetchWe123Status().catch(() => {})
  }, 10000)
})
onUnmounted(() => { if (we123Timer) { clearInterval(we123Timer); we123Timer = null } })

function openCreate () {
  editor.value = { id: 0, name: '', desc: '', code: "print('hello world')\n", requirements: '', enabled: true }
  editVisible.value = true
}

async function openEdit (row) {
  const res = await api.crawlerScriptGet({ id: row.id })
  editor.value = res.data
  editVisible.value = true
}

async function saveScript () {
  try {
    editLoading.value = true
if (editor.value.id) {
      await api.crawlerScriptUpdate(editor.value)
    } else {
      const ret = await api.crawlerScriptCreate(editor.value)
      editor.value.id = ret.data?.id
    }
    window.$message.success('已保存')
    editVisible.value = false
    await fetchList()
  } finally {
    editLoading.value = false
  }
}

async function removeScript (row) {
  await api.crawlerScriptDelete({ id: row.id })
  window.$message.success('已删除')
  await fetchList()
}

async function runScript (row) {
  try {
    runLoading.value = true
    const ret = await api.crawlerScriptRun({ id: row.id })
    lastRun.value = { id: ret.data?.run_id, status: ret.data?.status }
    await pollLogsUntilDone()
  } finally {
    runLoading.value = false
  }
}

async function refreshLogs () {
  if (!lastRun.value?.id) return
  try {
    const st = await api.crawlerScriptRunStatus({ run_id: lastRun.value.id })
    const lg = await api.crawlerScriptRunLogs({ run_id: lastRun.value.id })
    lastRun.value = st.data
    logs.value = lg.data
  } catch (e) {
    // 忽略一次错误，避免打断轮询
  }
}

// pip
async function refreshPip () {
  pipLoading.value = true
  try {
    const r = await api.crawlerPipList()
    pipList.value = r.data || []
  } finally {
    pipLoading.value = false
  }
}

async function pipSearch () {
  if (!pipQuery.value) { pipInfo.value = null; return }
  pipLoading.value = true
  try {
    const r = await api.crawlerPipShow({ name: pipQuery.value })
    pipInfo.value = r.data
  } catch (e) {
    pipInfo.value = null
  } finally {
    pipLoading.value = false
  }
}

async function pipInstall (name) {
  pipLoading.value = true
  try {
    await api.crawlerPipInstall({ name })
    window.$message.success('安装完成（请检查日志）')
    await refreshPip()
  } finally {
    pipLoading.value = false
  }
}

async function saveSettings () {
  await api.crawlerSettingsUpdate(settings.value)
  window.$message.success('设置已更新')
}

// we123 apis
async function fetchWe123Status () {
  const r = await api.we123Status()
  we123Status.value = r.data
}
async function fetchWe123Xpaths () {
  const r = await api.we123GetXpaths()
  we123XpathsText.value = JSON.stringify(r.data || {}, null, 2)
}
async function saveWe123Xpaths () {
  try {
    const payload = JSON.parse(we123XpathsText.value || '{}')
    await api.we123UpdateXpaths(payload)
    window.$message.success('XPath 已更新')
  } catch (e) {
    window.$message.error('JSON 解析失败，请检查格式')
  }
}
async function startWe123 () {
  try {
    we123Loading.value = true
    const payload = { ...we123Cfg.value }
    // 清理空字符串为 null
    if (!payload.ua) payload.ua = null
    if (!payload.proxy) payload.proxy = null
    await api.we123Start(payload)
    window.$message.success('任务已启动')
    await fetchWe123Status()
  } finally {
    we123Loading.value = false
  }
}
async function stopWe123 () {
  try {
    we123Loading.value = true
    await api.we123Stop()
    window.$message.success('任务已停止')
    await fetchWe123Status()
  } finally {
    we123Loading.value = false
  }
}
async function pollLogsUntilDone () {
  // 最多轮询 30 次（约 30 秒），直到状态不是 running/queued
  for (let i = 0; i < 30; i++) {
    await refreshLogs()
    const st = lastRun.value?.status
    if (st && st !== 'running' && st !== 'queued') {
      break
    }
    await new Promise(r => setTimeout(r, 1000))
  }
}
</script>

<template>
  <CommonPage show-footer title="脚本爬虫平台">
    <template #action>
      <NButton type="primary" @click="openCreate"><TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建脚本</NButton>
      <NButton class="ml-10" @click="fetchList"><TheIcon icon="mdi:refresh" :size="18" class="mr-5" />刷新</NButton>
    </template>

    <div class="grid" style="display:grid;grid-template-columns: 1fr 1fr;grid-gap:12px;">
      <NCard title="脚本列表">
<CrudTable ref="tableRef" :columns="[
          { title: 'ID', key: 'id', width: 80, align: 'center' },
          { title: '名称', key: 'name' },
          { title: '启用', key: 'enabled', render(row){ return h(NTag, { type: row.enabled ? 'success' : 'default' }, { default: () => row.enabled ? '是' : '否' }) } },
          { title: '更新时间', key: 'updated_at' },
          { title: '操作', key: 'actions', width: 260, align: 'center', render(row){
            return [
              h(NButton, { size: 'small', type: 'success', style: 'margin-right:8px;', onClick: ()=>runScript(row) }, { default: ()=>'运行', icon: ()=>h(TheIcon, { icon:'mdi:play' }) }),
              h(NButton, { size: 'small', type: 'primary', style: 'margin-right:8px;', onClick: ()=>openEdit(row) }, { default: ()=>'编辑', icon: ()=>h(TheIcon, { icon:'material-symbols:edit' }) }),
              h(NButton, { size: 'small', type: 'error', onClick: ()=>removeScript(row) }, { default: ()=>'删除', icon: ()=>h(TheIcon, { icon:'mdi:delete' }) }),
            ]
          }}
        ]" :get-data="async ({ page, pageSize })=>{ pagination.page=page; pagination.pageSize=pageSize; const r=await api.crawlerScriptList({ page, page_size: pageSize }); return r }" />
      </NCard>

      <NCard title="运行与日志" :segmented="{content:true,footer:true}">
        <template #header-extra>
          <NButton size="small" @click="refreshLogs">刷新日志</NButton>
        </template>
        <NSpin :show="runLoading">
          <div style="display:flex;gap:12px;">
            <div style="flex:1;">
              <div style="font-weight:600">STDOUT</div>
              <pre style="white-space:pre-wrap;max-height:300px;overflow:auto">{{ logs.stdout }}</pre>
            </div>
            <div style="flex:1;">
              <div style="font-weight:600">STDERR</div>
              <pre style="white-space:pre-wrap;max-height:300px;overflow:auto;color:#c00">{{ logs.stderr }}</pre>
            </div>
          </div>
        </NSpin>
        <template #footer>
<div>状态：{{ (lastRun && lastRun.status) || '-' }}，用时：{{ (lastRun && lastRun.duration_ms) || '-' }}ms</div>
        </template>
      </NCard>
    </div>

    <NDivider />
    <div class="grid" style="display:grid;grid-template-columns: 2fr 1fr;grid-gap:12px;">
      <NCard title="依赖管理">
        <div style="display:flex;gap:8px;align-items:center;">
          <NInput v-model:value="pipQuery" placeholder="输入包名，如 requests" style="max-width:320px" />
          <NButton @click="pipSearch">搜索</NButton>
          <NButton tertiary @click="refreshPip">刷新已安装</NButton>
        </div>
        <NSpin :show="pipLoading">
          <div v-if="pipInfo" class="mt-10">
            <div style="font-weight:600">{{ pipInfo.name }} <NTag type="info">{{ pipInfo.version }}</NTag></div>
            <div class="mt-5" style="color:#888">{{ pipInfo.summary }}</div>
            <div class="mt-5">
              <NButton size="small" type="primary" @click="pipInstall(pipInfo.name)">安装/升级</NButton>
            </div>
          </div>
          <NDivider />
          <div>
            <div style="font-weight:600">已安装</div>
            <ul>
              <li v-for="p in pipList" :key="p.name">{{ p.name }} <NTag size="small">{{ p.version }}</NTag></li>
            </ul>
          </div>
        </NSpin>
      </NCard>

      <NCard title="平台设置">
        <NForm :model="settings" label-placement="left" :label-width="130">
          <NFormItem label="日志保留天数"><NInputNumber v-model:value="settings.retention_days" :min="1" :max="365" /></NFormItem>
          <NFormItem label="默认超时(秒)"><NInputNumber v-model:value="settings.default_timeout_sec" :min="10" :max="86400" /></NFormItem>
          <NFormItem label="日志最大字节"><NInputNumber v-model:value="settings.max_log_bytes" :min="1024" :max="10485760" /></NFormItem>
          <NButton type="primary" @click="saveSettings">保存设置</NButton>
        </NForm>
      </NCard>
    </div>

    <NDivider />
    <NCard title="we123 爬虫">
      <NSpin :show="we123Loading">
        <div style="display:grid;grid-template-columns: 1fr 1fr;gap:12px;align-items:start;">
          <div>
            <NForm :model="we123Cfg" label-placement="left" :label-width="130">
              <NFormItem label="起始ID"><NInputNumber v-model:value="we123Cfg.start_id" :min="1" /></NFormItem>
              <NFormItem label="循环模式"><NSwitch v-model:value="we123Cfg.loop" /></NFormItem>
              <NFormItem label="连续404阈值"><NInputNumber v-model:value="we123Cfg.max_404_span" :min="10" :max="100000" /></NFormItem>
              <NFormItem label="最小间隔(秒)"><NInputNumber v-model:value="we123Cfg.delay_sec" :min="1" :max="60" :step="0.5" /></NFormItem>
              <NFormItem label="User-Agent"><NInput v-model:value="we123Cfg.ua" placeholder="可留空使用默认" /></NFormItem>
              <NFormItem label="代理"><NInput v-model:value="we123Cfg.proxy" placeholder="http://host:port 或鉴权代理" /></NFormItem>
              <div>
                <NButton type="primary" :disabled="we123Status?.running" @click="startWe123">启动</NButton>
                <NButton class="ml-10" type="warning" :disabled="!we123Status?.running" @click="stopWe123">停止</NButton>
                <NButton class="ml-10" @click="fetchWe123Status">刷新状态</NButton>
              </div>
            </NForm>
            <div class="mt-10">
              <div style="font-weight:600">当前状态</div>
              <ul style="line-height:1.8">
                <li>运行中：{{ we123Status?.running ? '是' : '否' }}</li>
                <li>last_id：{{ we123Status?.last_id ?? '-' }}</li>
                <li>last_ok_id：{{ we123Status?.last_ok_id ?? '-' }}</li>
                <li>连续404：{{ we123Status?.consecutive_404 ?? 0 }}</li>
                <li>成功/404/错误：{{ we123Status?.ok_count ?? 0 }} / {{ we123Status?.not_found_count ?? 0 }} / {{ we123Status?.error_count ?? 0 }}</li>
                <li>最近错误：{{ we123Status?.last_error || '-' }}</li>
              </ul>
            </div>
          </div>
          <div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <div style="font-weight:600">XPath 配置（JSON）</div>
              <div>
                <NButton size="small" type="primary" @click="saveWe123Xpaths">保存</NButton>
                <NButton size="small" class="ml-10" @click="fetchWe123Xpaths">重置</NButton>
              </div>
            </div>
            <NInput v-model:value="we123XpathsText" type="textarea" :rows="16" placeholder='{"name":"//h1/text()", ...}' />
          </div>
        </div>
      </NSpin>
    </NCard>

    <CrudModal v-model:visible="editVisible" title="编辑脚本" :loading="editLoading" @save="saveScript" width="900px">
      <NForm :model="editor" label-placement="left" :label-width="100">
        <NFormItem label="名称"><NInput v-model:value="editor.name" /></NFormItem>
        <NFormItem label="描述"><NInput v-model:value="editor.desc" /></NFormItem>
        <NFormItem label="代码"><NInput v-model:value="editor.code" type="textarea" :rows="12" /></NFormItem>
        <NFormItem label="依赖"><NInput v-model:value="editor.requirements" type="textarea" :rows="4" placeholder="每行一个包名，可留空" /></NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>
