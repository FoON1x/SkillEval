import { describe, expect, it } from 'vitest'
import { STATUS_LABEL, RESULT_LABEL, statusLabel, resultLabel } from './labels'

describe('STATUS_LABEL', () => {
  it('maps spec §8 status words to Chinese', () => {
    expect(STATUS_LABEL['completed']).toBe('已完成')
    expect(STATUS_LABEL['running']).toBe('运行中')
    expect(STATUS_LABEL['error']).toBe('错误')
    expect(STATUS_LABEL['skipped']).toBe('已跳过')
    expect(STATUS_LABEL['pending']).toBe('待定')
  })
})

describe('RESULT_LABEL', () => {
  it('maps eval result words to Chinese', () => {
    expect(RESULT_LABEL['passed']).toBe('通过')
    expect(RESULT_LABEL['failed']).toBe('未通过')
    expect(RESULT_LABEL['review']).toBe('待复核')
    expect(RESULT_LABEL['error']).toBe('错误')
  })
})

describe('statusLabel', () => {
  it('returns Chinese for known statuses', () => {
    expect(statusLabel('completed')).toBe('已完成')
    expect(statusLabel('running')).toBe('运行中')
  })
  it('falls back to the original string for unknown statuses', () => {
    expect(statusLabel('cancelled')).toBe('cancelled')
    expect(statusLabel('')).toBe('')
  })
})

describe('resultLabel', () => {
  it('returns Chinese for known results', () => {
    expect(resultLabel('passed')).toBe('通过')
    expect(resultLabel('failed')).toBe('未通过')
  })
  it('falls back to the original string for unknown results', () => {
    expect(resultLabel('weird')).toBe('weird')
    expect(resultLabel('')).toBe('')
  })
})
