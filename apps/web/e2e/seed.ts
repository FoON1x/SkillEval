/* E2E seed: imports a demo trace, creates a test case, runs an evaluation. */
const API = 'http://127.0.0.1:8000'

const SID = 'e2e-sess-1'

/* Real `opencode run --format json` JSONL shape: {"type","timestamp","sessionID","part"}. */
const RAW = {
  session_id: SID,
  skill_name: 'e2e-demo-skill',
  events: [
    {
      type: 'step_start', timestamp: 1787496829616, sessionID: SID,
      part: { id: 'p1', messageID: 'm1', sessionID: SID, type: 'step-start' },
    },
    {
      type: 'tool_use', timestamp: 1787496829700, sessionID: SID,
      part: {
        type: 'tool', tool: 'read_file', callID: 'c1',
        state: {
          status: 'completed', input: { path: '/a' }, output: 'content of /a',
          metadata: { output: 'content of /a', exit: 0, truncated: false },
          title: 'read_file', time: { start: 1787496829600, end: 1787496829900 },
        },
        id: 'p2', sessionID: SID, messageID: 'm1',
      },
    },
    {
      type: 'step_finish', timestamp: 1787496829900, sessionID: SID,
      part: {
        id: 'p3', reason: 'tool-calls', messageID: 'm1', sessionID: SID, type: 'step-finish',
        tokens: { total: 100, input: 80, output: 20 }, cost: 0.001,
      },
    },
    {
      type: 'step_start', timestamp: 1787496831000, sessionID: SID,
      part: { id: 'p4', messageID: 'm2', sessionID: SID, type: 'step-start' },
    },
    {
      type: 'tool_use', timestamp: 1787496831200, sessionID: SID,
      part: {
        type: 'tool', tool: 'grep', callID: 'c2',
        state: {
          status: 'completed', input: { q: 'x' }, output: 'match found',
          metadata: { output: 'match found', exit: 0, truncated: false },
          title: 'grep', time: { start: 1787496831100, end: 1787496831400 },
        },
        id: 'p5', sessionID: SID, messageID: 'm2',
      },
    },
    {
      type: 'step_finish', timestamp: 1787496831400, sessionID: SID,
      part: {
        id: 'p6', reason: 'stop', messageID: 'm2', sessionID: SID, type: 'step-finish',
        tokens: { total: 200, input: 150, output: 50 }, cost: 0.002,
      },
    },
  ],
  export_info: {
    id: SID, title: 'e2e-demo-skill', agent: 'build',
    model: { id: 'demo-model', providerID: 'demo', variant: 'default' },
    version: '1.18.21', cost: 0.003,
    tokens: { input: 230, output: 70 },
    time: { created: 1787496829000, updated: 1787496831400 },
  },
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
