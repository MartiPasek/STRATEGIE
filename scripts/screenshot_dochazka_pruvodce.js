/**
 * Pořídí PŘESNÉ snímky obrazovek docházky pro hlasového průvodce (per krok).
 * Pixel 7 viewport, ostré (deviceScaleFactor 2). Session z auth.json.
 * Spuštění:  node scripts/screenshot_dochazka_pruvodce.js
 * Výstup:    docs/navod_screenshoty/P_*.png   (pak cp do apps/api/static/navod_dochazka)
 */
const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, '..', 'docs', 'navod_screenshoty');
const STORAGE = path.join(OUT, 'auth.json');
const BASE = 'https://strategie-ai.com';

async function shot(page, name, fullPage = false) {
  const p = path.join(OUT, name);
  await page.screenshot({ path: p, fullPage });
  console.log('   OK', name, Math.round(fs.statSync(p).size / 1024) + ' KB');
}

async function main() {
  const storageState = JSON.parse(fs.readFileSync(STORAGE, 'utf8'));
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    ...devices['Pixel 7'],
    locale: 'cs-CZ', timezoneId: 'Europe/Prague', colorScheme: 'dark',
    viewport: { width: 390, height: 844 }, deviceScaleFactor: 2,
    isMobile: true, hasTouch: true, storageState,
  });
  const page = await context.newPage();

  async function gotoDochazka() {
    await page.goto(BASE + '/mobile', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2500);
    // Firma (spodní tab) -> Spolupráce
    try { await page.locator('text=Firma').last().click({ timeout: 4000 }); await page.waitForTimeout(1200); } catch (e) { console.log('  ! Firma', e.message); }
    try { await page.locator('text=Spolupráce').first().click({ timeout: 4000 }); await page.waitForTimeout(2500); } catch (e) { console.log('  ! Spoluprace', e.message); }
  }

  // 1) Firma tab
  console.log('1) Firma'); await page.goto(BASE + '/mobile', { waitUntil: 'networkidle' }); await page.waitForTimeout(2500);
  try { await page.locator('text=Firma').last().click(); await page.waitForTimeout(1500); } catch (e) {}
  await shot(page, 'P_firma.png');

  // 2) Přehled docházky (nahoře ZAKÁZKY A ČINNOSTI + Makat + Potřebuji)
  console.log('2) Prehled (zakazky a cinnosti)'); await gotoDochazka();
  await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(500);
  await shot(page, 'P_prehled.png');

  // 3) Zakázka picker
  console.log('3) Zakazka picker'); await gotoDochazka();
  try { await page.getByRole('button').filter({ hasText: /^.*Zakázka/ }).first().click({ timeout: 5000 }); await page.waitForTimeout(2000); } catch (e) { console.log('  ! Zakazka tile', e.message); }
  await shot(page, 'P_zakazka.png');

  // 4) Činnost picker
  console.log('4) Cinnost picker'); await gotoDochazka();
  try { await page.getByRole('button').filter({ hasText: /Činnost/ }).first().click({ timeout: 5000 }); await page.waitForTimeout(2000); } catch (e) { console.log('  ! Cinnost tile', e.message); }
  await shot(page, 'P_cinnost.png');

  // 5) Menu "Potřebuji ti něco říct"
  console.log('5) Menu Potrebuji'); await gotoDochazka();
  try { await page.locator('text=/Potřebuji ti něco/i').first().click({ timeout: 5000 }); await page.waitForTimeout(1500); } catch (e) { console.log('  ! Potrebuji', e.message); }
  await shot(page, 'P_menu.png');
  try { await page.mouse.wheel(0, 350); await page.waitForTimeout(700); await shot(page, 'P_menu_dole.png'); } catch (e) {}

  // 6) Tady budu jinde -> Osobní/Služební
  console.log('6) Tady budu jinde'); await gotoDochazka();
  try { await page.locator('text=/Tady budu jinde/i').first().click({ timeout: 5000 }); await page.waitForTimeout(1500);
    try { await page.locator('#dochJindeBox').scrollIntoViewIfNeeded({ timeout: 2000 }); } catch (e2) {}
    await page.waitForTimeout(500);
  } catch (e) { console.log('  ! Tady budu jinde', e.message); }
  await shot(page, 'P_jinde.png');
  // 6b) Osobní důvody rozbalené
  try { await page.locator('text=/Osobní důvody/i').first().click({ timeout: 4000 }); await page.waitForTimeout(1200); await shot(page, 'P_jinde_osobni.png'); } catch (e) { console.log('  ! Osobni duvody', e.message); }

  // 7) Potvrzení (pokud je nepotvrzený den)
  console.log('7) Potvrzeni'); await gotoDochazka();
  try { var c = page.locator('text=/Potvrzuji svou docházku/i').first(); if (await c.isVisible({ timeout: 3000 })) { await c.scrollIntoViewIfNeeded(); await page.waitForTimeout(500); await shot(page, 'P_potvrzeni.png'); } else { console.log('   (zadny nepotvrzeny den)'); } } catch (e) { console.log('   (zadny nepotvrzeny den)'); }

  console.log('HOTOVO -> ' + OUT);
  await browser.close();
}
main().catch(e => { console.error('CHYBA', e); process.exit(1); });
