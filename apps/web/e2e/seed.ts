/* E2E seed: imports a demo trace, creates a test case, runs an evaluation. */
const API = 'http://127.0.0.1:8000'

const RAW = {
  version: '0.1',
  session_id: 'e2e-sess-1',
  skill_name: 'e2e-demo-skill',
  events: [
    { type: 'session.start', ts: '2026-08-05T10:00:00Z' },
    { type: 'agent.start', ts: '2026-08-05T10:00:01Z' },
    { type: 'tool.start', tool: 'read_file', args: { path: '/a' }, ts: '2026-08-05T10:00:02Z' },
    { type: 'tool.end', tool: 'read_file', result: { ok: true }, ts: '2026-08-05T10:00:07Z' },
    { type: 'llm.start', model: 'claude-sonnet', input_tokens: 100, ts: '2026-08-05T10:00:07Z' },
    { type: 'llm.end', output_tokens: 50, cost_usd: 0.001, latency_ms: 900, ts: '2026-08-05T10:00:08Z' },
    { type: 'tool.start', tool: 'grep', args: { q: 'x' }, ts: '2026-08-05T10:00:09Z' },
    { type: 'tool.end', tool: 'grep', result: { ok: true }, ts: '2026-08-05T10:00:12Z' },
    { type: 'agent.end', ts: '2026-08-05T10:00:13Z' },
    { type: 'session.end', ts: '2026-08-05T10:00:15Z' },
  ],
}

export async function seed() {
  const importResp = await fetch(`${API}/api/ingest/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent: 'opencode', raw: RAW }),
  })
  if (!importResp.ok) throw new Error(`import failed: ${await importResp.text()}`)
  const { id: traceId } = await importResp.json()

  const caseResp = await fetch(`${API}/api/test-cases`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: 'e2e-demo-case',
      agent: 'opencode',
      rule: 'strict',
      expected: { tools: ['read_file', 'grep'] },
      assertions: [{ code: 'len(projection) >= 2' }],
    }),
  })
  if (!caseResp.ok) throw new Error(`case create failed: ${await caseResp.text()}`)
  const { id: caseId } = await caseResp.json()

  const evalResp = await fetch(`${API}/api/eval/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ test_case_id: caseId, trace_id: traceId }),
  })
  if (!evalResp.ok) throw new Error(`eval failed: ${await evalResp.text()}`)
  const { result } = await evalResp.json()
  return { traceId, caseId, result }
}
