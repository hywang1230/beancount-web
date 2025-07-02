import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
  // 设置基础路径
  base: '/',
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
    }),
    Components({
      resolvers: [ElementPlusResolver()],
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    // 构建优化
    target: 'es2020',
    cssCodeSplit: true,
    sourcemap: false, // 生产环境关闭sourcemap以减小体积
    minify: 'esbuild', // 使用esbuild进行压缩，速度更快
    rollupOptions: {
      output: {
        // 代码分割优化
        manualChunks: {
          // 将Vue相关库分离
          vue: ['vue', 'vue-router', 'pinia'],
          // 将UI库分离
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          // 将图表库分离
          echarts: ['echarts', 'vue-echarts'],
          // 将工具库分离
          utils: ['axios', 'dayjs'],
        },
        // 文件命名优化
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || []
          let extType = info[info.length - 1]
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)$/.test(assetInfo.name || '')) {
            extType = 'media'
          } else if (/\.(png|jpe?g|gif|svg)$/.test(assetInfo.name || '')) {
            extType = 'img'
          } else if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name || '')) {
            extType = 'fonts'
          }
          return `${extType}/[name]-[hash].[ext]`
        },
      },
      // 排除不需要打包的外部依赖（如果有CDN的话）
      external: [],
    },
    // 压缩配置
    terserOptions: {
      compress: {
        drop_console: true, // 移除console
        drop_debugger: true, // 移除debugger
      },
    },
    // 构建chunk大小警告阈值
    chunkSizeWarningLimit: 1000,
  },
  // 开发服务器配置
  server: {
    port: 5173,
    host: true,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  // 预览服务器配置
  preview: {
    port: 5173,
    host: true,
  },
  // 依赖预构建优化
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'element-plus',
      '@element-plus/icons-vue',
      'axios',
      'dayjs',
      'echarts',
      'vue-echarts',
    ],
    exclude: [],
  },
  // 环境变量配置
  envPrefix: ['VITE_', 'VUE_'],
}) 