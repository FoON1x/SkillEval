import { expect, test } from '@playwright/test'
import { seed } from './seed'

test.beforeAll(async () => {
  await seed()
})

test('trace list shows the imported trace', async ({ page }) => {
  await page.goto('/traces')
  await expect(page.getByRole('cell', { name: 'e2e-demo-skill' })).toBeVisible()
  await expect(page.getByRole('cell', { name: 'opencode' })).toBeVisible()
})

test('trace detail renders DAG, timeline and stats', async ({ page }) => {
  await page.goto('/traces')
  await page.getByRole('link', { name: 'e2e-demo-skill' }).first().click()
  await expect(page.getByTestId('dag')).toBeVisible()
  await expect(page.getByTestId('dag-node').first()).toBeVisible()
  await expect(page.getByTestId('timeline')).toBeVisible()
  await expect(page.getByTestId('cost-panel')).toBeVisible()
  await page.getByTestId('dag-node').filter({ hasText: 'read_file' }).click()
  await expect(page.getByTestId('detail-panel')).toContainText('read_file')
})

test('test case list shows seeded case and eval result', async ({ page }) => {
  await page.goto('/test-cases')
  await expect(page.getByTestId('case-item').first()).toContainText('e2e-demo-case')
  await expect(page.getByTestId('case-item').first()).toContainText('rule=strict')
})

test('creating a test case and running eval', async ({ page }) => {
  await page.goto('/test-cases')
  await page.getByRole('button', { name: '新建用例' }).click()
  await page.getByPlaceholder('名称').fill('e2e-created-case')
  await page.getByPlaceholder('期望工具（逗号分隔）：read_file, grep').fill('grep, read_file')
  await page.getByRole('button', { name: '创建' }).click()
  await expect(page.getByText('e2e-created-case')).toBeVisible()

  const item = page.getByTestId('case-item').filter({ hasText: 'e2e-created-case' })
  await item.getByRole('button', { name: '运行评测' }).click()
  await expect(item.getByTestId('eval-result')).toHaveText(/failed/)
})

test('eval runs page lists seeded run', async ({ page }) => {
  await page.goto('/eval-runs')
  await expect(page.getByText('score 1.00').first()).toBeVisible()
})
