// Zarámuje reálné screenshoty do telefonního rámečku + titulek = listingové
// obrázky 1080x1920 pro Google Play. node docs/google_play_grafika/frames.mjs
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import fs from 'fs';
import path from 'path';
const outDir = path.dirname(fileURLToPath(import.meta.url));

function b64(file) {
  return 'data:image/png;base64,' + fs.readFileSync(path.join(outDir, file)).toString('base64');
}

// (vstupní screenshot, titulek, podtitulek, výstup)
const SHOTS = [
  ['ss_tab_Aplikace.png', 'Všechny firemní moduly', 'na jednom místě', 'play_ss_1_moduly.png'],
  ['ss_tab_ukoly.png',    'Úkoly a oznámení',       'pod kontrolou',     'play_ss_2_ukoly.png'],
];

function html(imgData, h1, p) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  html,body{margin:0;padding:0;width:1080px;height:1920px;overflow:hidden;
    font-family:'Segoe UI',system-ui,Arial,sans-serif}
  .canvas{width:1080px;height:1920px;position:relative;
    background:linear-gradient(160deg,#0c1d33 0%,#0a1626 55%,#060d18 100%)}
  .glow{position:absolute;left:50%;top:60px;transform:translateX(-50%);
    width:760px;height:520px;background:radial-gradient(closest-side,rgba(45,212,191,.18),rgba(45,212,191,0))}
  .cap{position:absolute;top:96px;left:0;right:0;text-align:center}
  .cap h1{margin:0;font-size:66px;font-weight:800;color:#fff;letter-spacing:1px}
  .cap p{margin:8px 0 0;font-size:38px;font-weight:600;color:#9fe7d8}
  .phone{position:absolute;left:50%;top:360px;transform:translateX(-50%);
    width:712px;padding:16px;background:#11151c;border-radius:48px;
    box-shadow:0 30px 70px rgba(0,0,0,.5);border:1px solid #1d2735}
  .phone img{display:block;width:680px;border-radius:34px}
</style></head><body>
  <div class="canvas">
    <div class="glow"></div>
    <div class="cap"><h1>${h1}</h1><p>${p}</p></div>
    <div class="phone"><img src="${imgData}"></div>
  </div>
</body></html>`;
}

const browser = await chromium.launch();
for (const [src, h1, p, out] of SHOTS) {
  if (!fs.existsSync(path.join(outDir, src))) { console.log('chybi vstup:', src); continue; }
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.setContent(html(b64(src), h1, p), { waitUntil: 'networkidle' });
  await page.screenshot({ path: path.join(outDir, out), clip: { x: 0, y: 0, width: 1080, height: 1920 } });
  await page.close();
  console.log('OK ->', out);
}
await browser.close();
console.log('FRAMES HOTOVO');
