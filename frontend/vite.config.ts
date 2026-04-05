import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        // Manual chunking for better code splitting
        manualChunks: {
          // Vendor chunk for React and its libraries
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          // Chart library chunk
          'vendor-charts': ['recharts'],
          // i18n chunk
          'vendor-i18n': ['i18next', 'react-i18next', 'i18next-browser-languagedetector'],
          // Axios chunk
          'vendor-axios': ['axios'],
        },
      },
    },
    // Enable minification
    minify: 'terser',
    // Enable source maps for production debugging
    sourcemap: false,
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  // Optimize dependencies
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'axios', 'i18next', 'recharts']
  }
})
