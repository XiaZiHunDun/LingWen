import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
        ws: true,
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          // 将大型图表库拆分为独立 chunks
          if (id.includes('node_modules/echarts')) {
            return 'echarts';
          }
          if (id.includes('node_modules/mermaid')) {
            return 'mermaid';
          }
          if (id.includes('node_modules/cytoscape')) {
            return 'cytoscape';
          }
          if (id.includes('node_modules/katex')) {
            return 'katex';
          }
          if (id.includes('node_modules/naive-ui')) {
            return 'naive-ui';
          }
          if (id.includes('node_modules/vue-router')) {
            return 'vue-router';
          }
          if (id.includes('node_modules/pinia')) {
            return 'pinia';
          }
          if (id.includes('node_modules/@vicons')) {
            return 'vicons';
          }
          if (id.includes('node_modules/lodash')) {
            return 'lodash';
          }
          if (id.includes('node_modules/dayjs')) {
            return 'dayjs';
          }
          // 将其他第三方依赖合并到 vendor chunk
          // 排除可能导致循环依赖的包
          const excluded = ['mermaid', 'echarts', 'cytoscape', 'katex', 'naive-ui', 'vue-router', 'pinia', '@vicons', 'lodash', 'dayjs'];
          if (id.includes('node_modules/') && !excluded.some(e => id.includes(`node_modules/${e}`))) {
            return 'vendor';
          }
        }
      }
    },
    chunkSizeWarningLimit: 1000,
    minify: 'esbuild',
    assetsInlineLimit: 4096
  },
  root: '.'
})
