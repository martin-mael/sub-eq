import { defineConfig, type Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'node:fs'
import path from 'node:path'

/** Dev uniquement : POST /__screenshot?name=xxx (corps = PNG) -> viewer/screenshots/xxx.png */
function screenshotSink(): Plugin {
  return {
    name: 'screenshot-sink',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use('/__screenshot', (req, res) => {
        if (req.method !== 'POST') return res.end()
        const url = new URL(req.url ?? '', 'http://x')
        const name = (url.searchParams.get('name') ?? 'capture').replace(/[^a-z0-9_-]/gi, '_')
        const chunks: Buffer[] = []
        req.on('data', (c: Buffer) => chunks.push(c))
        req.on('end', () => {
          const dir = path.resolve(__dirname, 'screenshots')
          fs.mkdirSync(dir, { recursive: true })
          fs.writeFileSync(path.join(dir, name + '.png'), Buffer.concat(chunks))
          res.end('ok')
        })
      })
    },
  }
}

export default defineConfig({
  plugins: [react(), screenshotSink()],
  server: { port: 5174, strictPort: true },
  build: { chunkSizeWarningLimit: 2500 },
})
