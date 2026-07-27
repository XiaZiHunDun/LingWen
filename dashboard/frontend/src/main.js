import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import './assets/style.css'
import './assets/app-surfaces.css'
import './assets/readable-typography.css'
import './assets/creator-chrome.css'
import './assets/hub-chrome.css'
import { initTextScale } from './utils/textScale.js'
import { setConnectivityStore } from './api/connectivity.js'
import { useConnectivityStore } from './stores/index.js'
import { logger } from './utils/logger.js'

initTextScale()

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

const connectivityStore = useConnectivityStore()
setConnectivityStore(connectivityStore)

app.config.errorHandler = (error, instance, info) => {
  logger.error('[全局错误处理] 捕获到错误:', error)
  logger.error('组件:', instance?.$options?.name || '未知')
  logger.error('位置:', info)
}

app.config.warnHandler = (message, instance, trace) => {
  logger.warn('[全局警告处理]', message, instance, trace)
}

app.mount('#app')