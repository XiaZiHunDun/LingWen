import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { cytoscapeCjsInterop } from './vite-plugins/cytoscape-cjs-interop.js'

export default defineConfig({
  plugins: [vue(), cytoscapeCjsInterop()],
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
          //
          // === Phase 83 investigation (mermaid <-> vendor circular) ===
          //
          // Build emits: `Circular chunk: mermaid -> vendor -> mermaid`
          //
          // Analysis:
          // - mermaid chunk imports ~100+ Vue 3 internal symbols (createVNode, h, etc.)
          //   from vendor — LEGITIMATE dependency (mermaid needs Vue runtime)
          // - vendor chunk imports 1 symbol (_ as ln) from mermaid
          //   — likely a markdown lib (marked.js / markdown-it with mermaid extension)
          //   consuming a mermaid export
          //
          // Trade-off accepted:
          // - Build succeeds with warning only — runtime works
          // - True fix requires moving mermaid-consuming lib out of vendor
          //   OR merging mermaid into vendor (loses lazy-load isolation)
          // - Both options worse than current state
          //
          // Future work:
          // - Phase 84+ may delete dead mergePreset* refs (cleanup, unrelated)
          // - Phase 78+ reviews noted 7 dead refs in useMergePresets.ts
          //   — deletion may slightly alter chunk graph
          // - Vite upgrade could change warning behavior — revisit if upgraded
          //
          // === Phase 80 / Phase 71 chunk history ===
          //
          // - Phase 71: initial 8 chunks + vendor catch-all
          // - Phase 80: naive-ui already in NAMED (3.11kB chunk, but most code
          //   in vendor due to inter-deps with vue/pinia — see Phase 80 commit
          //   7516865d for verification details
          //
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
