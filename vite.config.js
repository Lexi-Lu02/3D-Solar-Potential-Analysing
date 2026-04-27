import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  root: './Frontend',
  publicDir: 'public',
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: 'http://15.134.87.211',
        changeOrigin: true,
      },
      '/combined-buildings.geojson': {
        target: 'http://15.134.87.211',
        changeOrigin: true,
      },
      '/melbourne_cbd_precincts.geojson': {
        target: 'http://15.134.87.211',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: '../dist'
  }
})
