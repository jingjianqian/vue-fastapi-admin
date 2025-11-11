/** 重置样式 */
import '@/styles/reset.css'
import 'uno.css'
import '@/styles/global.scss'

import { createApp } from 'vue'
import { setupRouter } from '@/router'
import { setupStore } from '@/store'
import App from './App.vue'
import { setupDirectives } from './directives'
import { useResize } from '@/utils'
import i18n from '~/i18n'

async function setupApp() {
  const app = createApp(App)

  setupStore(app)

  await setupRouter(app)
  setupDirectives(app)
  app.use(useResize)
  app.use(i18n)
  app.mount('#app')
  
  // 调试：将 app 和 store 暴露到 window 对象
  if (import.meta.env.DEV) {
    window.__APP__ = app
    // 通过 _context 访问 pinia
    const appContext = app._context
    window.__PINIA__ = appContext?.config?.globalProperties?.$pinia || appContext?.provides?.pinia
    // 直接暴露 router
    window.__ROUTER__ = appContext?.config?.globalProperties?.$router
    console.log('[Debug] window.__APP__, __PINIA__, __ROUTER__ 已暴露')
  }
}

setupApp()
