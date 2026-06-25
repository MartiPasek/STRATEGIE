/**
 * Automatický screenshot-maker pro uživatelský návod docházky.
 * Otevře strategie-ai.com/mobile v emulaci mobilního telefonu,
 * projde klíčové obrazovky a udělá screenshoty.
 *
 * Spuštění: node scripts/screenshot_navod.js
 * Výstup:   docs/navod_screenshoty/
 */

const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = path.join(__dirname, '..', 'docs', 'navod_screenshoty');
const BASE = 'https://strategie-ai.com';

// Konfigurace demo účtu - UPRAVIT pokud máte jiné přihlašovací údaje
// Pro screenshoty použijeme demo účet nebo session
const DEMO_MODE = true; // true = přes /mobile bez loginu (guest welcome screen)

async function main() {
  // Vytvoř výstupní složku
  fs.mkdirSync(OUT, { recursive: true });

  console.log('🚀 Spouštím Playwright s emulací mobilu...');

  const browser = await chromium.launch({
    headless: false,  // Viditelný prohlížeč - abys viděl co se děje
    slowMo: 500,      // Zpomalit akce pro lepší viditelnost
  });

  // Samsung Galaxy S24 emulace (390x844, touch, mobilní UA)
  const context = await browser.newContext({
    ...devices['Pixel 7'],
    locale: 'cs-CZ',
    timezoneId: 'Europe/Prague',
    colorScheme: 'dark',
    // Přidáme viewport přesně jako S24
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true,
  });

  const page = await context.newPage();

  // ═══════ SCREENSHOT 1: Úvodní obrazovka (guest) ═══════
  console.log('📸 1/8 — Úvodní obrazovka...');
  await page.goto(`${BASE}/mobile`, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);
  await page.screenshot({
    path: path.join(OUT, '01_uvodni_obrazovka.png'),
    fullPage: false,
  });
  console.log('   ✅ 01_uvodni_obrazovka.png');

  // ═══════ Pokus o demo login ═══════
  console.log('🔑 Zkouším demo login...');
  try {
    // Hledáme tlačítko demo / vyzkoušet
    const demoBtn = await page.locator('text=/demo|vyzkoušet|ukázk/i').first();
    if (await demoBtn.isVisible({ timeout: 3000 })) {
      await demoBtn.click();
      await page.waitForTimeout(3000);
      console.log('   ✅ Demo login kliknut');
    }
  } catch (e) {
    console.log('   ⚠️ Demo tlačítko nenalezeno, zkouším přímý /mobile...');
  }

  // ═══════ SCREENSHOT 2: Po loginu — domovská obrazovka ═══════
  console.log('📸 2/8 — Domovská obrazovka...');
  await page.waitForTimeout(2000);
  await page.screenshot({
    path: path.join(OUT, '02_domovska.png'),
    fullPage: false,
  });
  console.log('   ✅ 02_domovska.png');

  // ═══════ SCREENSHOT 3: Spodní lišta — zvýraznit Firma ═══════
  console.log('📸 3/8 — Hledám záložku Firma...');
  try {
    // Klikni na záložku Firma
    const firmaTab = await page.locator('text=/Firma/i').last();
    if (await firmaTab.isVisible({ timeout: 5000 })) {
      await page.screenshot({
        path: path.join(OUT, '03_pred_firma.png'),
        fullPage: false,
      });
      console.log('   ✅ 03_pred_firma.png');

      await firmaTab.click();
      await page.waitForTimeout(2000);

      await page.screenshot({
        path: path.join(OUT, '04_firma_tab.png'),
        fullPage: false,
      });
      console.log('   ✅ 04_firma_tab.png');
    }
  } catch (e) {
    console.log('   ⚠️ Záložka Firma nenalezena:', e.message);
  }

  // ═══════ SCREENSHOT 4: Klik na Spolupráce ═══════
  console.log('📸 5/8 — Hledám Spolupráce...');
  try {
    const spoluprace = await page.locator('text=/Spolupráce/i').first();
    if (await spoluprace.isVisible({ timeout: 5000 })) {
      await spoluprace.click();
      await page.waitForTimeout(2000);

      await page.screenshot({
        path: path.join(OUT, '05_spoluprace_dochazka.png'),
        fullPage: false,
      });
      console.log('   ✅ 05_spoluprace_dochazka.png');
    }
  } catch (e) {
    console.log('   ⚠️ Spolupráce nenalezena:', e.message);
  }

  // ═══════ SCREENSHOT 5: Menu "Potřebuji ti něco říct" ═══════
  console.log('📸 6/8 — Hledám hlavní tlačítko...');
  try {
    const btn = await page.locator('text=/Potřebuji ti něco říct/i').first();
    if (await btn.isVisible({ timeout: 5000 })) {
      await btn.click();
      await page.waitForTimeout(1500);

      await page.screenshot({
        path: path.join(OUT, '06_menu_rozbalene.png'),
        fullPage: false,
      });
      console.log('   ✅ 06_menu_rozbalene.png');
    }
  } catch (e) {
    console.log('   ⚠️ Hlavní tlačítko nenalezeno:', e.message);
  }

  // ═══════ SCREENSHOT FULLPAGE — celá stránka ═══════
  console.log('📸 7/8 — Celá stránka (scrollovatelná)...');
  try {
    await page.screenshot({
      path: path.join(OUT, '07_cela_stranka.png'),
      fullPage: true,
    });
    console.log('   ✅ 07_cela_stranka.png');
  } catch (e) {
    console.log('   ⚠️ Fullpage screenshot:', e.message);
  }

  // ═══════ SCREENSHOT 8: Mobilní rámeček (viewport only) ═══════
  console.log('📸 8/8 — Viewport screenshot...');
  await page.screenshot({
    path: path.join(OUT, '08_viewport.png'),
    fullPage: false,
  });
  console.log('   ✅ 08_viewport.png');

  // ═══════ HOTOVO ═══════
  console.log('\n═══════════════════════════════════════');
  console.log(`✅ Hotovo! Screenshoty v: ${OUT}`);
  console.log('═══════════════════════════════════════');
  console.log('\n👀 Prohlížeč zůstane otevřený 30 sekund — můžeš se podívat.');
  console.log('   Pak se automaticky zavře.\n');

  await page.waitForTimeout(30000);
  await browser.close();
}

main().catch(err => {
  console.error('❌ Chyba:', err.message);
  process.exit(1);
});
