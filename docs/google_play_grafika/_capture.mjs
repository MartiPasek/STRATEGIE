// Zachytí reálné screenshoty appky přes veřejný DEMO režim (read-only).
// Výstup: ss_*.png (1080x1920). node docs/google_play_grafika/_capture.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';
const outDir = path.dirname(fileURLToPath(import.meta.url));
const BASE = 'https://strategie-ai.com';

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 360, height: 640 },
  deviceScaleFactor: 3,
  isMobile: true,
  userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Mobile Safari/537.36',
});
const page = await ctx.newPage();

async function snap(name) {
  await page.waitForTimeout(1800);
  await page.screenshot({ path: path.join(outDir, 'ss_' + name + '.png') });
  console.log('snap', name, '->', page.url());
}
async function clickText(t) {
  try {
    const el = page.locator(`text=${t}`).first();
    await el.click({ timeout: 4000 });
    return true;
  } catch (e) { console.log('  (neklikl:', t, ')'); return false; }
}

await page.goto(BASE + '/mobile', { waitUntil: 'networkidle' });
await clickText('▶️ Vyzkoušet ukázku');
await page.waitForLoadState('networkidle').catch(()=>{});
await snap('01_home');

// Projdi spodní navigaci (co tam po demu je)
for (const tab of ['Aplikace', 'Úkoly', 'Kontakty', 'Firma', 'Domů']) {
  const ok = await clickText(tab);
  if (ok) await snap('tab_' + tab.replace(/[^A-Za-zÁ-ž]/g,''));
}

// zkus dalších obrazovek z domovské dlaždice (pokud jsou)
await clickText('Domů');
for (const item of ['Docházka', 'Můj týden', 'Přehled']) {
  const ok = await clickText(item);
  if (ok) { await snap('scr_' + item.replace(/[^A-Za-zÁ-ž]/g,'')); await clickText('Domů'); }
}

await browser.close();
console.log('CAPTURE HOTOVO');
