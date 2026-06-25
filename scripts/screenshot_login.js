/**
 * Krok 1: Otevře prohlížeč s mobilní emulací.
 * JIRKA SE PŘIHLÁSÍ RUČNĚ.
 * Po přihlášení uloží session cookies do souboru.
 *
 * Spuštění: node scripts/screenshot_login.js
 */
const { chromium, devices } = require('playwright');
const path = require('path');

const STORAGE = path.join(__dirname, '..', 'docs', 'navod_screenshoty', 'auth.json');

async function main() {
  console.log('═══════════════════════════════════════════════════');
  console.log('📱 STRATEGIE — Přihlášení pro screenshoty');
  console.log('═══════════════════════════════════════════════════');
  console.log('');
  console.log('1. Otevře se prohlížeč s mobilní emulací');
  console.log('2. PŘIHLAS SE svým účtem (login + heslo)');
  console.log('3. Až uvidíš domovskou obrazovku appky,');
  console.log('   ZAVŘI prohlížeč (křížkem)');
  console.log('');
  console.log('Session se automaticky uloží pro screenshoty.');
  console.log('═══════════════════════════════════════════════════');
  console.log('');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 200,
    args: ['--window-size=430,900'],
  });

  const context = await browser.newContext({
    ...devices['Pixel 7'],
    locale: 'cs-CZ',
    timezoneId: 'Europe/Prague',
    colorScheme: 'dark',
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,  // 2x místo 3x = menší obrázky
    isMobile: true,
    hasTouch: true,
  });

  const page = await context.newPage();
  await page.goto('https://strategie-ai.com/mobile', { waitUntil: 'networkidle', timeout: 30000 });

  console.log('🔓 Prohlížeč otevřen — PŘIHLAS SE a pak ZAVŘI okno.');
  console.log('   (Čekám max 5 minut...)');

  // Čekej až uživatel zavře prohlížeč
  try {
    await page.waitForTimeout(300000); // 5 minut
  } catch (e) {
    // browser closed by user
  }

  // Ulož session
  try {
    const storage = await context.storageState();
    require('fs').writeFileSync(STORAGE, JSON.stringify(storage, null, 2));
    console.log(`\n✅ Session uložena do: ${STORAGE}`);
  } catch (e) {
    console.log('\n⚠️ Session se neuložila (prohlížeč zavřen dřív)');
  }

  try { await browser.close(); } catch (e) {}
  console.log('Hotovo. Teď spusť: node scripts/screenshot_navod2.js');
}

main();
