/**
 * Nasnima bezpecne DEMO obrazovky STRATEGIE Mobil (telefon + tablet) pro Google Play.
 * Demo session pres /api/v1/auth/demo-login (UKAZKA s.r.o. — synteticka data, ZADNA realna).
 * Spusteni:  node docs/google_play_grafika/capture_demo.mjs
 * Vystup:    docs/google_play_grafika/_raw/{ph,tab}_*.png  (pak: python frame_screenshots.py)
 * Vyzaduje playwright (uz v node_modules) + chromium. Preskakuje Domu (avatar ditete Marti-AI).
 */
import { chromium, devices } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { mkdirSync, statSync } from 'fs';

const OUT = join(dirname(fileURLToPath(import.meta.url)), '_raw');
const BASE = 'https://strategie-ai.com';
mkdirSync(OUT, { recursive: true });

async function shot(page, name) { const p = join(OUT, name); await page.screenshot({ path: p }); console.log('  OK', name, Math.round(statSync(p).size/1024)+' KB'); }
async function tapNav(page, label){ try{ await page.locator('#navwrap >> text='+label).first().click({timeout:5000}); }catch(e){ try{ await page.locator('text='+label).last().click({timeout:4000}); }catch(e2){} } await page.waitForTimeout(1800); await page.evaluate(()=>scrollTo(0,0)); await page.waitForTimeout(400); }
async function gotoDoch(page){ await page.goto(BASE+'/mobile',{waitUntil:'networkidle',timeout:40000}); await page.waitForTimeout(2500); try{ await page.locator('#navwrap >> text=Firma').first().click({timeout:5000}); await page.waitForTimeout(1500);}catch(e){} try{ await page.locator('text=Spolupráce').first().click({timeout:5000}); await page.waitForTimeout(2500);}catch(e){} await page.evaluate(()=>scrollTo(0,0)); await page.waitForTimeout(400); }
async function tapTile(page,label){ try{ await page.locator('text='+label).first().click({timeout:5000}); await page.waitForTimeout(2000);}catch(e){} await page.evaluate(()=>scrollTo(0,0)); await page.waitForTimeout(400); }

async function run(deviceOpts, prefix){
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ ...deviceOpts, locale:'cs-CZ', timezoneId:'Europe/Prague', colorScheme:'dark' });
  const page = await ctx.newPage();
  await page.goto(BASE+'/api/v1/auth/demo-login?next=/mobile',{waitUntil:'networkidle',timeout:40000}); await page.waitForTimeout(3000);
  console.log(prefix,'aplikace'); await tapNav(page,'Aplikace'); await shot(page, prefix+'_aplikace.png');
  console.log(prefix,'ukoly');    await tapNav(page,'Úkoly');    await shot(page, prefix+'_ukoly.png');
  console.log(prefix,'dochazka'); await gotoDoch(page);          await shot(page, prefix+'_dochazka.png');
  console.log(prefix,'tyden');    await gotoDoch(page); await tapTile(page,'Týden'); await shot(page, prefix+'_tyden.png');
  console.log(prefix,'napoveda'); await page.goto(BASE+'/mobile',{waitUntil:'networkidle'}); await page.waitForTimeout(2000);
  try{ await page.locator('#navwrap >> text=Aplikace').first().click({timeout:5000}); await page.waitForTimeout(1500);}catch(e){}
  await tapTile(page,'Nápověda docházka'); await shot(page, prefix+'_napoveda.png');
  await browser.close();
}
await run({ ...devices['Pixel 7'] }, 'ph');
await run({ viewport:{width:834,height:1194}, deviceScaleFactor:2, isMobile:true, hasTouch:true }, 'tab');
console.log('HOTOVO ->', OUT);
