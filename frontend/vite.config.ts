import vue from "@vitejs/plugin-vue";
import { resolve } from "path";
import AutoImport from "unplugin-auto-import/vite";
import { VantResolver } from "unplugin-vue-components/resolvers";
import Components from "unplugin-vue-components/vite";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// https://vitejs.dev/config/
export default defineConfig({
  // 设置基础路径
  base: "/",
  plugins: [
    vue(),
    AutoImport({
      resolvers: [VantResolver()],
    }),
    Components({
      resolvers: [VantResolver({ importStyle: false })], // 禁用自动样式导入，手动控制
    }),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.svg", "robots.txt", "apple-touch-icon.png"],
      manifest: {
        name: "Beancount Web 记账系统",
        short_name: "Beancount",
        description: "基于Beancount的现代化复式记账系统",
        theme_color: "#1989fa",
        background_color: "#ffffff",
        display: "standalone",
        orientation: "portrait",
        scope: "/",
        start_url: "/",
        icons: [
          {
            src: "pwa-192x192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
          },
          {
            src: "pwa-512x512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
        navigateFallback: null,
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\..*/i,
            handler: "NetworkFirst",
            options: {
              cacheName: "api-cache",
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 7, // 7 days
              },
              cacheableResponse: {
                statuses: [0, 200],
              },
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
            handler: "CacheFirst",
            options: {
              cacheName: "images-cache",
              expiration: {
                maxEntries: 60,
                maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
              },
            },
          },
          {
            // 排除node_modules，只缓存应用自身的JS/CSS文件
            urlPattern: ({ url }) => {
              return (
                (url.pathname.endsWith(".js") ||
                  url.pathname.endsWith(".css")) &&
                !url.pathname.includes("node_modules") &&
                !url.pathname.includes("/@")
              );
            },
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "static-resources",
            },
          },
        ],
      },
      devOptions: {
        enabled: true,
        type: "module",
        navigateFallback: "index.html",
      },
    }),
  ],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
    },
  },
  build: {
    // 构建优化
    target: "es2020",
    cssCodeSplit: true,
    sourcemap: false, // 生产环境关闭sourcemap以减小体积
    minify: "esbuild", // 使用esbuild进行压缩，速度更快
    rollupOptions: {
      output: {
        // 代码分割优化
        manualChunks: {
          // 将Vue相关库分离
          vue: ["vue", "vue-router", "pinia"],
          // 将UI库分离
          vant: ["vant", "@vant/icons"],
          // 将图表库分离
          echarts: ["echarts", "vue-echarts"],
          // 将工具库分离
          utils: ["axios", "dayjs"],
        },
        // 文件命名优化
        chunkFileNames: "js/[name]-[hash].js",
        entryFileNames: "js/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split(".") || [];
          let extType = info[info.length - 1];
          if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)$/.test(assetInfo.name || "")) {
            extType = "media";
          } else if (/\.(png|jpe?g|gif|svg)$/.test(assetInfo.name || "")) {
            extType = "img";
          } else if (/\.(woff2?|eot|ttf|otf)$/.test(assetInfo.name || "")) {
            extType = "fonts";
          }
          return `${extType}/[name]-[hash].[ext]`;
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
      "/api": {
        target: "http://localhost:8000",
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
      "vue",
      "vue-router",
      "pinia",
      "vant",
      "@vant/icons",
      "axios",
      "dayjs",
      "echarts",
      "vue-echarts",
    ],
    exclude: [],
  },
  // 环境变量配置
  envPrefix: ["VITE_", "VUE_"],
});
