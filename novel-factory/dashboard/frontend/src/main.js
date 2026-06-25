import { createApp } from 'vue'
import App from './App.vue'
import './assets/style.css'
import './assets/readable-typography.css'
import { initTextScale } from './utils/textScale.js'

initTextScale()

const app = createApp(App)
app.mount('#app')