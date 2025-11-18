<script setup>
import CommonPage from '@/components/page/CommonPage.vue'
</script>

<template>
  <CommonPage show-footer title="脚本爬虫平台">
    <div style="padding:24px;">
      <p style="font-size:14px;line-height:1.8;">
        当前项目内置的「脚本爬虫平台」功能已移除，爬虫任务统一改为由 <strong>青龙面板</strong> 管理与调度。
      </p>
      <p style="font-size:14px;line-height:1.8;margin-top:8px;">
        如需新增、修改或查看爬虫任务，请登录青龙面板进行操作。后端 API 中已不再暴露 `/api/v1/crawler/*` 相关接口。
      </p>
    </div>
  </CommonPage>
</template>
