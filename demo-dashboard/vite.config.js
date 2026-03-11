import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Allow Vite to serve files from the parent directory (where MiraiDashboard.jsx lives)
  server: {
    fs: {
      allow: [
        path.resolve(__dirname, '..'),  // parent = Stock Analyzer root
      ],
    },
    // Proxy requests for /data_snapshots to the parent folder's data_snapshots
    proxy: {},
  },
  // Serve the parent's data_snapshots folder as a static public directory
  publicDir: path.resolve(__dirname, '..', 'data_snapshots_public_dummy'),  // dummy — we use the proxy below
})
