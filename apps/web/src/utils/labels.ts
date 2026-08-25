export const STATUS_LABEL: Record<string, string> = {
  completed: '已完成',
  running: '运行中',
  error: '错误',
  skipped: '已跳过',
  pending: '待定',
}

export const RESULT_LABEL: Record<string, string> = {
  passed: '通过',
  failed: '未通过',
  review: '待复核',
  error: '错误',
}

export function statusLabel(s: string): string {
  return STATUS_LABEL[s] ?? s
}

export function resultLabel(r: string): string {
  return RESULT_LABEL[r] ?? r
}
