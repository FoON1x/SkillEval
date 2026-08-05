import { defineConfig } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const apiDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../api')
const py = path.join(apiDir, '.venv', 'Scripts', 'python.exe')

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  use: {
    baseURL: 'http://localhost:5173',
    channel: 'chromium',
    trace: 'retain-on-failure',
  },
  webServer: [
    {
      cwd: apiDir,
      command: `"${py}" -c "import pathlib; [pathlib.Path(f'data/e2e.db{s}').unlink(missing_ok=True) for s in ['','-wal','-shm']]" && "${py}" -m uvicorn skill_eval.main:app --port 8000`,
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: false,
      env: { SKILLEVAL_DB_URL: 'sqlite:///data/e2e.db' },
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: false,
    },
  ],
})
