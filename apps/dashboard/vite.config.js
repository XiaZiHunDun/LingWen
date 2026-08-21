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
    target: 'es2020',
    reportCompressedSize: true,
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Named chunks: package → chunk name
          const NAMED = {
            echarts: 'echarts',
            mermaid: 'mermaid',
            cytoscape: 'cytoscape',
            katex: 'katex',
            'naive-ui': 'naive-ui',
            'vue-router': 'vue-router',
            pinia: 'pinia',
            '@vicons': 'vicons',
            lodash: 'lodash',
            dayjs: 'dayjs',
          };
          for (const [pkg, chunk] of Object.entries(NAMED)) {
            if (id.includes(`node_modules/${pkg}`)) return chunk;
          }
          // 剩余 node_modules 合并到 vendor chunk
          if (id.includes('node_modules/')) return 'vendor';
        }
      }
    },
    chunkSizeWarningLimit: 1000,
    minify: 'esbuild',
    assetsInlineLimit: 4096
  },
  root: '.'
})
