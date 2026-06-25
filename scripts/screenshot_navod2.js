/**
 * Krok 2: Použije uloženou session a udělá screenshoty
 * všech klíčových obrazovek docházky.
 *
 * PREREQ: Nejdřív spusť screenshot_login.js a přihlas se!
 * Spuštění: node scripts/screenshot_navod2.js
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
  const sz = Math.round(fs.statSync(p).size / 1024);
  console.log(`   ✅ ${name} (${sz} KB)`);
}

async function main() {
  if (!fs.existsSync(STORAGE)) {
    console.error('❌ Nenalezen auth.json! Nejdřív spusť: node scripts/screenshot_login.js');
    process.exit(1);
  }

  console.log('🚀 Načítám uloženou session...');
  const storageState = JSON.parse(fs.readFileSync(STORAGE, 'utf8'));

  const browser = await chromium.launch({
    headless: false,
    slowMo: 300,
    args: ['--window-size=430,932'],
  });

  const context = await browser.newContext({
    ...devices['Pixel 7'],
    locale: 'cs-CZ',
    timezoneId: 'Europe/Prague',
    colorScheme: 'dark',
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true,
    storageState,
  });

  const page = await context.newPage();

  // ═══════ 1. DOMOVSKÁ OBRAZOVKA ═══════
  console.log('\n📸 1. Domovská obrazovka...');
  await page.goto(`${BASE}/mobile`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(3000);
  await shot(page, 'S01_domovska.png');

  // ═══════ 2. TAB FIRMA ═══════
  console.log('📸 2. Záložka Firma...');
  try {
    // Najdi spodní tab "Firma"
    const firmaTab = page.locator('[onclick*="firma"], [data-tab="firma"]').first();
    const firmaText = page.locator('text=Firma').last();
    const target = (await firmaTab.isVisible({ timeout: 2000 }).catch(() => false))
      ? firmaTab : firmaText;
    await target.click();
    await page.waitForTimeout(2000);
    await shot(page, 'S02_firma.png');
  } catch (e) {
    console.log('   ⚠️ Tab Firma:', e.message);
    await shot(page, 'S02_firma.png');
  }

  // ═══════ 3. SPOLUPRÁCE (docházka) ═══════
  console.log('📸 3. Spolupráce (docházka)...');
  try {
    const spol = page.locator('text=Spolupráce').first();
    if (await spol.isVisible({ timeout: 3000 })) {
      await spol.click();
      await page.waitForTimeout(3000);
    }
  } catch (e) {
    console.log('   ⚠️ Spolupráce:', e.message);
  }
  await shot(page, 'S03_spoluprace.png');

  // ═══════ 4. HLAVNÍ TLAČÍTKO — menu ═══════
  console.log('📸 4. Menu "Potřebuji ti něco říct"...');
  try {
    const btn = page.locator('text=/Potřebuji ti něco/i').first();
    if (await btn.isVisible({ timeout: 3000 })) {
      await btn.click();
      await page.waitForTimeout(1500);
      await shot(page, 'S04_menu.png');
      // Scrollni dolů pro zbytek menu
      await page.mouse.wheel(0, 300);
      await page.waitForTimeout(800);
      await shot(page, 'S04b_menu_dole.png');
    }
  } catch (e) {
    console.log('   ⚠️ Tlačítko:', e.message);
  }

  // ═══════ 5. PŘÍCHOD — "Jsem v práci" ═══════
  console.log('📸 5. Hledám "Jsem v práci"...');
  try {
    const jsem = page.locator('text=/Jsem v práci/i').first();
    if (await jsem.isVisible({ timeout: 3000 })) {
      // Screenshot PŘED kliknutím (zvýrazněný)
      await jsem.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await shot(page, 'S05_jsem_v_praci.png');
    }
  } catch (e) {
    console.log('   ⚠️:', e.message);
  }

  // ═══════ 6. "Teď to bude jinak" (podrobnější menu) ═══════
  console.log('📸 6. Hledám "Teď to bude jinak"...');
  try {
    const jinak = page.locator('text=/Teď to bude jinak/i').first();
    if (await jinak.isVisible({ timeout: 3000 })) {
      await jinak.click();
      await page.waitForTimeout(1500);
      await shot(page, 'S06_jinak_menu.png');
    }
  } catch (e) {
    console.log('   ⚠️:', e.message);
  }

  // ═══════ 7. Hledáme dovolená / absence volby ═══════
  console.log('📸 7. Hledám absence volby...');
  try {
    // Scrollni aby bylo vidět absence volby
    await page.mouse.wheel(0, 400);
    await page.waitForTimeout(800);
    await shot(page, 'S07_absence_volby.png');
  } catch (e) {
    console.log('   ⚠️:', e.message);
  }

  // ═══════ 8. Scrollback nahoru — fullpage ═══════
  console.log('📸 8. Fullpage screenshot...');
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(500);
  await shot(page, 'S08_fullpage.png', true);

  // ═══════ 9. Sekce "Co se dělo" (joby) ═══════
  console.log('📸 9. Sekce záznamy...');
  try {
    const sekce = page.locator('text=/Co se vlastně dělo|Tak to bylo/i').first();
    if (await sekce.isVisible({ timeout: 3000 })) {
      await sekce.click();
      await page.waitForTimeout(1000);
      await shot(page, 'S09_zaznamy.png');
    }
  } catch (e) {
    console.log('   ⚠️:', e.message);
  }

  // ═══════ 10. Potvrzovací karty (pokud existují) ═══════
  console.log('📸 10. Potvrzovací karty...');
  try {
    const confirm = page.locator('text=/Potvrzuji svou docházku|potvrzuji/i').first();
    if (await confirm.isVisible({ timeout: 2000 })) {
      await confirm.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      await shot(page, 'S10_potvrzeni.png');
    } else {
      console.log('   ℹ️ Žádné nepotvrzené dny (to je OK)');
    }
  } catch (e) {
    console.log('   ℹ️ Žádné nepotvrzené dny');
  }

  // ═══════ HOTOVO ═══════
  console.log('\n═══════════════════════════════════════');
  console.log(`✅ Hotovo! Screenshoty v: ${OUT}`);
  console.log('═══════════════════════════════════════');

  const files = fs.readdirSync(OUT).filter(f => f.startsWith('S') && f.endsWith('.png'));
  console.log(`📷 Celkem ${files.length} screenshotů:`);
  files.forEach(f => console.log(`   ${f}`));

  console.log('\n👀 Prohlížeč zůstane 20 sekund otevřený — koukni se.');
  await page.waitForTimeout(20000);
  await browser.close();
}

main().catch(err => {
  console.error('❌ Chyba:', err.message);
  process.exit(1);
});
