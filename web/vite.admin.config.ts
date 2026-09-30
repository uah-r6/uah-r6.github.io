import { defineConfig } from 'vite'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  base: '/admin/',
  build: {
    outDir: 'admin-dist',
    rollupOptions: {
      input: fileURLToPath(new URL('./admin.html', import.meta.url)),
    },
  },
})
