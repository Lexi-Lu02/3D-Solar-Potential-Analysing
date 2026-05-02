import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, './Frontend', '')
  const apiProxyTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'
  const assetProxyTarget = env.VITE_ASSET_PROXY_TARGET || 'http://15.134.87.211'

  return {
    root: './Frontend',
    publicDir: 'public',
    plugins: [vue()],
    server: {
      proxy: {
        '/api': {
          target: apiProxyTarget,
          changeOrigin: true,
        },
        '/combined-buildings.geojson': {
          target: assetProxyTarget,
          changeOrigin: true,
        },
        '/melbourne_cbd_precincts.geojson': {
          target: assetProxyTarget,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: '../dist'
    }
  }
})
