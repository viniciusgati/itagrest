import { test, expect } from '@playwright/test';

test('deve realizar o setup do admin com sucesso', async ({ page }) => {
  await page.goto('http://localhost:3000/setup-admin');
  
  await page.fill('input[placeholder="Ex: João Silva"]', 'Administrador de Teste');
  await page.fill('input[placeholder="admin"]', 'admin_test');
  await page.fill('input[placeholder="admin@restaurante.com"]', 'test@example.com');
  
  const passwordInputs = page.locator('input[type="password"]');
  await passwordInputs.nth(0).fill('password123');
  await passwordInputs.nth(1).fill('password123');
  
  await page.click('button:has-text("Finalizar Configuração")');
  
  await expect(page.locator('text=Tudo Pronto!')).toBeVisible({ timeout: 15000 });
});
