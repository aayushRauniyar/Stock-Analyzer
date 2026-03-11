import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  root: '.',
  // The data_snapshots folder is in the project root and will be
  // accessible as /data_snapshots/latest_data.json automatically
  // because Vite serves static files from the root.
})
