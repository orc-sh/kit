import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    hmr: {
      host: 'www.localhooks.com',
      protocol: 'wss',
      clientPort: 443,
    },
    port: 3000,
    host: true,
    cors: true,
    allowedHosts: ['www.localhooks.com', 'localhost'],
    // Tell Vite to trust the proxy and use HTTPS URLs
    strictPort: true,
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
  },
  // Ensure proper URL generation when behind proxy
  base: '/',
  preview: {
    port: 3000,
    strictPort: true,
    host: true,
  },
});
